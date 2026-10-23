# Einleitung
Dieses Repository enthält einen MCP-Server, der für die Nutzung im Geoportal-Chatbot (auf Basis Apptiva Klar) aber auch in anderen Chatbots vorgesehen ist.

# Voraussetzungen
- uv installiert und im Pfad (https://docs.astral.sh/uv/)
- just installiert und im Pfad (https://github.com/casey/just)
- Node.js installiert und im Pfad (https://nodejs.org/en); V22.19.0 (LTS) als Standalone Binary (ZIP) downloaden, entpacken, kopieren und PATH setzen.
- Claude Desktop installiert & Konto eingerichtet (https://claude.ai/download)

# Debugging mit MCP Inspector
Der MCP-Server kann mit dem im SDK eingebauten MCP Inspector (Webapplikation) getestet und debugged werden. Das ist besonders nützlich weil z.B. Claude Desktop nur ein ziemlich limitierte Anzahl Prompts zulässt, die schnell aufgebraucht sind. Der MCP Inspector kann folgendermassen gestartet werden:
1. In der Kommandozeile in das Verzeichnis des MCP-Servers wechseln
2. just local_dev ausführen
    - Python Environment wird installiert
    - evtl. muss eine Node.JS-Installationsfrage mit Ja beantwortet werden
    - anschliessend geht ein Browser-Fenster mit dem MCP-Inspector auf. Dort einfach mit dem Server namens "uv" connecten und testen.

Im Justfile sind noch eine Reihe weiterer Commands definiert, die das Debuggen erleichtern. Sie sind im Justfile dokumentiert.

# Test-Suite
Der MCP-Server hat eine Reihe von Tests, die mit pytest ausgeführt werden können. Für jedes MCP-Tool gibt es Tests auf Stufe MCP - d.h. der Test wird via MCP gemacht - und auf Stufe der Funktion ohne MCP-Overhead. Dazu gibt es noch allgemeine Tests (test_general.py). 

# Integration in Claude Desktop
Damit Claude Desktop den MCP-Server erkennt, muss dieser ihm per Config-File bekannt gemacht werden. Ein Beispiel ist im Repository abgelegt (claude_desktop_config.json). Die Pfade darin sind bei Bedarf (Pfad zu uv und der Pfad zum Repository) anzupassen. Das File wird im Verzeichnis C:\Users\[USERID]\AppData\Roaming\Claude abgelegt. Wenn alle Pfade stimmen, dann wird Claude den MCP-Server beim Aufstarten erkennen und diesen starten. In Claude Desktop ist der MCP-Server dann unter den Konnektoren zu finden.

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
- Doku zu MCP Inspector: https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector

# Deployment
## Dockerfile
Der MCP-Server kann als Docker-Container betrieben werden (s. Dockerfile). Das Deployment erwartet folgende Umgebungsvariablen:
- MCP_WORKERS: Anzahl Worker in uvicorn
- MCP_MAX_REQUESTS: Maximale Anzahl Requests bis ein Worker restarted wird
- HTTP_PROXY / HTTPS_PROXY: Proxy-Konfiguration (für Aufrufen der externen APIs)
## Endpunkte für Probes
Für den Betrieb in einer Cloud-Umgebung sind nebst der MCP-Funktionalität noch zusätzliche Endpunkte definiert worden:
- /live: Gibt ein einfaches JSON zurück mit Status OK und der Uptime in Sekunden. Kann als Liveness-Probe dienen. Sagt nur etwas darüber aus, ob der Webservice noch läuft.
- /ready: Gibt ein JSON zurück mit dem Status aller externen APIs. Wenn eine der APIs nicht erreicht werden kann, wird ein HTTP 503 zurückgegeben, sonst 200. Kann als Readyness-Probe dienen.
- /version: gibt die Version des MCP-Servers aus.
## Github
Das Repository hat ein remote in der zentralen AGI-Ablage für Git-Repositories und eines auf Github (https://github.com/AGIBE/mcp_geoportal). Auf Github sind zwei Actions definiert, mit denen das Docker Image gebaut und die Test-Suite ausgeführt werden kann. Beide Actions werden im Moment nur bei Bedarf d.h. manuell ausgeführt. Das gebaute Docker Image ist unter Packages zu finden: https://github.com/AGIBE/mcp_geoportal/pkgs/container/mcp_geoportal
## Google Cloud Run
Bis zu einer definitiven Lösung wird der MCP-Server in der Google-Cloud (Google Cloud Run) betrieben. Er ist unter der folgenden URL erreichbar: https://mcp-geoportal-580214340102.europe-west6.run.app/mcp

Das Deployment auf Cloud Run wird automatisch aktualisiert und zwar jedes Mal, wenn auf Github etwas gepusht wird.