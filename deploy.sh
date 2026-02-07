#!/bin/bash

echo "🚀 Début du déploiement K-GUARD..."

# 1. Build des images
docker build -t k-guard-backend:latest ./backend
docker build -t k-guard-frontend:latest ./frontend/k-guard

# 2. Export et Import pour K3s
docker save k-guard-backend:latest -o backend.tar
docker save k-guard-frontend:latest -o frontend.tar
sudo k3s ctr images import backend.tar
sudo k3s ctr images import frontend.tar

# 3. Application Kubernetes
kubectl apply -f k8s/

# 4. NETTOYAGE AUTOMATIQUE
echo "🧹 Nettoyage des résidus de build..."
rm *.tar
docker system prune -f
docker image prune -a -f --filter "until=24h" # Garde les images de moins de 24h au cas où

echo "✅ Déploiement terminé et VPS nettoyé !"