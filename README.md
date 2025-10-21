# Einleitung
Dieser Ordner enthält einen einfachen POC für einen MCP-Server, der in einem LLM wie z.B. Claude Desktop verwendet wird.

# Voraussetzungen
- uv installiert und im Pfad (https://docs.astral.sh/uv/)
- just installiert und im Pfad (https://github.com/casey/just)
- Node.js installiert und im Pfad (https://nodejs.org/en); V22.19.0 (LTS) als Standalone Binary (ZIP) downloaden, entpacken, kopieren und PATH setzen.
- Claude Desktop installiert & Konto eingerichtet (https://claude.ai/download)

# Debugging mit MCP Inspector
Der MCP-Server kann mit dem im SDK eingebauten MCP Inspector (Webapplikation) getestet und debugged werden. Das ist besonders nützlich weil z.B. Claude Desktop nur ein ziemliche limitierte Anzahl Prompts zulässt, die schnell aufgebraucht sind. Der MCP Inspector kann folgendermassen gestartet werden:
1. In der Kommandozeile in das Verzeichnis des MCP-Servers wechseln
2. just local_dev ausführen
    - Python Environment wird installiert
    - evtl. muss eine Node.JS-Installationsfrage mit Ja beantwortet werden
    - anschliessend geht ein Browser-Fenster mit dem MCP-Inspector auf.

# Integration in Claude Desktop
Damit Claude Desktop den MCP-Server erkennt, muss dieser ihm per Config-File bekannt gemacht werden. Ein Beispiel ist im Repository abgelegt (claude_desktop_config.json). Die Pfade darin sind bei Bedarf (Pfad zu uv und der Pfad zum Repository) anzupassen. Das File wird im Verzeichnis C:\Users\M9K3\AppData\Roaming\Claude abgelegt. Wenn alle Pfade stimmen, dann wird Claude den MCP-Server beim Aufstarten erkennen und diesen starten.

# Alternativen zu Claude Desktop
Claude Desktop erlaubt im freien Abo nur wenige Prompts, so dass man schnell ausgeschossen ist. Daher ist es theoretisch eine Option, ein lokal installiertes LLM zu verwenden. Das sollte grob gesagt mit folgenden Schritten klappen:
- OLLAMA installieren und eines der grösseren LLMs installieren (https://ollama.com/)
- oterm installieren (https://github.com/ggozad/oterm)
- den MCP-Server bei oterm bekanntmachen (https://ggozad.github.io/oterm/mcp/)
Achtung: dieses Vorgehen braucht recht viel Diskplatz und läuft evtl. nur mit einer guten Grafikkarte einigermassen rund! Und: oterm auf Windows zu installieren, ist auch aufwendig.

# Links
- Einführung zu MCP: https://medium.com/@laurentkubaski/mcp-explained-45312250b161
- Offizielle MCP-Seite: https://modelcontextprotocol.io/docs/getting-started/intro
- Python SDK für MCP: https://github.com/modelcontextprotocol/python-sdk