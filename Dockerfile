# syntax=docker/dockerfile:1

# ── Stage 1: build the React frontend ────────────────────────────────────────
FROM node:20-alpine AS client
WORKDIR /client
COPY client/package.json client/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY client/ ./
RUN npm run build

# ── Stage 2: Python runtime — FastAPI serves the API *and* the built SPA ─────
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATABASE_URL=sqlite:////app/data/ajaia_docs.db

WORKDIR /app/server
COPY server/requirements.txt ./
RUN pip install -r requirements.txt

COPY server/ ./
# main.py looks for the SPA at ../client/dist relative to the server package.
COPY --from=client /client/dist /app/client/dist

RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/data && chown appuser /app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/api/health')" || exit 1

# Hosts like Render inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:application --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
