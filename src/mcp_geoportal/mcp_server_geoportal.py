import argparse
import asyncio
from dataclasses import dataclass
import logging
import time
from typing import Union

import httpx
import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp_geoportal import __version__
from tools.base_tools import __get_bfsnr_for_gemeinde, __get_egrid_from_address
from tools.gp_tools import __get_gemeinde_infos, __get_bohrprofile_for_egrid, __get_naturgefahren_for_egrid, __get_property_info_for_egrid
from tools.oereb_tools import __get_oereb_themes, __get_oereb_auszug

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

@mcp.custom_route("/version", methods=["GET"])
async def version(request: Request) -> Response:
    return JSONResponse(
        {
            "version": f"{__version__}"
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

# ÖREB-Tools

@mcp.tool(
    name="Suche_Themen_OEREB_Kataster",
    description="""Fragt im ÖREB-Kataster des Kantons Bern alle verfügbaren Themen ab.""",
)
async def get_oereb_themes() -> dict[str, str]:
    return await __get_oereb_themes(EXTERNAL_APIS)


@mcp.tool(
    name="Hole_OEREB_Auszug",
    description="""Erstellt für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und liest alle vorhandenen Eigentumsbeschränkungen aus.
        Als Input wird der E-GRID benötigt.""",
)
async def get_oereb_auszug(egrid: str) -> str:
    return await __get_oereb_auszug(egrid, EXTERNAL_APIS)

# BASE-Tools

@mcp.tool(
    name="Suche_BFSNR_zu_Gemeinde",
    description="Liefert die BFS-Nummer aus dem Amtlichen Gemeindeverzeichnis für die übergebene Gemeinde.",
)
async def get_bfsnr_for_gemeinde(
    searchtext: str) -> Union[float, dict]:
    return await __get_bfsnr_for_gemeinde(searchtext, EXTERNAL_APIS)

@mcp.tool(
    name="Suche_EGRID_fuer_Adresse",
    description="""Gibt für die eingegebene Adresse (Format: Strasse Nr., Gemeinde) den E-GRID (Eidgenössischer Grundstückidentifikator)
    sowie die X- und Y-Koordinate zurück.""",
)
async def get_egrid_from_address(
    searchtext: str,
) -> Union[dict[str, float, float], dict]:
    return await __get_egrid_from_address(searchtext, EXTERNAL_APIS)

# GP-Tools

@mcp.tool(
    name="Hole_Gemeindeinfos_zu_BFSNummer",
    description="""Ermittelt für die übergebene BFS-Nummer einer Gemeinde im Kanton Bern statistische und administrative Informationen, unter anderem die Fläche, Einwohnerzahl und Bevölkerungsdichte pro ha und Steueranlage.
        Returns:
            list: Ein Dictionary, der für die übergebene Gemeinde-BFS die Informationen zur Gemeinde zurückgibt.""",
)
async def get_gemeinde_infos(bfs_nr: int) -> dict:
    return await __get_gemeinde_infos(bfs_nr, EXTERNAL_APIS)

@mcp.tool(
    name="Hole_Bohrprofile_zu_EGRID",
    description="""Gibt die Bohrprofile (gemäss Geoprodukt GEOSOND) im Umkreis von 300m um den eingegebenen E-GRID zurück.
    Args:
        egrid (str): E-GRID, für welcher Bohrprofile gesucht werden sollen.
    Returns:
        list[dict]: Eine Liste mit einem Dictionary pro gefundenem Bohrprofil. Jeder Dictionary hat 5 Keys:
                    - Sondiertyp: Sondiertyp
                    - Sondierdatum: Datum der Sondierung
                    - Sondiertiefe: Tiefe der Sondierung
                    - Entfernung: Distanz des Sondierungsstandort zum Grundstück (E-GRID)
                    - pdf_link: Link auf das Bohrprofil-PDF
        str: Link zur Kartenansicht im Geoportal des Kantons Bern.""",
)
async def get_bohrprofile_for_egrid(egrid: str) -> dict:
    return await __get_bohrprofile_for_egrid(egrid, EXTERNAL_APIS)

@mcp.tool(
    name="Hole_Naturgefahreninfo_zu_EGRID",
    description="""Ermittelt für eine Adresse (Strasse Hausnummer, Ort) die Naturgefahrestufe pro Gefahr (Einsturz/Absenkung, Wasser, Sturz, Lawine, Rutschung).
        Args:
            egrid (str): E-GRID für den die Naturgefahren ermittelt werden sollen.
        Returns:
            dict: Dictionnary mit den Naturgefahren für die Adresse im Format: {"gefahr": "gefahrenstufe"}.
            str: Link zur Kartenansicht im Geoportal des Kantons Bern.""",
)
async def get_naturgefahren_for_egrid(egrid: str) -> dict:
    return await __get_naturgefahren_for_egrid(egrid, EXTERNAL_APIS)

@mcp.tool(
    name="Hole_Grundstueck_Info",
    description="""Ermittelt die verfügbaren Grundstücksdaten ohne Eigentumsauskunft.
        Returns:
            dict: Dictionnary mit den Grundstücks-Informationen für die EGRID.
            str: Link zur Kartenansicht im Geoportal des Kantons Bern.""",
)
async def get_property_info_for_egrid(egrid: str) -> dict:
    return await __get_property_info_for_egrid(egrid, EXTERNAL_APIS)


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
