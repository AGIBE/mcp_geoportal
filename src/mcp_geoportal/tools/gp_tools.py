import json

import duckdb
from mcp.server import MCPServer
from tools.create_map_link import get_map_link

# TODO: AED-Standort: Wo sind die nächste AED-Standort?
# TODO: Gibt es in der Gemeinde, in der Nähe von Gebäude im Bauinventar?
# TODO: Gibt es in der Gemeinde XY unüberbaute Bauzonen? - Geschütztes Geoprodukt (kein Parquet-File vorhanden)
# TODO: Freies Übernachten/Biwakieren (z.B. darf ich am Hinterburgseeli biwakieren)?
# TODO: Suchdienst für Orts-, Flur- und Geländenamen (liefert Koordinaten zurück) - Suchfunktion Geodat-Tools
# TODO: Suchdienst für bekannte Denkmäler und Häuser (liefert Koordinaten zurück) - z.B. wo ist das Rütihubelbad?
# TODO: Abfragen von Erdbebenzonen für EGRID (WMS der swisstopo mit getFeatureInfo auf https://wms.geo.admin.ch) -> evtl. Anreichern bei Naturgefahrenabfrage
# TODO: Abragen aktueller Messdaten von Oberflächengewässern oder Luftqualität (klären, ob es API auf Messnetze gibt)
# TODO: Rutschgebiete der AV (noch keine Geodaten)
# TODO: Darf ich an Adresse XY eine Erdwärmesonde/Grundwasserwärmesonde bauen?


async def __get_gemeinde_infos(bfs_nr: int, api_definitions: dict) -> dict:
    """
    ADMGDE_GDEDAT
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    gde.espop AS Einwohnerzahl, gde.espop_gmfl AS "Bevölkerungsdichte pro ha", gde.gmdflaeche AS "Gemeindefläche in ha", ste.steuanlg as Steueranlage, gde.url AS Website
                    from '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/ADMGDE/admgde_gdedat.parquet' gde
                    join '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/STEUERN/steuern_steuanl.parquet' ste on ST_Intersects(gde.geometry, ST_Buffer(ste.geometry, -50))
                    where gde.bfsnr = {bfs_nr}
                """
    con.execute(spatial_sql)
    row = con.fetchone()
    if row is None:
        return {}
    columns = [desc[0] for desc in con.description]
    return dict(zip(columns, row))

async def __get_bohrprofile_for_egrid(egrid: str, api_definitions: dict) -> dict:
    """
    GEOSOND_GEOSOND
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    typt_sondtyp_de as Sondiertyp, sond_datum as Sondierdatum, sond_tiefe as Sondiertiefe, round(ST_Distance(lif.geometry, gef.geometry)) as Entfernung, url as pdf_link
                    from '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/GEOSOND/geosond_geosond.parquet' gef on ST_Intersects(lif.geometry, ST_Buffer(gef.geometry, 300))
                    where
                    lif.egrid = '{egrid}'
                """
    con.execute(spatial_sql)
    results = con.fetchall()
    columns = [desc[0] for desc in con.description]
    dicts = [dict(zip(columns, row)) for row in results]
    map_link = get_map_link("get_bohrprofile_for_egrid", {"egrid": egrid})
    return dicts, map_link

async def __get_naturgefahren_for_egrid(egrid: str, api_definitions: dict) -> dict:
    """
    NATGEFKA_GEFGEB
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    json_object('gefahr', gef.hprozt_hproz_de,'stufe', gef.gefstuf) AS gefahrenstufe
                    from '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/NATGEFKA/natgefka_gefgeb.parquet' gef on ST_Intersects(lif.geometry, gef.geometry)
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

async def __get_property_info_for_egrid(egrid: str, api_definitions: dict) -> dict:
    """
    DIPANU_DIPANUF
    """
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    spatial_sql = f"""
                    select
                    dp.gstnr as Grundstücksnummer, dp.gstbez as Grundstückbezeichnung, dp.gbflae as Grundstücksfläche, dp.gstartt_gstart_de as Grundstückart_deutsch, dp.gstartt_gstart_fr as Grundstückart_französisch
                    from '{api_definitions['geofiles']['api_url']}/geoportal/pub/download/DIPANU/dipanu_dipanuf.parquet' dp
                    where egrid = '{egrid}'
                """
    con.execute(spatial_sql)
    row = con.fetchone()
    if row is None:
        return {}
    columns = [desc[0] for desc in con.description]
    map_link = get_map_link("get_property_info_for_egrid", {"egrid": egrid})
    return dict(zip(columns, row)), map_link
