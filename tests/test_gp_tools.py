import pytest

from mcp_geoportal.tools import (
    __get_gemeinde_infos,
    __get_bohrprofile_for_egrid,
    __get_naturgefahren_for_egrid,
    __get_property_info_for_egrid,
)


@pytest.mark.anyio
async def test_get_gemeinde_infos_valid_bfsnr(
    bfnsr_valid, api_definitions, duckdb_connection
):
    result = await __get_gemeinde_infos(bfnsr_valid, api_definitions, duckdb_connection)

    assert "Einwohnerzahl" in result.keys()


@pytest.mark.anyio
async def test_get_gemeinde_infos_invalid_bfsnr(
    bfnsr_invalid, api_definitions, duckdb_connection
):
    result = await __get_gemeinde_infos(
        bfnsr_invalid, api_definitions, duckdb_connection
    )

    assert result == {}


@pytest.mark.anyio
async def test_get_bohrprofile_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_list, map_link = await __get_bohrprofile_for_egrid(
        egrid_valid, api_definitions, duckdb_connection
    )

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert len(result_list) > 0
    assert "Sondiertyp" in result_list[0].keys()


@pytest.mark.anyio
async def test_get_bohrprofile_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_list, map_link = await __get_bohrprofile_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection
    )

    assert result_list[0] == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_naturgefahren_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_naturgefahren_for_egrid(
        egrid_valid, api_definitions, duckdb_connection
    )

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Lawine" in result_dict.keys()


@pytest.mark.anyio
async def test_get_naturgefahren_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_naturgefahren_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection
    )

    assert map_link == ""
    assert result_dict == {}


@pytest.mark.anyio
async def test_get_property_info_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_property_info_for_egrid(
        egrid_valid, api_definitions, duckdb_connection
    )

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Grundstücksnummer" in result_dict.keys()


@pytest.mark.anyio
async def test_get_property_info_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_property_info_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection
    )

    assert map_link == ""
    assert result_dict == {}
