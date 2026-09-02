import argparse
import logging

import httpx
import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from tools.base_tools import register_base_tools
from tools.gp_tools import register_gp_tools
from tools.oereb_tools import register_oereb_tools

# Server-Instanz
mcp = MCPServer("Geoportal des Kantons Bern",
                )

# Logging initialisieren
logger = logging.getLogger(__name__)

# Constants
MWH_API_BASE = "https://www.metawarehouse.apps.be.ch"
OEREB_API_BASE = "https://www.oereb2.apps.be.ch"

# Registriere alle Tools
register_base_tools(mcp)
register_oereb_tools(mcp)
register_gp_tools(mcp)


@mcp.tool()
def get_geoproducts() -> list[dict]:
    """Frage im Metawarehouse des Geoportals alle Geoprodukte des Kantons Bern ab.

    Returns:
        list[str]: Eine Liste mit den Codes und Bezeichnungen aller Geoprodukte
    """
    url = f"{MWH_API_BASE}/geoportal_geoproduct?select=code,name"
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
            transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
        )
        config = uvicorn.Config(
            app, host="0.0.0.0", port=6789, workers=2, timeout_keep_alive=300, access_log=True
        )
        server = uvicorn.Server(config)
        server.run()