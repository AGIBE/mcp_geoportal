import argparse
import json
import logging
import re
from typing import Union

import duckdb
import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from tools.base_tools import register_base_tools
from tools.create_map_link import get_map_link
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


@mcp.tool()
def get_gebaeude_in_rote_zonen() -> list[dict]:
    """Ermittelt für jede Gemeinde des Kantons Bern, wieviele Gebäude in der Naturgefahrenkarte in der Zone mit erheblicher Gefährdung liegen.

    Returns:
        list[dict]: Eine Liste mit einem Dictionary pro Gemeinde. Jeder Dictionary hat drei Keys:
                    - bfsnr: BFS-Nummer der Gemeinde
                    - gemname: Name der Gemeinde
                    - anzahl_gebaeude_in_roter_zone: Anzahl der Gebäude, die in der Naturgefahrenkarte in der Zone mit erheblicher Gefährdung liegen.
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")

    spatial_sql = """
                    select
                    bbf.bfsnr,
                    gde.gemname,
                    count(gef.objectid)
                    from 'https://geofiles.be.ch/geoportal/pub/download/MOPUBE/mopube_bbf.parquet' bbf
                    join 'https://geofiles.be.ch/geoportal/pub/download/ADMGDE/admgde_gdedat.parquet' gde on bbf.bfsnr = gde.bfsnr
                    join 'https://geofiles.be.ch/geoportal/pub/download/NATGEFKA/natgefka_sygefgeb.parquet' gef on ST_Intersects(bbf.geometry, gef.geometry)
                    where
                    bbf.bbartt_bez_de = 'Gebäude'
                    and gef.max_gefstu = 4
                    group by bbf.bfsnr, gde.gemname
                    order by gde.gemname
                """

    con.execute(spatial_sql)
    result_list = []
    results = con.fetchall()
    for gemeinde in results:
        result_dict = {
            "bfsnr": gemeinde[0],
            "gemeindename": gemeinde[1],
            "anzahl_gebaeude_in_roter_zone": gemeinde[2],
        }
        result_list.append(result_dict)

    return result_list


@mcp.tool()
def get_naturgefahren_for_egrid(egrid: str) -> dict:
    """Ermittelt für eine Adresse (Strasse Hausnummer, Ort) die Naturgefahrestufe pro Gefahr (Einsturz/Absenkung, Wasser, Sturz, Lawine, Rutschung).
    Args:
        egrid (str): E-GRID für den die Naturgefahren ermittelt werden sollen.
    Returns:
        dict, str: Dictionnary mit den Naturgefahren für die Adresse im Format: {"gefahr": "gefahrenstufe"}, Link zur Kartenansicht im Geoportal des Kantons Bern.
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    json_object('gefahr', gef.hprozt_hproz_de,'stufe', gef.gefstuf) AS gefahrenstufe
                    from 'https://geofiles.be.ch/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join 'https://geofiles.be.ch/geoportal/pub/download/NATGEFKA/natgefka_gefgeb.parquet' gef on ST_Intersects(lif.geometry, gef.geometry)
                    where
                    lif.egrid = '{egrid}'
                """
    con.execute(spatial_sql)
    results = con.fetchall()
    result_dict = {}
    for row in results:
        json_str = row[0]
        item = json.loads(json_str)
        if item.get("gefahr") not in result_dict:
            result_dict[item.get("gefahr")] = item.get("stufe")
        elif (
            item.get("gefahr") in result_dict
            and item.get("stufe") > result_dict[item.get("gefahr")]
        ):
            result_dict[item.get("gefahr")] = item.get("stufe")

    mapped_result_dict = {
        k: get_gefahrenstufe_mapped(v) for k, v in result_dict.items()
    }
    map_link = get_map_link("get_naturgefahren_for_egrid", {"egrid": egrid})
    return mapped_result_dict, map_link


def get_gefahrenstufe_mapped(value: int) -> str:
    """Mappt die Gefahrenstufe auf eine lesbare Bezeichnung.

    Args:
        value (int): Gefahrenstufe als Integer.

    Returns:
        str: Lesbare Bezeichnung der Gefahrenstufe.
    """
    mapping = {
        0: "nicht gefährdet",
        1: "Restgefährdung",
        2: "geringe Gefahr",
        3: "mittlere Gefahr",
        4: "erhebliche Gefahr",
    }
    return mapping.get(value, "unbekannte Gefahrenstufe")


@mcp.tool(
    name="get_bohrprofile",
    description="""Gibt die Bohrprofile (gemäss Geoprodukt GEOSOND) im Umkreis von 300m um den eingegebenen E-GRID zurück.""",
)
def get_bohrprofile_for_egrid(egrid: str) -> dict:
    """
    Args:
        egrid (str): E-GRID, für welcher Bohrprofile gesucht werden sollen.
    Returns:
        list: Eine Liste mit Dictionaries, die die gefundenen Bohrprofile inkl. Link auf das PDF des Bohrprofils enthält.
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    typt_sondtyp_de as Sondiertyp, sond_datum as Sondierdatum, sond_tiefe as Sondiertiefe, url as pdf_link
                    from 'https://geofiles.be.ch/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join 'https://geofiles.be.ch/geoportal/pub/download/GEOSOND/geosond_geosond.parquet' gef on ST_Intersects(lif.geometry, ST_Buffer(gef.geometry, 300))
                    where 
                    lif.egrid = '{egrid}'
                """
    con.execute(spatial_sql)
    results = con.fetchall()
    columns = [desc[0] for desc in con.description]
    dicts = [dict(zip(columns, row)) for row in results]

    return dicts


@mcp.tool()
def get_gemeinde_infos() -> list[dict]:
    """Ermittelt für alle Gemeinden im Kanton Bern statistische und administrative Informationen, unter anderem die Fläche, Einwohnerzahl und Bevölkerungsdichte pro ha .

    Returns:
        list: Eine Liste mit Dictionaries, die pro Gemeinde die Informationen zurückgibt.
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = """
                    select
                    bfsnr, gemname AS Gemeindename, espop AS Einwohnerzahl, espop_gmfl AS "Bevölkerungsdichte pro ha", gmdflaeche AS "Gemeindefläche in ha", url AS Website
                    from 'https://geofiles.be.ch/geoportal/pub/download/ADMGDE/admgde_gdedat.parquet'
                """
    con.execute(spatial_sql)
    results = con.fetchall()
    columns = [desc[0] for desc in con.description]
    dicts = [dict(zip(columns, row)) for row in results]

    return dicts


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
