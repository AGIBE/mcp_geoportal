FROM python:3.13.9-slim as builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.4 /uv /usr/local/bin/uv

COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md* ./

RUN uv sync --frozen --no-dev

FROM python:3.13.9-slim

WORKDIR /app

RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

COPY --from=ghcr.io/astral-sh/uv:0.9.4 /uv /usr/local/bin/uv

COPY --from=builder /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "src/mcp_geoportal/mcp_server_geoportal.py"]