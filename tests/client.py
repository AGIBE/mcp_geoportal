#!/usr/bin/env python3
"""
Einfacher MCP-Client für einen entfernten Server über HTTPS.

Nutzt den "Streamable HTTP"-Transport (aktueller MCP-Standard für
netzwerkbasierte Server). Verbindet sich, listet die verfügbaren Tools
auf und ruft anschließend ein bestimmtes Tool mit Argumenten auf.

Voraussetzung:
    pip install mcp

Anpassen musst du:
    - SERVER_URL   -> die HTTPS-URL deines MCP-Servers
    - HEADERS      -> z. B. ein Auth-Token, falls der Server das braucht
    - TOOL_NAME / TOOL_ARGS -> welches Tool mit welchen Argumenten
                                aufgerufen werden soll
"""

import asyncio
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# --- Konfiguration -----------------------------------------------------

SERVER_URL = "https://mcp-geoportal-580214340102.europe-west6.run.app/mcp"

TOOL_NAME = "Hole_Gemeindeinfos_zu_BFSNummer"
TOOL_ARGS = {"bfs_nr": "743"}

# ------------------------------------------------------------------------


async def main() -> None:
    async with streamable_http_client(SERVER_URL) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            # Verbindung initialisieren (MCP-Handshake)
            await session.initialize()

            # Verfügbare Tools auflisten
            tools_result = await session.list_tools()
            print("Verfügbare Tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Ein bestimmtes Tool aufrufen
            start = time.time()
            print(f"\nRufe Tool '{TOOL_NAME}' auf mit Argumenten: {TOOL_ARGS}")
            result = await session.call_tool(TOOL_NAME, arguments=TOOL_ARGS)
            stop = time.time()
            duration = stop - start

            print("\nErgebnis:")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
                else:
                    print(content)

            print(f"Dauer: {duration}")

if __name__ == "__main__":
    asyncio.run(main())