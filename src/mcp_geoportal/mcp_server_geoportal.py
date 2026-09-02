import argparse
import asyncio
from dataclasses import dataclass
import logging
import time

import httpx
import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from tools.base_tools import register_base_tools
from tools.gp_tools import register_gp_tools
from tools.oereb_tools import register_oereb_tools

# Server-Instanz
mcp = MCPServer(
    "Geoportal des Kantons Bern",
)
START_TIME = time.time()

# Logging initialisieren
logger = logging.getLogger(__name__)

# Constants
EXTERNAL_APIS = {
    "metawarehouse": {
        "api_url": "https://www.metawarehouse.apps.be.ch",
        "readyness_url": "https://www.metawarehouse.apps.be.ch"
    },
    "oereb_server": {
        "api_url": "https://www.oereb2.apps.be.ch",
        "readyness_url": "https://www.oereb2.apps.be.ch/version"
    },
    "geofiles": {
        "api_url": "https://geofiles.be.ch",
        "readyness_url": "https://geofiles.be.ch/readyness.txt"
    }
}

# Registriere alle Tools
register_base_tools(mcp, EXTERNAL_APIS)
register_oereb_tools(mcp, EXTERNAL_APIS)
register_gp_tools(mcp, EXTERNAL_APIS)

@dataclass
class APICheckResult:
    name: str
    url: str
    ok: bool
    error: str | None = None


async def _check_single_api(
    client: httpx.AsyncClient, name: str, url: str
) -> APICheckResult:
    try:
        response = await client.head(url)
        response.raise_for_status()
        return APICheckResult(name=name, url=url, ok=True)
    except httpx.TimeoutException:
        return APICheckResult(name=name, url=url, ok=False, error="Timeout")
    except httpx.HTTPStatusError as e:
        return APICheckResult(
            name=name, url=url, ok=False, error=f"Status {e.response.status_code}"
        )
    except httpx.RequestError as e:
        return APICheckResult(name=name, url=url, ok=False, error=str(e))


async def check_external_apis(
    readyness_urls = {name: api["readyness_url"] for name, api in EXTERNAL_APIS.items()}
) -> list[APICheckResult]:
    """Prüft alle konfigurierten externen APIs parallel."""
    async with httpx.AsyncClient(timeout=3.0) as client:
        results = await asyncio.gather(
            *[_check_single_api(client, name, url) for name, url in readyness_urls.items()]
        )
    return list(results)

@mcp.custom_route("/ready", methods=["GET"])
async def readiness(request: Request) -> JSONResponse:
    results = await check_external_apis()
    all_ok = all(r.ok for r in results)
    body = {
        "status": "ready" if all_ok else "not_ready",
        "checks": {
            r.name: {
                "ok": r.ok,
                "url": r.url,
                **({"error": r.error} if r.error else {}),
            }
            for r in results
        },
    }
    return JSONResponse(body, status_code=200 if all_ok else 503)

@mcp.custom_route("/live", methods=["GET"])
async def liveness(request: Request) -> Response:
    return JSONResponse(
        {
            "status": "ok",
            "uptime_s": round(time.time() - START_TIME, 1),
        }
    )


@mcp.tool()
def get_geoproducts() -> list[dict]:
    """Frage im Metawarehouse des Geoportals alle Geoprodukte des Kantons Bern ab.

    Returns:
        list[str]: Eine Liste mit den Codes und Bezeichnungen aller Geoprodukte
    """
    url = f"{EXTERNAL_APIS['metawarehouse']['api_url']}/geoportal_geoproduct?select=code,name"
    logger.info(url)
    mwh_result = httpx.get(url)
    result_list = []
    mwh_json = mwh_result.json()
    for gpr in mwh_json:
        gpr_dict = {"code": gpr["code"], "bezeichnung": gpr["name"]["de"]}
        result_list.append(gpr_dict)

    return result_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server Geoportal")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Server-Modus: stdio (lokal) oder http (remote)",
        required=False,
    )

    args = parser.parse_args()

    if args.mode == "stdio":
        mcp.run(transport="stdio")
    else:
        # Wenn enable_dns_rebinding_protection=True
        # kann mit allow_hosts / allowed_origins gesteuert
        # werden, wer auf den MCP-Server zugreifen darf.
        app = mcp.streamable_http_app(
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            )
        )
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=6789,
            workers=2,
            timeout_keep_alive=300,
            access_log=True,
        )
        server = uvicorn.Server(config)
        server.run()
