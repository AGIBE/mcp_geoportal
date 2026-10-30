import pytest


@pytest.mark.anyio
async def test_bfsnr_for_municipality_mcp_valid_municipality(unique_municipality, mcp_session):
    result = await mcp_session.call_tool(
        "Suche_BFSNR_zu_Gemeinde", {"searchtext": unique_municipality[0]}
    )
    assert result.structured_content["result"] == unique_municipality[1]


@pytest.mark.anyio
async def test_bfsnr_for_municipality_mcp_inexisting_municipality(
    not_existing_municipality, mcp_session
):
    result = await mcp_session.call_tool(
        "Suche_BFSNR_zu_Gemeinde", {"searchtext": not_existing_municipality}
    )
    assert "hinweis" in result.structured_content["result"]


@pytest.mark.anyio
async def test_bfsnr_for_municipality_mcp_multiple_municipality(multiple_municipality, mcp_session):
    result = await mcp_session.call_tool(
        "Suche_BFSNR_zu_Gemeinde", {"searchtext": multiple_municipality}
    )
    assert "hinweis" in result.structured_content["result"]
    assert "optionen" in result.structured_content["result"]
    assert isinstance(result.structured_content["result"]["optionen"], list)


@pytest.mark.anyio
async def test_egrid_for_address_mcp_valid_address(unique_address, mcp_session):
    result = await mcp_session.call_tool(
        "Suche_EGRID_fuer_Adresse", {"searchtext": unique_address[0]}
    )
    assert result.structured_content["result"]["egrid"] == unique_address[1]


@pytest.mark.anyio
async def test_egrid_for_address_mcp_inexisting_address(
    not_existing_address, mcp_session
):
    result = await mcp_session.call_tool(
        "Suche_EGRID_fuer_Adresse", {"searchtext": not_existing_address}
    )
    assert "hinweis" in result.structured_content["result"]


@pytest.mark.anyio
async def test_egrid_for_address_mcp_multiple_address(multiple_address, mcp_session):
    result = await mcp_session.call_tool(
        "Suche_EGRID_fuer_Adresse", {"searchtext": multiple_address}
    )
    assert "hinweis" in result.structured_content["result"]
    assert "optionen" in result.structured_content["result"]
    assert isinstance(result.structured_content["result"]["optionen"], list)


@pytest.mark.anyio
async def test_get_geoproducts_mcp(mcp_session):
    result = await mcp_session.call_tool("Hole_Geoprodukte")

    result_content = result.structured_content["result"]

    assert len(result_content) > 0
    assert "code" in result_content[0].keys()
