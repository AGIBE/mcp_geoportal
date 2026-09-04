import pytest

import mcp_geoportal

@pytest.fixture(scope="module")
def server_instance():
    mcp_geoportal.mcp_server_geoportal

@pytest.fixture(scope="module")
def api_definitions():
    apis = {
        "metawarehouse": {
            "api_url": "https://www.metawarehouse.apps.be.ch",
            "readyness_url": "https://www.metawarehouse.apps.be.ch"
        },
        "oereb_server": {
            "api_url": "https://www.oereb2.apps.be.ch",
            "readyness_url": "https://www.oereb2.apps.be.ch/version"
        },
        "geofiles": {
            "api_url": "https://geofiles.be.ch",
            "readyness_url": "https://geofiles.be.ch/readyness.txt"
        }
    }
    return apis

@pytest.fixture(scope="module")
def unique_gemeinde() -> tuple:
    """Gemeindename, der ein eindeutiges Ergebnis zurückgibt.
    """
    return ("Nidau", 743)

@pytest.fixture(scope="module")
def not_existing_gemeinde() -> str:
    """Gemeindename, der kein Ergebnis zurückgibt.
    """
    return ("asdfasdfsfadfa")

@pytest.fixture(scope="module")
def multiple_gemeinde() -> str:
    """Gemeindename, der mehrere Ergebnisse zurückgibt.
    """
    return ("igen")
