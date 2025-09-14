# ---------- Base (gemeinsam für alle Stages) ----------
FROM python:3.12-slim AS base

# Keine interaktiven Prompts, schnellere Pip-Installs
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

# System-Dependencies minimal (certs, locales, optional git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Nur Build-Metadaten zuerst kopieren, damit Layer-Caching greift
# (passt zu deinem Repo: pyproject.toml + README.md + ggf. requirements.txt)
COPY pyproject.toml README.md ./

# Falls du eine requirements.txt nutzt (z. B. für dev), optional:
# COPY requirements.txt ./

# ---------- Builder: installiert das Paket ----------
FROM base AS builder
RUN python -m pip install --upgrade pip wheel build
# Project-Quellcode
COPY src ./src
# (Optional) Falls es Konsolen-Skripte im Tests-Ordner gibt:
# COPY tests ./tests

# Installiere das Projekt inklusive Abhängigkeiten
# PEP 517 Build + Install, stabil & reproducible
RUN python -m build --wheel --outdir /dist \
 && pip install /dist/*.whl

# ---------- Test-Stage (optional, nur wenn du im Image testen willst) ----------
FROM builder AS tester
# pytest nur für diese Stage installieren
#RUN pip install pytest pytest-cov
RUN pip install -e ".[dev]"
COPY tests ./tests
# Führe Tests aus (kann via CI o. Build arg übersprungen werden)
# Tipp: Im CI diese Stage explizit bauen: `docker build --target tester .`
RUN pytest -q --cov=src --cov-report=term-missing

# ---------- Runtime: schlankes End-Image ----------
FROM base AS runtime

# Nicht als root laufen
RUN useradd -u 10001 -m appuser
USER appuser

# Nur das bereits gebaute Wheel + Runtime-Abhängigkeiten übernehmen
# -> effizient & sauber
COPY --from=builder /usr/local /usr/local

WORKDIR /app

# Standard-Entrypoint für dein CLI (laut Projektstruktur: rolling_returns.cli:main_rr)
# Beispiel: `docker run --rm app legacyex --csv-file ...`
ENTRYPOINT ["python", "-m", "rolling_returns.cli"]
# Alternativ: CMD leer lassen, damit man alles frei übergeben kann
# CMD ["--help"]
