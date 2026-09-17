import pytest

from mcp_geoportal.tools import __get_bfsnr_for_gemeinde, __get_egrid_from_address

@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_valid(unique_gemeinde, api_definitions):
    result = await __get_bfsnr_for_gemeinde(unique_gemeinde[0], api_definitions)
    assert result == unique_gemeinde[1]

@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_inexisting_gemeinde(not_existing_gemeinde, api_definitions):
    result = await __get_bfsnr_for_gemeinde(not_existing_gemeinde, api_definitions)

    assert "hinweis" in result.keys()

@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_multiple_results(multiple_gemeinde, api_definitions):
    result = await __get_bfsnr_for_gemeinde(multiple_gemeinde, api_definitions)

    assert "hinweis" in result.keys()
    assert "optionen" in result.keys()
    assert isinstance(result['optionen'] , list)