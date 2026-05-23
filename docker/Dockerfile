# ── Stage 1: Base ────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ── Stage 2: Dependencies ───────────────────────────────────
FROM base AS deps

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install .

# ── Stage 3: Application ────────────────────────────────────
FROM deps AS app

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
