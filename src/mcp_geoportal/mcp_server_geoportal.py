import logging
import json
import duckdb
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Geoportal des Kantons Bern")

# Constants
MWH_API_BASE = "https://www.metawarehouse.apps.be.ch"
OEREB_API_BASE = "https://www.oereb2.apps.be.ch"


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
def get_oereb_themes() -> dict[str, str]:
    """Frage im ÖREB-Kataster des Kantons Bern alle verfügbaren Themen ab."""
    url = f"{OEREB_API_BASE}/capabilities/json"
    result = httpx.get(url)
    result_dict = {}
    js = result.json()
    for theme in js["GetCapabilitiesResponse"]["topic"]:
        code = theme["Code"]
        name = ""
        for lang in theme["Text"]:
            if lang["Language"] == "de":
                name = lang["Text"]
                break
        result_dict[code] = name

    return result_dict


@mcp.tool()
def get_egrid_from_address(searchtext: str) -> str:
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


@mcp.tool()
def get_oereb_auszug(egrid: str) -> str:
    """Erstelle für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und lies alle vorhandenen Eigentumsbeschränkungen aus.

    Args:
        egrid: Eidgenössischer Grundstück-Identifikator. Beginnt mit "CH".

    """
    url = f"{OEREB_API_BASE}/extract/xml?egrid={egrid}&lang=de"
    result = httpx.get(url)
    return result.text


@mcp.tool()
def get_oereb_auszug_for_address(searchtext: str) -> str:
    """Ermittelt in einem ersten Schritt für die gesuchte Adresse den eidgenössischen Grundstück-Identifikator (EGRID).
    Für diesen EGRID wird dann in einem zweiten Schritt ein Auszug aus dem Kataster der öffentlich-rechtlichen
    Eigentumsbeschränkungen (ÖREB-Kataster) erstellt. Dessen Inhalt wird zurückgegeben.

    Args:
        searchtext (str): Suchtext mit dem nach der Adresse gesucht wird.

    Returns:
        list[str]: Liste der im Auszug enthaltenen Themen und deren Bezeichnung.
    """
    egrid = get_egrid_from_address(searchtext)
    auszug = get_oereb_auszug(egrid)
    return auszug


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
def get_naturgefahren_for_address(adresse: str) -> dict:
    """Ermittelt für eine Adresse (Strasse Hausnummer, Ort) die Naturgefahrestufe pro Gefahr (Einsturz/Absenkung, Wasser, Sturz, Lawine, Rutschung).
    Args:
        adresse (str): Adresse, für die die Naturgefahren ermittelt werden sollen. Format: "Strasse Hausnummer, Ort"
    Returns:
        dict: Dictionnary mit den Naturgefahren für die Adresse im Format: {"gefahr": "gefahrenstufe"}
    """
    egrid = get_egrid_from_address(adresse)
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
    return mapped_result_dict


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


@mcp.tool()
def get_bohrprofile_for_address(adresse: str) -> dict:
    """Gibt die Bohrprofile (gemäss Geoprodukt GEOSOND) im Umkreis von 300m um die übergebene Adresse zurück. 
    Args:
        adresse (str): Adresse, für welche Bohrprofile gesucht werden sollen. Format: "Strasse Hausnummer, Ort"
    Returns:
        list: Eine Liste mit Dictionaries, die die gefundenen Bohrprofile inkl. Link auf das PDF des Bohrprofils enthält.
    """
    egrid = get_egrid_from_address(adresse)
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
    mcp.run(transport="stdio")
