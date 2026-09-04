import pytest

from mcp.client import Client

from mcp_geoportal.mcp_server_geoportal import mcp

@pytest.mark.asyncio
async def test_bfsnr_for_gemeinde_mcp_valid(unique_gemeinde):
    async with Client(mcp) as client:
        result = await client.call_tool("Suche_BFSNR_zu_Gemeinde", {"searchtext": unique_gemeinde[0]})
        assert result.structured_content['result'] == unique_gemeinde[1]

