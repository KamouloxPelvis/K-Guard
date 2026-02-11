#!/bin/bash

cd "$(dirname "$0")/.." || exit

echo "🚀 Début du déploiement K-GUARD..."

# 1. Détection de l'IP pour le lien Front/Back
VPS_IP=$(hostname -I | awk '{print $1}')
echo "🌐 API Target: http://$VPS_IP:8000"

# 2. Build des images (avec injection de l'URL API pour le Front)
echo "📦 Building images..."
docker build -t k-guard-backend:latest ./backend
docker build --build-arg VITE_API_URL=http://$VPS_IP:8000 -t k-guard-frontend:latest ./frontend

# 3. Export et Import pour K3s (Injection directe dans containerd)
echo "🚚 Transfert des images vers K3s..."
docker save k-guard-backend:latest -o backend.tar (avec injection de l'URL API pour le Front)
docker save k-guard-frontend:latest -o frontend.tar

sudo k3s ctr images import backend.tar
sudo k3s ctr images import frontend.tar

# 4. Application Kubernetes
echo "☸️ Applying Kubernetes manifests..."
kubectl apply -f k8s/

# 5. NETTOYAGE
echo "🧹 Nettoyage des résidus..."
rm backend.tar frontend.tar
# On évite le prune -a -f qui pourrait supprimer d'autres images utiles sur ton VPS
docker image prune -f 

echo "✅ Déploiement terminé sur le cluster K3s !"