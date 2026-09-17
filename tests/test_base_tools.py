import pytest
from mcp_geoportal.tools import __get_bfsnr_for_gemeinde, __get_egrid_from_address


@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_valid_gemeinde(unique_gemeinde, api_definitions):
    result = await __get_bfsnr_for_gemeinde(unique_gemeinde[0], api_definitions)
    assert result == unique_gemeinde[1]


@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_inexisting_gemeinde(
    not_existing_gemeinde, api_definitions
):
    result = await __get_bfsnr_for_gemeinde(not_existing_gemeinde, api_definitions)

    assert "hinweis" in result


@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_multiple_results(multiple_gemeinde, api_definitions):
    result = await __get_bfsnr_for_gemeinde(multiple_gemeinde, api_definitions)

    assert "hinweis" in result
    assert "optionen" in result
    assert isinstance(result["optionen"], list)


@pytest.mark.anyio
async def test_egrid_from_address_valid_address(unique_address, api_definitions):
    result = await __get_egrid_from_address(unique_address[0], api_definitions)

    assert result["egrid"] == unique_address[1]


@pytest.mark.anyio
async def test_egrid_from_address_inexisting_address(
    not_existing_address, api_definitions
):
    result = await __get_egrid_from_address(not_existing_address, api_definitions)

    assert "hinweis" in result


@pytest.mark.anyio
async def test_egrid_from_address_multiple_address(multiple_address, api_definitions):
    result = await __get_egrid_from_address(multiple_address, api_definitions)

    assert "hinweis" in result
    assert "optionen" in result
    assert isinstance(result["optionen"], list)
