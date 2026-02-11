#!/bin/bash
# setup.sh - Orchestration K-Guard pour Kamal

# On se place dans le dossier du script
cd "$(dirname "$0")"

echo "🛡️  Lancement du Pre-flight Check..."
python3 check_env.py || exit 1

echo "🔧 Configuration de l'environnement hôte..."

# 1. Configuration K3s & Socket
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
sudo chmod 666 /run/k3s/containerd/containerd.sock

# 2. Cache Trivy
TRIVY_CACHE="$HOME/.cache/trivy"
mkdir -p "$TRIVY_CACHE"
sudo chown -R $(whoami):$(whoami) "$TRIVY_CACHE"

# 3. Build & Run Backend
echo "🏗️  Construction du Backend..."
# On remonte à la racine pour le contexte Docker
docker build -t k-guard-backend ../backend

echo "🚀 Lancement du conteneur Backend..."
docker rm -f k-guard-app 2>/dev/null
docker run -d \
  --name k-guard-app \
  -p 8000:8000 \
  -v /etc/rancher/k3s/k3s.yaml:/etc/rancher/k3s/k3s.yaml:ro \
  -v /run/k3s/containerd/containerd.sock:/run/k3s/containerd/containerd.sock \
  -v "$TRIVY_CACHE":/root/.cache/trivy \
  --env-file ../backend/.env \
  -e KUBECONFIG=/etc/rancher/k3s/k3s.yaml \
  --restart unless-stopped \
  k-guard-backend

# 4. Build & Run Frontend
echo "🌐 Configuration du Frontend..."
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "🌍 IP détectée : $IP_ADDR"
read -p "Confirmer l'IP pour l'API (ou saisir manuellement) : " USER_IP
FINAL_IP=${USER_IP:-$IP_ADDR}

echo "🏗️  Construction du Frontend (URL: http://$FINAL_IP:8000)..."
docker build --build-arg VITE_API_URL=http://$FINAL_IP:8000 -t k-guard-frontend ../frontend

echo "🚀 Lancement du Frontend sur le port 80..."
docker rm -f k-guard-ui 2>/dev/null
docker run -d \
  --name k-guard-ui \
  -p 80:80 \
  --restart unless-stopped \
  k-guard-frontend

echo "✅ DÉPLOIEMENT TERMINÉ !"
echo "📊 Dashboard accessible sur : http://$FINAL_IP"