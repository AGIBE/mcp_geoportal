import httpx
from mcp.server.fastmcp import FastMCP

# Constants
MWH_API_BASE = "https://www.metawarehouse.apps.be.ch"
OEREB_API_BASE = "https://www.oereb2.apps.be.ch"


def register_oereb_tools(server: FastMCP):
    "Hilfsfunktion zum Gruppieren und einfachen Importieren der oereb-tools."
    
    @server.tool(
        name="Suche_Themen_OEREB_Kataster",
        description="""Fragt im ÖREB-Kataster des Kantons Bern alle verfügbaren Themen ab."""
    )
    async def get_oereb_themes() -> dict[str, str]:
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


    @server.tool(
            name="Hole_OEREB_Auszug",
            description="""Erstellt für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und liest alle vorhandenen Eigentumsbeschränkungen aus.
            Als Input wird der E-GRID benötigt."""
    )
    async def get_oereb_auszug(egrid: str) -> str:
        """Erstelle für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und lies alle vorhandenen Eigentumsbeschränkungen aus.

        Args:
            egrid: Eidgenössischer Grundstück-Identifikator. Beginnt mit "CH".

        """
        url = f"{OEREB_API_BASE}/extract/xml?egrid={egrid}&lang=de"
        result = httpx.get(url)
        return result.text

    # Braucht es nicht mehr, da es bereits eine Funktion gibt, die aus einer Adresse ein egrid ausgibt.
    # @server.tool()
    # async def get_oereb_auszug_for_address(searchtext: str) -> str:
        # """Ermittelt in einem ersten Schritt für die gesuchte Adresse den eidgenössischen Grundstück-Identifikator (EGRID).
        # Für diesen EGRID wird dann in einem zweiten Schritt ein Auszug aus dem Kataster der öffentlich-rechtlichen
        # Eigentumsbeschränkungen (ÖREB-Kataster) erstellt. Dessen Inhalt wird zurückgegeben.

        # Args:
            # searchtext (str): Suchtext mit dem nach der Adresse gesucht wird.

        # Returns:
            # list[str]: Liste der im Auszug enthaltenen Themen und deren Bezeichnung.
        # """
        # egrid = register_base_tools.get_egrid_from_address(searchtext)
        # auszug = get_oereb_auszug(egrid)
        # return auszug