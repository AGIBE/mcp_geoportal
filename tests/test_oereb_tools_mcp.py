import pytest
from helpers import is_well_formed_xml

@pytest.mark.anyio
async def test_get_oereb_themes_mcp(mcp_session):
    result = await mcp_session.call_tool("Suche_Themen_OEREB_Kataster")
    result_content = result.structured_content

    theme_keys = list(result_content.keys())
    assert isinstance(result_content, dict)
    assert theme_keys[0].startswith('ch.')

@pytest.mark.anyio
async def test_get_oereb_auszug_mcp_valid_egrid(mcp_session, egrid_valid):
    result = await mcp_session.call_tool(
        "Hole_OEREB_Auszug",
        {"egrid": egrid_valid}
    )

    assert is_well_formed_xml(result.structured_content['result'])

@pytest.mark.anyio
async def test_get_oereb_auszug_mcp_invalid_egrid(mcp_session, egrid_invalid):
    result = await mcp_session.call_tool(
        "Hole_OEREB_Auszug",
        {"egrid": egrid_invalid}
    )

    assert "hinweis" in result.structured_content['result']
