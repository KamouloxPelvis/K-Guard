# Utilisation d'une image légère mais complète
FROM python:3.10-slim

# Installation des dépendances système et de Trivy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    ca-certificates \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.49.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie et installation des dépendances (Python)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# On s'assure que le dossier de cache Trivy existe et appartient à l'utilisateur
RUN mkdir -p /root/.cache/trivy

# Exposition du port FastAPI
EXPOSE 8000

# Commande de lancement
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips='*'"]