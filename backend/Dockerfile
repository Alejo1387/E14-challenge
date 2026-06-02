# Backend E14 Challenge — imagen para scripts y (futuro) API FastAPI
FROM python:3.12-slim-bookworm

# UV: instalar dependencias rápido (misma herramienta que en local)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencias primero (mejor caché al reconstruir la imagen)
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Código del backend
COPY config.py .
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Carpetas de datos (el volumen en compose montará data/ y logs/)
RUN mkdir -p data/raw data/processed logs

# Por defecto el contenedor queda vivo para ejecutar scripts con:
#   docker compose exec backend python scripts/setup_db.py
CMD ["sleep", "infinity"]
