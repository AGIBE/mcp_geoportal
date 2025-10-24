import argparse
import logging

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from tools.base_tools import register_base_tools
from tools.gp_tools import register_gp_tools
from tools.oereb_tools import register_oereb_tools

# mcp = FastMCP("Geoportal des Kantons Bern", stateless_http=True)
mcp = FastMCP("Geoportal des Kantons Bern")
# app = mcp.streamable_http_app()

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
    logging.info(url)
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
        app = mcp.streamable_http_app()
        config = uvicorn.Config(
            app, host="0.0.0.0", port=6789, workers=2, timeout_keep_alive=300
        )
        server = uvicorn.Server(config)
        server.run()
        # uvicorn.run(
        #     app,
        #     host="0.0.0.0",
        #     port=6789,
        #     timeout_keep_alive=300
        # )
