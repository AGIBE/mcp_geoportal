import json

import duckdb
import rasterio # rasterio und requests musste ich noch ins venv installieren
from rasterio.mask import mask
import requests

from .create_map_link import get_map_link

# TODO: AED-Standort: Wo sind die nächste AED-Standort?
# TODO: Gibt es in der Gemeinde, in der Nähe von Gebäude im Bauinventar?
# TODO: Gibt es in der Gemeinde XY unüberbaute Bauzonen (SEIN_UNUEBAU)?
# TODO: Freies Übernachten/Biwakieren (z.B. darf ich am Hinterburgseeli biwakieren)?
# TODO: Suchdienst für Orts-, Flur- und Geländenamen (liefert Koordinaten zurück) - Suchfunktion Geodat-Tools
# TODO: Suchdienst für bekannte Denkmäler und Häuser (liefert Koordinaten zurück) - z.B. wo ist das Rütihubelbad?
# TODO: Abfragen von Erdbebenzonen für EGRID (WMS der swisstopo mit getFeatureInfo auf https://wms.geo.admin.ch) -> evtl. Anreichern bei Naturgefahrenabfrage
# TODO: Abragen aktueller Messdaten von Oberflächengewässern oder Luftqualität (klären, ob es API auf Messnetze gibt)
# TODO: Rutschgebiete der AV (noch keine Geodaten)
# TODO: Darf ich an Adresse XY eine Erdwärmesonde/Grundwasserwärmesonde bauen?


async def __get_gemeinde_infos(
    bfs_nr: int, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    ADMGDE_GDEDAT
    """
    cursor = con.cursor()
    spatial_sql = f"""
                    select
                    gde.espop::VARCHAR AS Einwohnerzahl, gde.espop_gmfl::VARCHAR AS "Bevölkerungsdichte pro ha", gde.gmdflaeche::VARCHAR AS "Gemeindefläche in ha", ste.steuanlg::VARCHAR as Steueranlage, gde.url::VARCHAR AS Website
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/ADMGDE/admgde_gdedat.parquet' gde
                    join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/STEUERN/steuern_steuanl.parquet' ste on gde.bfsnr = ste.bfsnr
                    where gde.bfsnr = {bfs_nr}
                """
    try:
        cursor.execute(spatial_sql)
        row = cursor.fetchone()
        if row is None:
            return {}
        columns = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
    return dict(zip(columns, row))


async def __get_bohrprofile_for_egrid(
    egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    GEOSOND_GEOSOND
    """
    cursor = con.cursor()
    spatial_sql = f"""
                    select
                    typt_sondtyp_de as Sondiertyp, sond_datum as Sondierdatum, sond_tiefe as Sondiertiefe, round(ST_Distance(lif.geometry, gef.geometry)) as Entfernung, url as pdf_link
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/GEOSOND/geosond_geosond.parquet' gef on ST_Intersects(lif.geometry, ST_Buffer(gef.geometry, 300))
                    where
                    lif.egrid = '{egrid}'
                """
    try:
        cursor.execute(spatial_sql)
        results = cursor.fetchall()
        if not results:
            return ([{}], "")
        columns = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
    dicts = [dict(zip(columns, row)) for row in results]
    map_link = get_map_link("get_bohrprofile_for_egrid", {"egrid": egrid})
    return dicts, map_link


async def __get_naturgefahren_for_egrid(
    egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    NATGEFKA_GEFGEB
    """
    cursor = con.cursor()
    spatial_sql = f"""
                    select
                    json_object('gefahr', gef.hprozt_hproz_de,'stufe', gef.gefstuf) AS gefahrenstufe
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/NATGEFKA/natgefka_gefgeb.parquet' gef on ST_Intersects(lif.geometry, gef.geometry)
                    where
                    lif.egrid = '{egrid}'
                """
    try:
        cursor.execute(spatial_sql)
        results = cursor.fetchall()
        if not results:
            return ({}, "")
    finally:
        cursor.close()
    result_dict = {}
    for row in results:
        json_str = row[0]
        item = json.loads(json_str)
        if item.get("gefahr") not in result_dict or (
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


async def __get_property_info_for_egrid(
    egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    DIPANU_DIPANUF
    """
    cursor = con.cursor()
    spatial_sql = f"""
                    select
                    dp.gstnr as Grundstücksnummer, dp.gstbez as Grundstückbezeichnung, dp.gbflae as Grundstücksfläche, dp.gstartt_gstart_de as Grundstückart_deutsch, dp.gstartt_gstart_fr as Grundstückart_französisch
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/DIPANU/dipanu_dipanuf.parquet' dp
                    where egrid = '{egrid}'
                """
    try:
        cursor.execute(spatial_sql)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        if not row:
            return ({}, "")
    finally:
        cursor.close()
    map_link = get_map_link("get_property_info_for_egrid", {"egrid": egrid})
    return dict(zip(columns, row)), map_link

async def __get_erdbebenrisiko_for_egrid(
        egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    FRK_SEDIRAS
    """
    cursor = con.cursor()
    result = dict()

    # EGRID Geometrie holen
    spatial_sql = f"""
                    select ST_AsGeoJSON(lif.geometry) as egrid_mask
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                    where lif.egrid = '{egrid}'
                    """

    try:
        cursor.execute(spatial_sql)
        egrid_mask = cursor.fetchone()[0]
        egrid_mask = json.loads(egrid_mask)

        # Erdbebengefährdungszone von Swisstopo WMS für den nördlichsten, östlichsten, südlichsten, westlichsten Punkt der Parzelle
        corner_points = get_corner_points(egrid_mask, con)
        zone_list = []

        for point in corner_points:
            zone = query_swisstopo(point)
            zone_list.append(zone)
        result["Gefährdungszone"] = max(zone_list) # mögliche Zonen: Z1a, Z1b, Z2, Z3a, Z3b, mit alphabetischer Sortierung kommt die risikoreichste Zone als Maximum zurück

        # Baugrundklasse: nur die maximale Mächtigkeit Lockergestein über alle Pixel in der EGRID-Geometrie auslesen
        with rasterio.open(f"{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/FRK/frk_sediras.tif") as file:
            data, transform = mask(
                                    file,
                                    [egrid_mask],
                                    crop=True,
                                    all_touched=True,
                                    filled=False,         
                                )
        max_sediment_depth = data.max()

        if max(zone_list) is None or max_sediment_depth is None:
            return ({}, "")

        # Mächtigkeit Lockergestein auf Baugrundklasse umrechnen
        if max_sediment_depth <= 5:
            baugrundklasse = "Klasse A"
        elif max_sediment_depth <= 20:
            baugrundklasse = "Klasse E"
        else:
            baugrundklasse = "Klasse B+C+D"
        result["Baugrundklasse"] = baugrundklasse

    except Exception as e:
        return ({}, "")

    finally:
        cursor.close()

    # Karte nur für die Baugrundklasse anzeigen?
    # evtl zweite Karte für die Erdbebenzone?
    map_link = get_map_link("get_baugrundklasse_for_egrid", {"egrid": egrid})
    return result, map_link

def get_corner_points(geometry, con):
    """
    Gibt den nördlichsten, östlichsten, südlichsten, westlichsten Punkt einer Geometrie jeweils als Tuple (x-Koordinate, y-Koordinate)
     zurück.
    
    Args:
        geometry (str): Geometrie als GeoJSON-string.
    Returns:
        corner_points (list): Liste der Punkte.
    """
    cursor = con.cursor()
    corners_sql = f"""
                    with points as (
                            select unnest(ST_Dump(ST_points(ST_GeomFromGeoJSON({geometry})))).geom as p),
                        corners as (
                            select arg_max(p, ST_X(p)) as ost,
                                arg_min(p, ST_X(p)) as west,
                                arg_max(p, ST_Y(p)) as nord,
                                arg_min(p, ST_Y(p)) as sued
                            from points)
                    select
                        (ST_X(ost), ST_Y(ost)) AS ost,
                        (ST_X(west), ST_Y(west)) AS west,
                        (ST_X(nord), ST_Y(nord)) AS nord,
                        (ST_X(sued), ST_Y(sued)) AS sued
                    FROM corners
                    """
    try:
        cursor.execute(corners_sql)
        corner_points = cursor.fetchone()
    finally:
        cursor.close()

    return corner_points

def query_swisstopo(point, layer = "ch.bafu.gefahren-gefaehrdungszonen"):
    """
    Führt einen GetFeatureInfo Request auf den gewünschten Layer des WMS von swisstopo aus.
    
    Args:
        - point (tuple): Punkt als Tuple (x-Koordinate, y-Koordinate), der abgefragt werden soll.
        - layer (str): Bezeichnung des Layers, der abgefragt wird.
    Returns:
        - value (str): Resultat der Abfrage, None falls kein Resultat zurückkam.
    """
    
    e, n = point
    r = requests.get("https://wms.geo.admin.ch/", params={
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
        "LAYERS": layer, "QUERY_LAYERS": layer,
        "CRS": "EPSG:2056",
        "BBOX": f"{e-50},{n-50},{e+50},{n+50}",
        "WIDTH": 101, "HEIGHT": 101, "I": 50, "J": 50,
        "INFO_FORMAT": "application/json; subtype=geojson",
    }, timeout=30)
    try:
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        value = features[0]["properties"]["zone"] if features else None
    except:
        value = None

    return value


async def __get_aed_standorte_for_egrid(
        egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    AEDSTO_AEDSTO
    """
    cursor = con.cursor()
    spatial_sql = f"""
                    select
                    aed.adresse as Adresse, aed.ortschaft as Ortschaft, aed.telefon as Telefon, aed.titel as Titel, aed.beschreib as Beschreibung, aed.zugzeit as Erreichbarkeit, aed.zugang as Zugang, round(ST_Distance(lif.geometry, aed.geometry)) as Entfernung
                        from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                        join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/AEDSTO/aedsto_aedsto.parquet' aed on ST_Intersects(lif.geometry, ST_Buffer(aed.geometry, 2000))
                        where lif.egrid = '{egrid}'
                        order by Entfernung asc
                    """
    # reicht Luftlinie als Entfernungsangabe? gibt auch Geoprodukte zur Erreichbarkeit (AEDFALLE, AEDFOPEN), ist aber nicht so genau für Standorte innerhalb von Gebäuden?
    # besser nur den allernächsten Standort angeben? oder nur solche, die jederzeit verfügbar sind (aed.zugang = '24h')?
    try:
        cursor.execute(spatial_sql)
        results = cursor.fetchall()
        if not results:
            return([{}], "")
        columns = [desc[0] for desc in cursor.description]
        dicts = [dict(zip(columns, row)) for row in results]
    finally:
        cursor.close()
    map_link = get_map_link("get_aed_standorte_for_egrid", {"egrid": egrid})
    return dicts, map_link
