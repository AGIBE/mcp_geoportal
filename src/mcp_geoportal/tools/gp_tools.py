import json

import duckdb
from mcp.server.fastmcp import FastMCP
from tools.create_map_link import get_map_link

# Constants
MWH_API_BASE = "https://www.metawarehouse.apps.be.ch"
OEREB_API_BASE = "https://www.oereb2.apps.be.ch"


def register_gp_tools(server: FastMCP):
    "Hilfsfunktion zum Gruppieren und einfachen Importieren der gp-tools."
    # TODO: AED-Standort: Wo sind die nächste AED-Standort?
    # TODO: Gibt es in der Gemeinde XY unüberbaute Bauzonen?
    # TODO: Gibt es in der Gemeinde, in der Nähe von Gebäude im Bauinventar?
    # ADMGDE
    @server.tool(
            name="Hole_Gemeindeinfos_zu_BFSNummer",
            description="""Ermittelt für die übergebene BFS-Nummer einer Gemeinde im Kanton Bern statistische und administrative Informationen, unter anderem die Fläche, Einwohnerzahl und Bevölkerungsdichte pro ha.
            Returns:
                list: Eine Liste mit Dictionaries, die pro Gemeinde die Informationen zurückgibt."""
    )
    async def get_gemeinde_infos(bfs_nr:int) -> dict:
        """
        ADMGDE_GDEDAT
        """
        con = duckdb.connect()
        con.install_extension("spatial")
        con.load_extension("spatial")
        spatial_sql = f"""
                        select
                        espop AS Einwohnerzahl, espop_gmfl AS "Bevölkerungsdichte pro ha", gmdflaeche AS "Gemeindefläche in ha", url AS Website
                        from 'https://geofiles.be.ch/geoportal/pub/download/ADMGDE/admgde_gdedat.parquet'
                        where bfsnr = {bfs_nr}
                    """
        con.execute(spatial_sql)
        row = con.fetchone()
        if row is None:
            return {}
        columns = [desc[0] for desc in con.description]
        return dict(zip(columns, row))

    # GEOSOND
    @server.tool(
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
            str: Link zur Kartenansicht im Geoportal des Kantons Bern."""
    )
    async def get_bohrprofile_for_egrid(egrid: str) -> dict:
        """
        GEOSOND_GEOSOND
        """
        con = duckdb.connect()
        con.install_extension("spatial")
        con.load_extension("spatial")
        spatial_sql = f"""
                        select
                        typt_sondtyp_de as Sondiertyp, sond_datum as Sondierdatum, sond_tiefe as Sondiertiefe, round(ST_Distance(lif.geometry, gef.geometry)) as Entfernung, url as pdf_link
                        from 'https://geofiles.be.ch/geoportal/pub/download/MOPUBE/mopube_lif.parquet' lif
                        join 'https://geofiles.be.ch/geoportal/pub/download/GEOSOND/geosond_geosond.parquet' gef on ST_Intersects(lif.geometry, ST_Buffer(gef.geometry, 300))
                        where
                        lif.egrid = '{egrid}'
                    """
        con.execute(spatial_sql)
        results = con.fetchall()
        columns = [desc[0] for desc in con.description]
        dicts = [dict(zip(columns, row)) for row in results]

        map_link = get_map_link("get_bohrprofile_for_egrid", {"egrid": egrid})

        return dicts, map_link

    @server.tool(
            name="Hole_Naturgefahreninfo_zu_EGRID",
            description="""Ermittelt für eine Adresse (Strasse Hausnummer, Ort) die Naturgefahrestufe pro Gefahr (Einsturz/Absenkung, Wasser, Sturz, Lawine, Rutschung).
            Args:
                egrid (str): E-GRID für den die Naturgefahren ermittelt werden sollen.
            Returns:
                dict: Dictionnary mit den Naturgefahren für die Adresse im Format: {"gefahr": "gefahrenstufe"}.
                str: Link zur Kartenansicht im Geoportal des Kantons Bern."""
    )
    async def get_naturgefahren_for_egrid(egrid: str) -> dict:
        """
        NATGEFKA_GEFGEB
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
