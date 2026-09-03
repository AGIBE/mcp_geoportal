FROM python:3.14.7-slim as builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv

ADD . /app

# COPY pyproject.toml ./
# COPY uv.lock* ./
# COPY README.md* ./

RUN uv sync --frozen --no-dev --no-cache

FROM python:3.14.7-slim

WORKDIR /app

#RUN groupadd appuser && useradd -m -g appuser appuser

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv

COPY --from=builder /app/.venv /app/.venv

#COPY --chown=appuser:appuser . .
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
RUN python -c "import duckdb; duckdb.sql('INSTALL spatial; LOAD spatial;')"

# appuser

CMD ["python", "src/mcp_geoportal/mcp_server_geoportal.py", "--mode", "http"]