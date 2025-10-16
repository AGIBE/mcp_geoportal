FROM python:3.13.9-slim-bookworm as builder

COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /bin/uv

WORKDIR /usr/src/mcp_geoportal

ENV UV_COMPILE_BYTECODE=1

RUN apt-get update && apt-get -y upgrade && \
	DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
	libgeos-c1v5 libpq5 build-essential libgeos-dev libpq-dev

ADD . /usr/src/mcp_geoportal

RUN uv sync --frozen --no-dev --no-cache

FROM python:3.13.9-slim-bookworm

RUN apt-get update && apt-get -y upgrade && \
	DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
	gosu tini && \
    apt-get clean && \
    rm --force --recursive /var/lib/apt/lists/*

RUN groupadd mcp && useradd -g mcp mcprunner

WORKDIR /usr/src/mcp_geoportal

COPY --from=builder --chown=mcprunner:mcp /usr/src/mcp_geoportal /usr/src/mcp_geoportal

RUN chmod +x run_mcp_server_uvicorn.sh

ENV PATH="/usr/src/mcp_geoportal/.venv/bin:$PATH"

ENTRYPOINT [ "gosu", "oerebrunner", "tini", "--" ]

CMD ["/usr/src/mcp_geoportal/run_mcp_server_uvicorn.sh"]