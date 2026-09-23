import logging
import re
from typing import Union

import httpx

logger = logging.getLogger("MCP_Geoportal_Logger")

# TODO Basisfunktionen ausbauen
# TODO: z.B. Von Koordinate zu Gemeinde / EGRID
# TODO: von einer Parzellennummer zu EGRID


async def __get_bfsnr_for_gemeinde(
    searchtext: str, api_definitions: dict, client: httpx.AsyncClient
) -> Union[int, dict]:
    """
    Args:
        searchtext (str): Suchtext mit dem nach der BFS-Nummer gesucht wird (Format: Gemeindename).
    Returns:
        float: BFS-Nummer
    """
    url_search = f"{api_definitions['metawarehouse']['api_url']}/rpc/oereb_search"
    params = {"searchtext": searchtext, "origins": "grenz5"}

    try:
        result = await client.get(url_search, params=params)
    except httpx.RequestError as exc:
        # Irgendein Fehler wurde zurückgegeben
        logger.error("Fehler beim Abrufen der ÖREB-Suche.")
        logger.error(f"URL: {url_search}")
        logger.error(exc)
        return {
            "hinweis": "Die Anfrage hat einen Fehler zurückgegeben. Bitte später nochmals probieren."
        }

    js = result.json()
    if js:
        result_ohnebfs = (re.sub(r"\s\d+", "", js[0]["label"])).lower()
        if len(js) == 1 or (result_ohnebfs == searchtext.lower()):
            # Prüfen, ob der erste Eintrag identisch mit dem searchtext ist
            bfsnr = int((re.findall(r"\s\d+", js[0]["label"])[0]).strip())

            return bfsnr
        else:
            adresslist = []
            for gemeinde in js:
                adresslist.append(gemeinde["label"])
            return {
                "hinweis": "Mehrdeutiger oder unpräziser Gemeindename. Bitte wähle eine der folgenden Gemeinden:",
                "optionen": adresslist,
            }
    else:
        # Keinen Treffer gefunden
        return {
            "hinweis": "Gemeindename nicht gefunden. Bitte nach einem anderen Gemeindenamen suchen."
        }


async def __get_egrid_from_address(
    searchtext: str, api_definitions: dict, client: httpx.AsyncClient
) -> Union[dict[str, float, float], dict]:
    """
    Args:
        searchtext (str): Suchtext mit dem nach der Adresse gesucht wird (Format: Strasse Nr., Gemeinde).

    Returns:
        dict:
            - egrid: E-GRID der Adresse. Beginnt mit "CH".
            - x: X-Koordinate der Adresse
            - y: Y-Koordinate der Adresse
    """
    url_search = f"{api_definitions['metawarehouse']['api_url']}/rpc/oereb_search"
    params = {"searchtext": searchtext}

    try:
        result = await client.get(url_search, params=params)
    except httpx.RequestError as exc:
        # Irgendein Fehler wurde zurückgegeben
        logger.error("Fehler beim Abrufen der ÖREB-Suche.")
        logger.error(f"URL: {url_search}")
        logger.error(exc)
        return {
            "hinweis": "Die Anfrage hat einen Fehler zurückgegeben. Bitte später nochmals probieren."
        }

    js = result.json()
    if js:
        result_ohneplz = (re.sub(r"\b\d{4}\b\s*", "", js[0]["label"])).lower()
        if result_ohneplz == searchtext.replace(",", "").lower():
            # Prüfen, ob der erste Eintrag identisch mit dem searchtext ist
            x = js[0]["x"]
            y = js[0]["y"]

            url_oereb = f"{api_definitions['oereb_server']['api_url']}/getegrid/json/?EN={x},{y}"
            try:
                result = await client.get(url_oereb)
            except httpx.RequestError as exc:
                # Irgendein Fehler wurde zurückgegeben
                logger.error("Fehler beim Abrufen des EGRIDs vom ÖREB-Servers.")
                logger.error(f"URL: {url_oereb}")
                logger.error(exc)
                return {
                    "hinweis": "Die Anfrage hat einen Fehler zurückgegeben. Bitte später nochmals probieren."
                }
            js = result.json()
            egrid = js["GetEGRIDResponse"][0]["egrid"]
            # return egrid
            return {"egrid": egrid, "x": x, "y": y}
        else:
            adresslist = []
            for adresse in js:
                adresslist.append(adresse["label"])
            return {
                "hinweis": "Mehrdeutige oder unpräzise Adresse. Bitte wähle eine der folgenden Adressen:",
                "optionen": adresslist,
            }
    else:
        # Keinen Treffer gefunden
        return {
            "hinweis": "Adresse nicht gefunden. Bitte nach einer anderen Adresse suchen."
        }


async def __get_geoproducts(
    api_definitions: dict, client: httpx.AsyncClient
) -> list[dict[str, str]]:
    """Gibt alle Geoprodukte aus dem MWH zurück (Code und Bezeichnung)

    Args:
        api_definitions (dict): _description_
        client (httpx.AsyncClient): _description_

    Returns:
        list[dict[str, str]]: Liste von Dicts (jeweils code und bezeichnung)
    """
    url_geoproducts = f"{api_definitions['metawarehouse']['api_url']}/geoportal_geoproduct?select=code,name"
    mwh_result = await client.get(url_geoproducts)
    result_list = []
    mwh_json = mwh_result.json()
    for gpr in mwh_json:
        gpr_dict = {"code": gpr["code"], "bezeichnung": gpr["name"]["de"]}
        result_list.append(gpr_dict)

    return result_list
