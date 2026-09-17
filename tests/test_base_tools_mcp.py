import pytest


@pytest.mark.anyio
async def test_bfsnr_for_gemeinde_mcp_valid(unique_gemeinde, mcp_session):
        result = await mcp_session.call_tool("Suche_BFSNR_zu_Gemeinde", {"searchtext": unique_gemeinde[0]})
        assert result.structured_content['result'] == unique_gemeinde[1]

