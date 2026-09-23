import logging
import httpx

logger = logging.getLogger("MCP_Geoportal_Logger")


async def __get_oereb_themes(
    api_definitions: dict, client: httpx.AsyncClient
) -> dict[str, str]:
    """Frage im ÖREB-Kataster des Kantons Bern alle verfügbaren Themen ab."""
    url = f"{api_definitions['oereb_server']['api_url']}/capabilities/json"

    try:
        result = await client.get(url)
        result.raise_for_status()
    except httpx.RequestError as exc:
        # Irgendein Fehler wurde zurückgegeben
        logger.error("Fehler beim Abrufen der ÖREB-Themenliste vom ÖREB-Server")
        logger.error(f"URL: {url}")
        logger.error(exc)
        return {
            "hinweis": "Die Anfrage hat einen Fehler zurückgegeben. Bitte später nochmals probieren."
        }

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


async def __get_oereb_auszug(
    egrid: str, api_definitions: dict, client: httpx.AsyncClient
) -> str:
    """Erstelle für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und lies alle vorhandenen Eigentumsbeschränkungen aus.

    Args:
        egrid: Eidgenössischer Grundstück-Identifikator. Beginnt mit "CH".

    """
    url = f"{api_definitions['oereb_server']['api_url']}/extract/xml?egrid={egrid}&lang=de"
    try:
        result = await client.get(url)
        result.raise_for_status()
    except httpx.RequestError as exc:
        # Irgendein Fehler wurde zurückgegeben
        logger.error("Fehler beim Abrufen eines ÖREB-Auszugs vom ÖREB-Server")
        logger.error(f"URL: {url}")
        logger.error(exc)
        return {
            "hinweis": "Die Anfrage hat einen Fehler zurückgegeben. Bitte anderen EGRID abfragen oder später nochmals probieren."
        }
    if result.status_code == 200:
        return result.text
    elif result.status_code == 204:
        # EGRID wurde nicht gefunden (ÖREB-Server gibt hier 204 zurück)
        return {
            "hinweis": "EGRID nicht gefunden. Bitte nach einem anderen EGRID suchen."
        }
