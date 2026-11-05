import time

import pytest


@pytest.fixture(autouse=True)
def pause_between_tests():
    """Die DuckDB-Aufrufe können bei den auf geofiles gehosteten Parquet-Files sporadisch SSL-Fehler auslösen. Möglicherweise, weil der dortige Webserver nicht nachkommt. Daher wird hier zwischen jedem Test eine Pause eingelegt. Wenn die Parquet-Files dereinst auf einem richtigen Cloud Storage abgelegt sind, erübrigt sich das wohl wieder."""
    yield
    time.sleep(1.5)


@pytest.mark.anyio
async def test_get_municipality_infos_mcp_valid_bfsnr(mcp_session, bfnsr_valid):
    result = await mcp_session.call_tool(
        "Hole_Gemeindeinfos_zu_BFSNummer", {"bfs_nr": bfnsr_valid}
    )
    result_content = result.structured_content

    assert "Einwohnerzahl" in result_content.keys()


@pytest.mark.anyio
async def test_get_municipality_infos_mcp_invalid_bfsnr(mcp_session, bfnsr_invalid):
    result = await mcp_session.call_tool(
        "Hole_Gemeindeinfos_zu_BFSNummer", {"bfs_nr": bfnsr_invalid}
    )
    result_content = result.structured_content

    assert result_content == {}


@pytest.mark.anyio
async def test_get_coordinates_from_nomkl_mcp_valid(mcp_session, nomkl_string_valid):
    result = await mcp_session.call_tool(
        "Hole_Koordinaten_von_Ortsnamen_Flurnamen_Gelaendenamen",
        {"search_string": nomkl_string_valid},
    )
    result_content = result.structured_content["result"]

    assert "Gemeindename" in result_content[0].keys()


@pytest.mark.xfail(
    reason="Der Test macht keinen Sinn, da mit der Fuzzy-Suche immer ein Resultat zurückkommt.",
    strict=True,
)
@pytest.mark.anyio
async def test_get_coordinates_from_nomkl_mcp_invalid(
    mcp_session, nomkl_string_invalid
):
    result = await mcp_session.call_tool(
        "Hole_Koordinaten_von_Ortsnamen_Flurnamen_Gelaendenamen",
        {"search_string": nomkl_string_invalid},
    )
    result_content = result.structured_content["result"]

    assert "feedback" in result_content[0].keys()


@pytest.mark.anyio
async def test_get_borehole_profiles_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_Bohrprofile_zu_EGRID", {"egrid": egrid_valid}
    )
    result_content = result.structured_content["result"]

    result_list = result_content[0]
    map_link = result_content[1]

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert len(result_list) > 0
    assert "Sondiertyp" in result_list[0].keys()


@pytest.mark.anyio
async def test_get_borehole_profiles_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_Bohrprofile_zu_EGRID", {"egrid": egrid_invalid}
    )
    result_content = result.structured_content["result"]

    result_list = result_content[0]
    map_link = result_content[1]

    assert result_list[0] == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_natural_hazards_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_Naturgefahreninfo_zu_EGRID", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Lawine" in result_dict.keys()


@pytest.mark.anyio
async def test_get_natural_hazards_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_Naturgefahreninfo_zu_EGRID", {"egrid": egrid_invalid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert map_link == ""
    assert result_dict == {}


@pytest.mark.anyio
async def test_get_property_info_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_Grundstueck_Info", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert "Grundstücksnummer" in result_dict.keys()
    assert map_link.startswith("https://www.topo.apps.be.ch")


@pytest.mark.anyio
async def test_get_property_info_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_Grundstueck_Info", {"egrid": egrid_invalid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert result_dict == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_aed_locations_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_naechste_AED_Standorte_zu_EGRID", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert (
        "Adresse" in result_dict[0].keys()
    )  # Funktion gibt Liste von Standorten zurück
    assert map_link.startswith("https://www.topo.apps.be.ch")


@pytest.mark.anyio
async def test_get_aed_locations_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_naechste_AED_Standorte_zu_EGRID", {"egrid": egrid_invalid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert result_dict == [{}]
    assert map_link == ""


@pytest.mark.anyio
async def test_get_earthquake_risk_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_Erdbebenrisiko_zu_EGRID", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert "Gefährdungszone" in result_dict.keys()
    assert map_link.startswith("https://www.topo.apps.be.ch")


@pytest.mark.anyio
async def test_get_earthquake_risk_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_Erdbebenrisiko_zu_EGRID", {"egrid": egrid_invalid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert result_dict == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_river_zones_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_genehmigte_Gewaesserraeume_zu_EGRID", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_list = result_content[0]
    map_link = result_content[1]

    assert len(result_list[0]) > 0
    assert map_link.startswith("https://www.topo.apps.be.ch")


@pytest.mark.anyio
async def test_get_river_zones_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_genehmigte_Gewaesserraeume_zu_EGRID", {"egrid": egrid_invalid}
    )

    result_content = result.structured_content["result"]

    result_list = result_content[0]
    map_link = result_content[1]

    assert result_list == [{}]
    assert map_link == ""
