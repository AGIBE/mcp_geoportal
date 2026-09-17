# use PowerShell instead of sh:
set shell := ["cmd.exe", "/c"]

list:
    just --list

# Startet den MCP-Inspector standalone und öffnet den Browser
inspector:
    npx @modelcontextprotocol/inspector

# Startet den MCP-Server lokal (stdio)
local:
    uv run python src\mcp_geoportal\mcp_server_geoportal.py --mode=stdio

# Startet den MCP-Server lokal (stdio) und den MCP-Inspector
local_dev:
    npx @modelcontextprotocol/inspector uv --directory C:/Daten/repos/mcp_geoportal run python src/mcp_geoportal/mcp_server_geoportal.py

# Startet den MCP-Server als Webservice
server:
    uv run python src\mcp_geoportal\mcp_server_geoportal.py --mode=http

# Führt die Test-Suite lokal aus
test_local:
    uv run pytest tests --env=dev

# Führt die Test-Suite gegen den MCP-Server bei Google aus
test_google:
    uv run pytest tests --env=google
