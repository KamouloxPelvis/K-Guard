#!/bin/bash

# ==============================================================================
# 🛡️  K-GUARD CYBER-WIZARD (GUM + STABLE FUSION)
# Author: Kamal | Visit: https://devopsnotes.org
# ==============================================================================

# 0. Initialisation
# On s'assure d'être dans le dossier racine du projet
cd "$(dirname "$0")/.." || exit

# On s'assure aussi que Gum est bien installé sur la machine/VPS de l'utilisateur
command -v gum >/dev/null 2>&1 || { echo "Veuillez installer 'gum' d'abord."; exit 1; }

# Chargement de la config existante
if [ -f "backend/.env" ]; then
    source backend/.env
else
    echo "❌ Erreur: .env non trouvé. Lancez l'assistant d'installation d'abord."
    exit 1
fi

# Récupération intelligente de l'IP ou du Domaine
VPS_IP=$(hostname -I | awk '{print $1}')
TARGET_URL=${USER_DOMAIN:-$VPS_IP}

# --- Header Style Gum ---
clear
gum style \
    --foreground 212 --border-foreground 212 --border double \
    --align center --width 60 --margin "1 2" --padding "0 1" \
    "🛡️  K-GUARD " "K3S MONITOR & SECURITY OPERATOR" "Target: http://$TARGET_URL/k-guard"

# 1. CLEANING
    if kubectl get namespace k-guard >/dev/null 2>&1; then
        gum spin --spinner dot --title "Purging old namespace..." -- \
            kubectl delete namespace k-guard --wait=true
    fi
gum style --foreground 82 "  ✓ Environment cleared"

# 2. BUILDING
gum style --foreground 212 "🏗️  Starting Binary Builds..."

gum spin --spinner pulse --title "Compiling Backend Engine..." -- \
    docker build -t k-guard-backend:latest ./backend

# CRUCIAL : Injection de l'URL API pour Vite (Format: http://IP/k-guard)
gum spin --spinner pulse --title "Compiling Frontend Interface..." -- \
    docker build --build-arg VITE_API_URL="http://$TARGET_URL/k-guard" -t k-guard-frontend:latest ./frontend

# Vérification immédiate du build
if [[ "$(docker images -q k-guard-frontend:latest 2> /dev/null)" == "" ]]; then
    gum style --foreground 196 "❌ ERROR: Frontend build failed!"
    exit 1
fi
gum style --foreground 82 "  ✓ Images generated"

# 3. IMPORTING (Transfert Docker -> K3s Containerd)
gum style --foreground 212 "📦 Injecting into K3s Registry..."
docker save k-guard-backend:latest -o backend.tar
docker save k-guard-frontend:latest -o frontend.tar

gum spin --spinner line --title "Importing layers to K3s..." -- \
    bash -c "sudo k3s ctr images import backend.tar && sudo k3s ctr images import frontend.tar"

rm backend.tar frontend.tar
gum style --foreground 82 "  ✓ Registry updated"

# 4. ORCHESTRATION
gum style --foreground 212 "🚀 Kubernetes Orchestration..."

# Création du namespace d'abord (nécessaire avant les secrets)
kubectl create namespace k-guard --dry-run=client -o yaml | kubectl apply -f -

# Création des secrets depuis le .env
kubectl create secret generic k-guard-secrets --from-env-file=backend/.env -n k-guard --dry-run=client -o yaml | kubectl apply -f -

# Application des manifestes (On utilise directement ingress.yaml propre)
kubectl apply -f k8s/deployment.yaml -n k-guard > /dev/null
kubectl apply -f k8s/service.yaml -n k-guard > /dev/null
kubectl apply -f k8s/rbac.yaml -n k-guard > /dev/null
kubectl apply -f k8s/ingress.yaml -n k-guard > /dev/null

gum style --foreground 82 "  ✓ Manifests & Ingress applied"

# 5. FINAL STABILIZATION
echo ""
gum style --foreground 212 "📡 Final Health Check..."

# On attend que le déploiement soit prêt
if gum spin --spinner points --title "Waiting for Liveness Probes..." -- \
    kubectl rollout status deployment/k-guard-deployment -n k-guard --timeout=120s; then
    
    gum style \
        --foreground 82 --border-foreground 82 --border rounded \
        --align center --width 60 --margin "1" --padding "1" \
        "✅ K-GUARD IS ONLINE" \
        "Dashboard: http://$TARGET_URL/k-guard" \
        "API Health: http://$TARGET_URL/k-guard/api/k3s/health" \
        "Visit https://devopsnotes.org"
else
    gum style --foreground 196 --bold "❌ STABILIZATION FAILED"
    echo "🔍 Debugging Pods :"
    kubectl get pods -n k-guard
    # On affiche les logs du backend pour comprendre pourquoi ça a planté
    echo "📋 Backend Logs :"
    kubectl logs -l app=k-guard -c backend -n k-guard --tail=20
    echo "📋 Recent Events :"
    kubectl get events -n k-guard --sort-by='.lastTimestamp' | tail -n 10
    exit 1
fi