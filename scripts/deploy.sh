#!/bin/bash
# On se place à la racine du projet
cd "$(dirname "$0")/.." || exit

# --- 0. ASSISTANT D'INSTALLATION (Si .env absent) ---
if [ ! -f "backend/.env" ]; then
    if ! command -v whiptail &> /dev/null; then
        echo "📦 Installation des outils d'interface..."
        sudo apt-get update -y && sudo apt-get install -y whiptail
    fi

    whiptail --title "🛡️ K-Guard - Setup Assistant" \
            --msgbox "Bienvenue dans l'assistant d'installation.\n\nAucune configuration détectée. Nous allons générer vos accès sécurisés et configurer le domaine." 12 60

    USER_DOMAIN=$(whiptail --title "🌐 Configuration Réseau" \
                        --inputbox "Entrez le domaine ou l'IP publique de votre VPS :" 10 60 \
                        3>&1 1>&2 2>&3)

    ADMIN_PASS=$(whiptail --title "🔐 Sécurité Admin" \
                        --passwordbox "Définissez un mot de passe pour l'accès au Dashboard :" 10 60 \
                        3>&1 1>&2 2>&3)

    echo "⚙️ Génération des credentials..."
    python3 scripts/generate_creds.py "$USER_DOMAIN" "$ADMIN_PASS"

    whiptail --title "✅ Configuration terminée" \
            --msgbox "Le fichier .env a été généré.\n\nNotez bien vos accès. L'installation va maintenant commencer." 12 60
fi

# --- 1. PRE-FLIGHT & CONFIG ---
echo "🛡️ Pre-flight checks..."
python3 scripts/check_env.py || exit 1

VPS_IP=$(hostname -I | awk '{print $1}')
source backend/.env
TARGET_URL=${USER_DOMAIN:-$VPS_IP}

# --- 2. DÉPLOIEMENT AVEC ANIMATION ---
(
    echo 10 ; sleep 1
    # Templating Ingress
    sed "s/REPLACEME_DOMAIN/$TARGET_URL/g" k8s/ingress.yaml > k8s/ingress_tmp.yaml
    echo 20
    
    # Build des images Docker
    docker build -t k-guard-backend:latest ./backend > /dev/null 2>&1
    echo 40
    docker build --build-arg VITE_API_URL=http://$TARGET_URL -t k-guard-frontend:latest ./frontend > /dev/null 2>&1
    echo 60
    
    # Transfert vers le runtime K3s
    docker save k-guard-backend:latest -o backend.tar
    docker save k-guard-frontend:latest -o frontend.tar
    sudo k3s ctr images import backend.tar > /dev/null 2>&1
    sudo k3s ctr images import frontend.tar > /dev/null 2>&1
    echo 80
    
    # --- Kubernetes Orchestration ---
    # 1. Namespace
    kubectl create namespace k-guard --dry-run=client -o yaml | kubectl apply -f -
    echo 85
    
    # 2. Secret (Idempotent)
    kubectl create secret generic k-guard-secrets --from-env-file=backend/.env -n k-guard --dry-run=client -o yaml | kubectl apply -f -
    echo 90
    
    # 3. Manifestes globaux
    kubectl apply -f k8s/deployment.yaml -n k-guard > /dev/null 2>&1
    kubectl apply -f k8s/service.yaml -n k-guard > /dev/null 2>&1
    kubectl apply -f k8s/rbac.yaml -n k-guard > /dev/null 2>&1
    
    # 4. Ingress spécifique
    kubectl apply -f k8s/ingress_tmp.yaml -n k-guard > /dev/null 2>&1
    echo 95

    # 5. Forcer le redémarrage pour charger les nouvelles images/secrets
    kubectl rollout restart deployment k-guard-deployment -n k-guard > /dev/null 2>&1

    # 6. Nettoyage Cyber Hygiene
    kubectl delete deployment k-guard-deployment --namespace default --ignore-not-found > /dev/null 2>&1
    
    echo 100
    sleep 1
) | whiptail --title "🚀 Déploiement K-Guard" --gauge "Préparation et déploiement des conteneurs sur K3s..." 10 60 0

# --- 3. NETTOYAGE & FIN ---
rm -f backend.tar frontend.tar k8s/ingress_tmp.yaml
echo "⏳ Attente du démarrage des pods K-Guard..."

# Attendre que le déploiement soit considéré comme réussi par Kubernetes
kubectl rollout status deployment/k-guard-deployment -n k-guard --timeout=90s

if [ $? -eq 0 ]; then
    echo "-----------------------------------------------------"
    echo "✅ TOUS LES SYSTÈMES SONT OPÉRATIONNELS"
    echo "-----------------------------------------------------"
    # Affichage propre du statut final
    kubectl get pods -n k-guard -o wide
    echo ""
    echo "🌐 Dashboard : http://$TARGET_URL/k-guard/"
    echo "📚 API Docs  : http://$TARGET_URL/k-guard/api/docs"
else
    echo "-----------------------------------------------------"
    echo "❌ ERREUR : Le déploiement a pris trop de temps ou a échoué"
    echo "-----------------------------------------------------"
    kubectl get pods -n k-guard
    echo "🔍 Analyse des logs du backend :"
    kubectl logs -l app=k-guard -n k-guard -c backend --tail=20
    exit 1
fi

echo "-----------------------------------------------------"
echo "✅ K-Guard est déployé sur http://$TARGET_URL/k-guard"
echo "-----------------------------------------------------"