# syntax=docker/dockerfile:1

# ---------- Stage 1: Builder ----------
FROM python:3.14.7-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Erst nur Dependency-Dateien -> Layer-Caching
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Restlichen Code kopieren und Projekt selbst installieren
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- Stage 2: Runtime ----------
FROM python:3.14.7-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Non-root User + Gruppe anlegen
RUN groupadd --system --gid 1000 appuser && \
    useradd --system --uid 1000 --gid appuser --create-home appuser

# Nur das fertige venv + Code aus der Builder-Stage übernehmen
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

# RUN python -c "import duckdb; duckdb.sql('INSTALL spatial; LOAD spatial;')"

EXPOSE 8000

CMD ["python", "src/mcp_geoportal/mcp_server_geoportal.py", "--mode", "http"]