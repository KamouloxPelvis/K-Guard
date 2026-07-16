# --- STAGE 1: Frontend Build Process ---
FROM node:22-bullseye AS build-frontend
WORKDIR /app/frontend

COPY frontend/package.json ./
COPY frontend/package-lock.json ./

RUN npm install --legacy-peer-deps

COPY frontend/ ./

RUN npm run build

# --- STAGE 2: Backend Runtime ---
FROM python:3.11-slim-bookworm 
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code backend et configuration
COPY backend/ ./backend/
COPY tests/ ./tests/
COPY infra/ ./infra/

# Copie du build frontend depuis la STAGE 1
COPY --from=build-frontend /app/frontend/dist /app/static

# Configuration SRE
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Préparation du répertoire de données et permissions
RUN mkdir -p /app/data && chown -R 1000:1000 /app
USER 1000

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]