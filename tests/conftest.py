import duckdb
import httpx
import pytest
from mcp import ClientSession
from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client
from mcp_geoportal.mcp_server_geoportal import DUCKDB_EXTENSIONS, USER_AGENT, mcp


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
    if environment == "google":
        url = "https://mcp-geoportal-580214340102.europe-west6.run.app/mcp"
    elif environment == "prod":
        # TODO: Produktive Bedag-URL
        url = ""
    elif environment == "test":
        # TODO: Test Bedag-URL
        url = ""
    else:
        # DEV: die Fixture wird dann gar nicht verwendet.
        url = ""

    return url


@pytest.fixture
async def mcp_session(environment, server_url):
    if environment == "dev":
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
            "readyness_url": "https://www.metawarehouse.apps.be.ch",
        },
        "oereb_server": {
            "api_url": "https://www.oereb2.apps.be.ch",
            "readyness_url": "https://www.oereb2.apps.be.ch/version",
        },
        "geofiles": {
            "api_url": "https://geofiles.be.ch",
            "readyness_url": "https://geofiles.be.ch/readyness.txt",
        },
    }
    return apis


@pytest.fixture
def unique_gemeinde() -> tuple:
    """Gemeindename, der ein eindeutiges Ergebnis zurückgibt."""
    return ("Nidau", 743)


@pytest.fixture
def not_existing_gemeinde() -> str:
    """Gemeindename, der kein Ergebnis zurückgibt."""
    return "asdfasdfsfadfa"


@pytest.fixture
def multiple_gemeinde() -> str:
    """Gemeindename, der mehrere Ergebnisse zurückgibt."""
    return "igen"


@pytest.fixture
def unique_address() -> tuple:
    """Adresse, die ein eindeutiges Ergebnis zurückgibt."""
    return ("Reiterstrasse 11 Bern", "CH743546874207")


@pytest.fixture
def not_existing_address() -> str:
    """Adresse, die kein Ergebnis zurückgibt."""
    return "asdfasdfsfadfa"


@pytest.fixture
def multiple_address() -> str:
    """Adresse, die mehrere Ergebnisse zurückgibt."""
    return "Reiterstrasse"


@pytest.fixture
def egrid_valid() -> str:
    """Gültiger d.h. existierender EGRID."""
    return "CH743546874207"


@pytest.fixture
def egrid_invalid() -> str:
    """Ungültiger d.h. nichtexistierender EGRID."""
    return "1234asdf"


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=5, headers={"User-Agent": USER_AGENT})


@pytest.fixture
def duckdb_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:", config={"custom_user_agent": USER_AGENT})

    for ext in DUCKDB_EXTENSIONS:
        conn.install_extension(ext)
        conn.load_extension(ext)

    return conn


@pytest.fixture
def bfnsr_valid() -> int:
    """Existierende BFS-Nummer"""
    return 351


@pytest.fixture
def bfnsr_invalid() -> int:
    """Nicht existierende BFS-Nummer"""
    return 666666
