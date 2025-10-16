# use PowerShell instead of sh:
set shell := ["cmd.exe", "/c"]

list:
    just --list

dev:
    uv run mcp dev src\mcp_geoportal\mcp_server_geoportal.py

run:
    uv run python src\mcp_geoportal\mcp_server_geoportal.py