# Utilisation d'une image légère
FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système nécessaires pour certaines libs python (si besoin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances (Python)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le code source du dossier backend
COPY . .

# Exposition du port FastAPI
EXPOSE 8000

# Lancement de l'app avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]