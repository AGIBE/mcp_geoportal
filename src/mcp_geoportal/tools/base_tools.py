import re
from typing import Union

import httpx

# TODO Basisfunktionen ausbauen
# TODO: z.B. Von Koordinate zu Gemeinde / EGRID
# TODO: von einer Parzellennummer zu EGRID


async def __get_bfsnr_for_gemeinde(
    searchtext: str, api_definitions: dict
) -> Union[float, dict]:
    """
    Args:
        searchtext (str): Suchtext mit dem nach der BFS-Nummer gesucht wird (Format: Gemeindename).
    Returns:
        float: BFS-Nummer
    """
    url_search = f"{api_definitions['metawarehouse']['api_url']}/rpc/oereb_search"
    params = {"searchtext": searchtext, "origins": "grenz5"}
    result = httpx.get(url_search, params=params)
    js = result.json()
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

async def __get_egrid_from_address(
    searchtext: str, api_definitions: dict
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
    result = httpx.get(url_search, params=params)
    js = result.json()
    result_ohneplz = (re.sub(r"\b\d{4}\b\s*", "", js[0]["label"])).lower()
    if result_ohneplz == searchtext.replace(",", "").lower():
        # Prüfen, ob der erste Eintrag identisch mit dem searchtext ist
        x = js[0]["x"]
        y = js[0]["y"]

        url_oereb = f"{api_definitions['oereb_server']['api_url']}/getegrid/json/?EN={x},{y}"
        result = httpx.get(url_oereb)
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
