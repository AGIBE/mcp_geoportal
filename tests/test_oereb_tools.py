import pytest
from helpers import is_well_formed_xml

from mcp_geoportal.tools import __get_oereb_extract, __get_oereb_themes


@pytest.mark.anyio
async def test_get_oereb_themes(api_definitions, http_client):
    result = await __get_oereb_themes(api_definitions, http_client)
    theme_keys = list(result.keys())
    assert isinstance(result, dict)
    assert theme_keys[0].startswith("ch.")


@pytest.mark.anyio
async def test_get_oereb_extract_valid_egrid(egrid_valid, api_definitions, http_client):
    result = await __get_oereb_extract(egrid_valid, api_definitions, http_client)

    assert is_well_formed_xml(result)


@pytest.mark.anyio
async def test_get_oereb_extract_invalid_egrid(
    egrid_invalid, api_definitions, http_client
):
    result = await __get_oereb_extract(egrid_invalid, api_definitions, http_client)

    assert "hinweis" in result
