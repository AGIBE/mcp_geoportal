import pytest

from mcp_geoportal.tools import (
    __get_bfsnr_for_municipality,
    __get_egrid_from_address,
    __get_geoproducts,
)


@pytest.mark.anyio
async def test_bfsnr_for_municipality_valid_municipality(
    unique_municipality, api_definitions, http_client
):
    result = await __get_bfsnr_for_municipality(
        unique_municipality[0], api_definitions, http_client
    )
    assert result == unique_municipality[1]


@pytest.mark.anyio
async def test_bfsnr_for_municipality_inexisting_municipality(
    not_existing_municipality, api_definitions, http_client
):
    result = await __get_bfsnr_for_municipality(
        not_existing_municipality, api_definitions, http_client
    )

    assert "hinweis" in result


@pytest.mark.anyio
async def test_bfsnr_for_municipality_multiple_results(
    multiple_municipality, api_definitions, http_client
):
    result = await __get_bfsnr_for_municipality(
        multiple_municipality, api_definitions, http_client
    )

    assert "hinweis" in result
    assert "optionen" in result
    assert isinstance(result["optionen"], list)


@pytest.mark.anyio
async def test_egrid_from_address_valid_address(
    unique_address, api_definitions, http_client
):
    result = await __get_egrid_from_address(
        unique_address[0], api_definitions, http_client
    )

    assert result["egrid"] == unique_address[1]


@pytest.mark.anyio
async def test_egrid_from_address_inexisting_address(
    not_existing_address, api_definitions, http_client
):
    result = await __get_egrid_from_address(
        not_existing_address, api_definitions, http_client
    )

    assert "hinweis" in result


@pytest.mark.anyio
async def test_egrid_from_address_multiple_address(
    multiple_address, api_definitions, http_client
):
    result = await __get_egrid_from_address(
        multiple_address, api_definitions, http_client
    )

    assert "hinweis" in result
    assert "optionen" in result
    assert isinstance(result["optionen"], list)


@pytest.mark.anyio
async def test_get_geoproducts(api_definitions, http_client):
    result = await __get_geoproducts(api_definitions, http_client)

    assert len(result) > 0
    assert "code" in result[0].keys()
