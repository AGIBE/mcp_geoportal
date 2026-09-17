import pytest
from mcp import ClientSession
from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client

from mcp_geoportal.mcp_server_geoportal import mcp


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="Eines von dev, test, prod",
        choices=["dev", "google"],
    )

class SessionAdapter:
    """Vereinheitlicht Client (lokal) und ClientSession (web) auf eine gemeinsame Schnittstelle."""
    def __init__(self, backend):
        self._backend = backend

    async def list_tools(self):
        return await self._backend.list_tools()

    async def call_tool(self, name, arguments=None):
        return await self._backend.call_tool(name, arguments=arguments)

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def environment(pytestconfig):
    return pytestconfig.getoption("--env")

@pytest.fixture
def server_url(environment):
    if environment == 'google':
        url = 'https://mcp-geoportal-580214340102.europe-west6.run.app/mcp'
    elif environment == 'prod':
        #TODO: Produktive Bedag-URL
        url = ''
    elif environment == 'test':
        #TODO: Test Bedag-URL
        url = ''
    else:
        # DEV: die Fixture wird dann gar nicht verwendet.
        url =''

    return url

@pytest.fixture
async def mcp_session(environment, server_url):
    if environment == 'dev':
        async with Client(mcp) as client:
            yield SessionAdapter(client)
    else:
        async with streamable_http_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield SessionAdapter(session)

@pytest.fixture
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

@pytest.fixture
def unique_gemeinde() -> tuple:
    """Gemeindename, der ein eindeutiges Ergebnis zurückgibt.
    """
    return ("Nidau", 743)

@pytest.fixture
def not_existing_gemeinde() -> str:
    """Gemeindename, der kein Ergebnis zurückgibt.
    """
    return ("asdfasdfsfadfa")

@pytest.fixture
def multiple_gemeinde() -> str:
    """Gemeindename, der mehrere Ergebnisse zurückgibt.
    """
    return ("igen")
