import httpx

async def __get_oereb_themes(api_definitions: dict) -> dict[str, str]:
    """Frage im ÖREB-Kataster des Kantons Bern alle verfügbaren Themen ab."""
    url = f"{api_definitions['oereb_server']['api_url']}/capabilities/json"
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

async def __get_oereb_auszug(egrid: str, api_definitions: dict) -> str:
    """Erstelle für eine Parzelle/Grundstück einen Auszug aus dem ÖREB-Kataster und lies alle vorhandenen Eigentumsbeschränkungen aus.

    Args:
        egrid: Eidgenössischer Grundstück-Identifikator. Beginnt mit "CH".

    """
    url = f"{api_definitions['oereb_server']['api_url']}/extract/xml?egrid={egrid}&lang=de"
    result = httpx.get(url)
    return result.text
