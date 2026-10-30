import pytest
from mcp_geoportal.tools import (
    __get_borehole_profiles_for_egrid,
    __get_municipality_infos,
    __get_natural_hazards_for_egrid,
    __get_property_info_for_egrid,
    __get_coordinates_from_nomkl,
    __get_aed_locations_for_egrid,
    __get_earthquake_risk_for_egrid
)


@pytest.mark.anyio
async def test_get_municipality_infos_valid_bfsnr(
    bfnsr_valid, api_definitions, duckdb_connection
):
    result = await __get_municipality_infos(bfnsr_valid, api_definitions, duckdb_connection)

    assert "Einwohnerzahl" in result.keys()


@pytest.mark.anyio
async def test_get_municipality_infos_invalid_bfsnr(
    bfnsr_invalid, api_definitions, duckdb_connection
):
    result = await __get_municipality_infos(
        bfnsr_invalid, api_definitions, duckdb_connection
    )

    assert result == {}

    
@pytest.mark.anyio
async def test_get_coordinates_from_nomkl_valid(
    nomkl_string_valid, api_definitions, duckdb_connection
):
    result_list = await __get_coordinates_from_nomkl(
        nomkl_string_valid, api_definitions, duckdb_connection
    )
    
    assert "Gemeindename" in result_list[0].keys()


@pytest.mark.anyio
async def test_get_coordinates_from_nomkl_invalid(
    nomkl_string_invalid, api_definitions, duckdb_connection
):
    result_list = await __get_coordinates_from_nomkl(
        nomkl_string_invalid, api_definitions, duckdb_connection
    )

    assert "feedback" in result_list[0].keys()

@pytest.mark.anyio
async def test_get_borehole_profiles_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_list, map_link = await __get_borehole_profiles_for_egrid(
        egrid_valid, api_definitions, duckdb_connection
    )

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert len(result_list) > 0
    assert "Sondiertyp" in result_list[0].keys()


@pytest.mark.anyio
async def test_get_borehole_profiles_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_list, map_link = await __get_borehole_profiles_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection
    )

    assert result_list[0] == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_natural_hazards_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_natural_hazards_for_egrid(
        egrid_valid, api_definitions, duckdb_connection
    )

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Lawine" in result_dict.keys()


@pytest.mark.anyio
async def test_get_natural_hazards_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_natural_hazards_for_egrid(
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

@pytest.mark.anyio
async def test_get_aed_locations_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_aed_locations_for_egrid(
            egrid_valid, api_definitions, duckdb_connection
        )
    
    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Adresse" in result_dict[0].keys() # Funktion gibt Liste mit Standorten zurück

@pytest.mark.anyio
async def test_get_aed_locations_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection
):
    result_dict, map_link = await __get_aed_locations_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection
    )

    assert map_link == ""
    assert result_dict == [{}]


@pytest.mark.anyio
async def test_get_earthquake_risk_egrid_valid(
    egrid_valid, api_definitions, duckdb_connection, http_client
):
    result_dict, map_link = await __get_earthquake_risk_for_egrid(
            egrid_valid, api_definitions, duckdb_connection, http_client
        )
    
    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Gefährdungszone" in result_dict.keys()

@pytest.mark.anyio
async def test_get_earthquake_risk_egrid_invalid(
    egrid_invalid, api_definitions, duckdb_connection, http_client
):
    result_dict, map_link = await __get_earthquake_risk_for_egrid(
        egrid_invalid, api_definitions, duckdb_connection, http_client
    )

    assert map_link == ""
    assert result_dict == {}
