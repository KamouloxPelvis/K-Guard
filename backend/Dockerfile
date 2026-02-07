FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Exposition du port
EXPOSE 8000

# Lancement de l'app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]