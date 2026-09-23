import pytest


@pytest.mark.anyio
async def test_get_gemeinde_infos_mcp_valid_bfsnr(mcp_session, bfnsr_valid):
    result = await mcp_session.call_tool(
        "Hole_Gemeindeinfos_zu_BFSNummer", {"bfs_nr": bfnsr_valid}
    )
    result_content = result.structured_content

    assert "Einwohnerzahl" in result_content.keys()


@pytest.mark.anyio
async def test_get_gemeinde_infos_mcp_invalid_bfsnr(mcp_session, bfnsr_invalid):
    result = await mcp_session.call_tool(
        "Hole_Gemeindeinfos_zu_BFSNummer", {"bfs_nr": bfnsr_invalid}
    )
    result_content = result.structured_content

    assert result_content == {}


@pytest.mark.anyio
async def test_get_bohrprofile_egrid_mcp_valid(mcp_session, egrid_valid):
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
async def test_get_bohrprofile_egrid_mcp_invalid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_Bohrprofile_zu_EGRID", {"egrid": egrid_invalid}
    )
    result_content = result.structured_content["result"]

    result_list = result_content[0]
    map_link = result_content[1]

    assert result_list[0] == {}
    assert map_link == ""


@pytest.mark.anyio
async def test_get_naturgefahren_egrid_mcp_valid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_Naturgefahreninfo_zu_EGRID", {"egrid": egrid_valid}
    )

    result_content = result.structured_content["result"]

    result_dict = result_content[0]
    map_link = result_content[1]

    assert map_link.startswith("https://www.topo.apps.be.ch")
    assert "Lawine" in result_dict.keys()


@pytest.mark.anyio
async def test_get_naturgefahren_egrid_mcp_invalid(mcp_session, egrid_invalid):
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
