import logging
import json
import duckdb
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Geoportal des Kantons Bern", stateless_http=True)
app = mcp.streamable_http_app()


# Constants
MWH_API_BASE = "https://www.metawarehouse.apps.be.ch"
OEREB_API_BASE = "https://www.oereb2.apps.be.ch"


@mcp.tool(
    name="address_to_egrid",
    description="Gibt für die eingegebene Adresse den EGRID zurück"
)
def get_egrid_from_address_XXXX(searchtext: str) -> str:
    """Suche für den eingegebene Adresse den dazugehörigen EGRID.

    Args:
        searchtext (str): Suchtext mit dem nach der Adresse gesucht wird.

    Returns:
        str: Eidgenössischer Grundstück-Identifikator. Beginnt mit "CH".
    """
    url_search = f"{MWH_API_BASE}/rpc/oereb_search"
    params = {"searchtext": searchtext}
    result = httpx.get(url_search, params=params)
    js = result.json()
    x = js[0]["x"]
    y = js[0]["y"]

    url_oereb = f"{OEREB_API_BASE}/getegrid/json/?EN={x},{y}"
    result = httpx.get(url_oereb)
    js = result.json()
    egrid = js["GetEGRIDResponse"][0]["egrid"]
    return egrid
