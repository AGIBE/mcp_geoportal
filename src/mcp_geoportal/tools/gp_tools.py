import asyncio
import json

import duckdb
import httpx2
import rasterio
from rasterio.mask import mask

from .create_map_link import get_map_link

# TODO: Gibt es in der Gemeinde, in der Nähe von Gebäude im Bauinventar?
# TODO: Gibt es in der Gemeinde XY unüberbaute Bauzonen (SEIN_UNUEBAU)?
# TODO: Freies Übernachten/Biwakieren (z.B. darf ich am Hinterburgseeli biwakieren)?
# TODO: Suchdienst für bekannte Denkmäler und Häuser (liefert Koordinaten zurück)
# TODO: Abragen aktueller Messdaten von Oberflächengewässern oder Luftqualität (klären, ob es API auf Messnetze gibt)
# TODO: Rutschgebiete der AV (noch keine Geodaten)
# TODO: Darf ich an Adresse XY eine Erdwärmesonde/Grundwasserwärmesonde bauen?
# TODO: Ist am Bach XYZ entlang der Parzelle Nr. xx an der Adresse XY ein Gewässerraum festgelegt?
# TODO: Liegt die Parzelle Nr. xx an der Adresse XY innerhalb eines dicht überbauten Gebietes?
# TODO: Wie gross ist der Nutzen von Revitalisierungsmassnahmen entlang dem Abschnitt auf der Parzelle Nr. xx an der Adresse XY? -> Geodatensatz strategische Revitalisierungsplanung
# TODO: Gibt es «Bauwerke Fliessgewässer» entlang dem Bach XYZ in der Gemeinde ABC? -> Geodatensatz Ökomorphologie der Fliessgewässer
# TODO: Welche «Bauwerke Fliessgewässer» gibt es entlang dem Bach XYZ in der Gemeinde ABC? -> Geodatensatz Ökomorphologie der Fliessgewässer
# TODO: Gibt es «Abstürze Fliessgewässer» entlang dem Bach XYZ in der Gemeinde ABC? -> Geodatensatz Ökomorphologie der Fliessgewässer
# TODO: Welche «Abstürze Fliessgewässer» gibt es entlang dem Bach XYZ in der Gemeinde ABC? -> Geodatensatz Ökomorphologie der Fliessgewässer
# TODO: Wie grosse sind die «Abstürze Fliessgewässer» gibt es entlang dem Bach XYZ in der Gemeinde ABC? -> Geodatensatz Ökomorphologie der Fliessgewässer?
# TODO: Tangiert der Bach XYZ in der Gemeinde ABC Fruchtfolgeflächen?
# TODO: Tangiert der Bach XYZ in der Gemeinde ABC ein Naturschutzgebiet?
# TODO: Tangiert der Bach XYZ in der Gemeinde ABC ein Gebiet mit Gewässer- und Grundwasserschutz?
# TODO: Von welchen Gefährdungshinweisen ist die Parzelle Nr. xx an der Adresse XY betroffen?
# TODO: Von welchen Naturgefahrenprozessen ist die Parzelle Nr. xx an der Adresse XY betroffen?
# TODO: Von welchen Intensitäten nach Hauptprozessen ist die Parzelle Nr. xx an der Adresse XY betroffen?
# TODO: Von welchen Intensitäten nach Prozessquellen ist die Parzelle Nr. xx an der Adresse XY betroffen?
# TODO: Von welcher oder welchen Gefahrenstufen des/der Naturgefahrenprozesse(s) XX / YY etc. ist die Parzelle Nr. xx an der Adresse XY betroffen?
# TODO: Aus welchem Jahr stammt die aktuelle Gefahrenbeurteilung auf der Parzelle Nr. xx an der Adresse XY?
# TODO: In welchen Geodatensätzen ist auf der Parzelle Nr. xx an der Adresse XY ein Fliessgewässer eingetragen? -> (bspw. Siegfriedkarten, LK 25, Gewässernetz des Kantons Bern, AV, UP5 etc.)
# TODO: Wie ist die Versickerungsfähigkeit auf der Parzelle Nr. xx an der Adresse XY?
# TODO: Gibt es Altlasten auf der Parzelle Nr. xx an der Adresse XY?
# TODO: Welche Geologie gibt es auf der Parzelle Nr. xx an der Adresse XY?
# TODO: Gibt es Schutzwald in der Gemeinde ABC?
# TODO: Gibt es Schutzwald auf der Parzelle Nr. xx an der Adresse XYZ?
# TODO: Welchen Schutzwald gibt es in der Gemeinde ABC / auf der Parzelle Nr. xx an der Adresse XYZ?


async def __get_municipality_infos(
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
                    where gde.bfsnr = ?
                """
    try:
        cursor.execute(spatial_sql, [bfs_nr])
        row = cursor.fetchone()
        if row is None:
            return {}
        columns = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
    return dict(zip(columns, row))


async def __get_borehole_profiles_for_egrid(
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
                    lif.egrid = ?
                """
    try:
        cursor.execute(spatial_sql, [egrid])
        results = cursor.fetchall()
        if not results:
            return ([{}], "")
        columns = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
    dicts = [dict(zip(columns, row)) for row in results]
    map_link = get_map_link("get_borehole_profiles_for_egrid", {"egrid": egrid})
    return dicts, map_link


async def __get_natural_hazards_for_egrid(
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
                    lif.egrid = ?
                """
    try:
        cursor.execute(spatial_sql, [egrid])
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

    mapped_result_dict = {k: get_danger_level_mapped(v) for k, v in result_dict.items()}
    map_link = get_map_link("get_natural_hazards_for_egrid", {"egrid": egrid})
    return mapped_result_dict, map_link


def get_danger_level_mapped(value: int) -> str:
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
                    where egrid = ?
                """
    try:
        cursor.execute(spatial_sql, [egrid])
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        if not row:
            return ({}, "")
    finally:
        cursor.close()
    map_link = get_map_link("get_property_info_for_egrid", {"egrid": egrid})
    return dict(zip(columns, row)), map_link


async def __get_earthquake_risk_for_egrid(
    egrid: str,
    api_definitions: dict,
    con: duckdb.DuckDBPyConnection,
    client: httpx2.AsyncClient,
) -> tuple[dict, str]:
    """
    Ermittelt Erdbebengefährdungszone und Baugrundklasse für ein EGRID.
    """
    cursor = con.cursor()
    result = {}

    # 1. EGRID Geometrie holen (Sicher mittels Prepared Statement Bindings)
    spatial_sql = f"""
        select ST_AsGeoJSON(lif.geometry) as egrid_mask
        from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
        where lif.egrid = ?
    """
    try:
        db_res = cursor.execute(spatial_sql, [egrid]).fetchone()
        if not db_res:
            return {}, ""

        egrid_mask_str = db_res[0]
        egrid_mask = json.loads(egrid_mask_str)

        # 2. Extrempunkte ermitteln und WMS abfragen
        corner_points = get_corner_points(egrid_mask_str, con)

        # None-Werte filtern, um Fehler bei max() zu verhindern
        zone_list = list(
            await asyncio.gather(
                *(query_swisstopo(p, client) for p in corner_points if p is not None)
            )
        )
        zone_list = [z for z in zone_list if z is not None]

        if not zone_list:
            return {}, ""

        max_zone = max(zone_list)
        result["Gefährdungszone"] = max_zone

        # 3. Rasteranalyse für Baugrundklasse (Sedimentmächtigkeit)
        raster_url = f"{api_definitions['geofiles']['api_url']}/geoportal/pub/download/FRK/frk_sediras.tif"
        with rasterio.open(raster_url) as file:
            data, _ = mask(
                file,
                [egrid_mask],
                crop=True,
                all_touched=True,
                filled=False,
            )

        max_sediment_depth = data.max()
        if max_sediment_depth is None:
            return {}, ""

        # Klassierung vornehmen
        if max_sediment_depth <= 5:
            subsoil_class = "Klasse A"
        elif max_sediment_depth <= 20:
            subsoil_class = "Klasse E"
        else:
            subsoil_class = "Klasse B+C+D"

        result["Baugrundklasse"] = subsoil_class
    except httpx2.RequestError as e:
        return {"Hinweis": f"Fehler beim Abrufen des Swisstopo WMS, {e}"}
    except Exception:
        return ({}, "")
    finally:
        cursor.close()

    # 4. Maplink generieren
    map_link = get_map_link("get_subsoil_class_for_egrid", {"egrid": egrid})
    return result, map_link


def get_corner_points(geometry: str, con: duckdb.DuckDBPyConnection):
    """
    Gibt den nördlichsten, östlichsten, südlichsten, westlichsten Punkt einer Geometrie jeweils als Tuple (x-Koordinate, y-Koordinate)
     zurück.

    Args:
        geometry (str): Geometrie als GeoJSON-string.
    Returns:
        corner_points (list): Liste der Punkte.
    """
    cursor = con.cursor()
    corners_sql = """
                    with points as (
                            select unnest(ST_Dump(ST_points(ST_GeomFromGeoJSON(?)))).geom as p),
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
        res = cursor.execute(corners_sql, [geometry]).fetchone()
    finally:
        cursor.close()
    return res if res else (None, None, None, None)


async def query_swisstopo(
    point: tuple,
    client: httpx2.AsyncClient,
    layer: str = "ch.bafu.gefahren-gefaehrdungszonen",
):
    """
    Führt einen GetFeatureInfo Request auf den gewünschten Layer des WMS von swisstopo aus.

    Args:
        - point (tuple): Punkt als Tuple (x-Koordinate, y-Koordinate), der abgefragt werden soll.
        - client (httpx2.AsyncClient): HTTP-Client für die Abfrage mit httpx2.
        - layer (str): Bezeichnung des Layers, der abgefragt wird.
    Returns:
        - value (str): Resultat der Abfrage, None falls kein Resultat zurückkam.
    """

    e, n = point
    search_url = "https://wms.geo.admin.ch/"
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": layer,
        "CRS": "EPSG:2056",
        "BBOX": f"{e - 1},{n - 1},{e + 1},{n + 1}",
        "WIDTH": 3,
        "HEIGHT": 3,
        "I": 1,
        "J": 1,
        "INFO_FORMAT": "application/json; subtype=geojson",
    }
    try:
        r = await client.get(search_url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        value = features[0]["properties"]["zone"] if features else None
    except:
        value = None

    return value


async def __get_aed_locations_for_egrid(
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
                        where lif.egrid = ?
                        order by Entfernung asc
                    """

    try:
        cursor.execute(spatial_sql, [egrid])
        results = cursor.fetchall()
        if not results:
            return ([{}], "")
        columns = [desc[0] for desc in cursor.description]
        dicts = [dict(zip(columns, row)) for row in results]
    finally:
        cursor.close()
    map_link = get_map_link("get_aed_locations_for_egrid", {"egrid": egrid})
    return dicts, map_link


async def __get_coordinates_from_nomkl(
    search_string: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> list[dict]:
    """
    Hauptmethode: Liefert Koordinaten für einen Suchbegriff.
    Falls kein exakter Treffer existiert, werden die 3 besten Alternativen geliefert.
    """
    cursor = con.cursor()
    source_names = ["Ortsname", "Flurname", "Geländename"]
    layer_names = ["ortsname", "flurname", "gelname"]

    # 1. Exakte Suche über alle Layer
    dicts = __search_exact_matches(
        cursor, search_string, layer_names, source_names, api_definitions
    )

    # 2. Falls nichts gefunden, fuzzy Fallback-Suche triggern
    if not dicts:
        dicts = __search_fuzzy_alternatives(
            cursor, search_string, layer_names, source_names, api_definitions
        )

    # 3. Resultate anreichern
    if dicts and "feedback" not in dicts[0]:
        for d in dicts:
            d["Kartenlink"] = get_map_link("get_coordinates_from_nomkl", d)

    cursor.close()
    return dicts


def __search_exact_matches(
    cursor: duckdb.DuckDBPyConnection,
    search_string: str,
    layer_names: list[str],
    source_names: list[str],
    api_definitions: dict,
) -> list[dict]:
    """Sucht in allen Layern nach exakten Treffern."""
    matches = []
    for index, data_name in enumerate(layer_names):
        sql = f"""
            SELECT gemname AS Gemeindename, {data_name} AS Datentyp, bbox.min_x, bbox.max_x, bbox.min_y, bbox.max_y
            FROM '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/NOMKL/nomkl_{data_name}.parquet'
            WHERE {data_name} ILIKE ?
        """
        try:
            cursor.execute(sql, [search_string])
            results = cursor.fetchall()
            if results:
                columns = [desc[0] for desc in cursor.description]
                for row in results:
                    d = dict(zip(columns, row))
                    d["source"] = source_names[index]
                    matches.append(d)
        except Exception:
            pass
            # sys.stderr.write(f"Error executing exact SQL for {data_name}: {e}")
    return matches


def __search_fuzzy_alternatives(
    cursor: duckdb.DuckDBPyConnection,
    search_string: str,
    layer_names: list[str],
    source_names: list[str],
    api_definitions: dict,
) -> list[dict]:
    """Sucht mittels Levenshtein-Distanz nach den global 3 besten Alternativen."""
    candidates = []
    for index, data_name in enumerate(layer_names):
        sql = f"""
            SELECT gemname AS Gemeindename, {data_name} AS Datentyp, bbox.min_x, bbox.max_x, bbox.min_y, bbox.max_y,
                   levenshtein({data_name}, ?) AS distance
            FROM '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/NOMKL/nomkl_{data_name}.parquet'
            ORDER BY distance ASC
            LIMIT 3
        """
        try:
            cursor.execute(sql, [search_string])
            results = cursor.fetchall()
            if results:
                columns = [desc[0] for desc in cursor.description]
                for row in results:
                    d = dict(zip(columns, row))
                    d["source"] = source_names[index]
                    candidates.append(d)
        except Exception:
            pass
            # sys.stderr.write(f"Error executing fuzzy SQL for {data_name}: {e}")

    if candidates:
        # Sortiert alle Kandidaten layerübergreifend nach der kleinsten Distanz
        candidates.sort(key=lambda x: x["distance"])
        top_3 = candidates[:3]

        # Hinweis-Text einbauen und temporäre Distanz-Spalte entfernen
        for d in top_3:
            d["note"] = (
                f"Bezeichnung konnte nicht gefunden werden. Meinten Sie '{d['Datentyp']}'?"
            )
            del d["distance"]
        return top_3

    return [{"feedback": "Hinweis: Die Bezeichnung wurde nicht gefunden."}]


async def __get_river_zones_for_egrid(
    egrid: str, api_definitions: dict, con: duckdb.DuckDBPyConnection
) -> dict:
    """
    GEWRGNHM_GEWRPOLY / GEWRGNHM_GEWRSTA
    """
    cursor = con.cursor()

    # erst abfragen, ob diese Gemeinde genehmigte Gewässerräume hat
    status_sql = f"""
                    select
                    gnhm.statust_status_de
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/GEWRGNHM/gewrgnhm_gewrsta.parquet' gnhm
                    join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif on ST_Intersects(lif.geometry, gnhm.geometry)
                    where lif.egrid = ?
                    """
    # falls ja, Gewässerräume suchen
    spatial_sql = f"""
                    select
                    gwr.gewrkatt_gewrkat_de as Gewässerraumkategorie_de, gwr.gewrkatt_gewrkat_fr as Gewässerraumkategorie_fr, gwr.gewrtypt_gewrtyp_de as Gewässerraumtyp_de, gwr.gewrtypt_gewrtyp_fr as Gewässerraumtyp_fr, ST_Area(ST_Intersection(lif.geometry, gwr.geometry)) as Fläche
                    from '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/GEWRGNHM/gewrgnhm_gewrpoly.parquet' gwr
                    join '{api_definitions["geofiles"]["api_url"]}/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif on ST_Intersects(lif.geometry, gwr.geometry)
                    where lif.egrid = ? and Fläche != 0
                    """
    try:
        cursor.execute(status_sql, [egrid])
        status = cursor.fetchone()[0]
        results = None
        if status == "nicht genehmigt":
            dicts = [{"Status": status}]
        elif status == "genehmigt":
            cursor.execute(spatial_sql, [egrid])
            results = cursor.fetchall()
            if not results:
                return [{}], ""
            columns = [desc[0] for desc in cursor.description]
            dicts = [dict(zip(columns, row)) for row in results]
    except:
        return [{}], ""
    finally:
        cursor.close()

    map_link = get_map_link("get_river_zones_for_egrid", {"egrid": egrid})
    return dicts, map_link
