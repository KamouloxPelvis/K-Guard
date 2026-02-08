import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config  # <--- AJOUTÉ
# On importe ta logique métier automatisée
from k3s_manager import get_k3s_status 

app = FastAPI(title="K-Guard API")

# Configuration du client Kubernetes
try:
    # On essaie de charger la config K3s locale [cite: 2026-02-07]
    config.load_kube_config()
except:
    # Si on est dans le cluster (VPS), on utilise la config interne
    config.load_incluster_config()

v1 = client.CoreV1Api() # <--- L'OBJET MANQUANT EST ICI

# Sécurité pour le développement local [cite: 2026-02-07]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/k3s/health")
async def get_cluster_health():
    """Appelle ton script de monitoring pour le dashboard"""
    return get_k3s_status()

@app.get("/")
async def root():
    return {"status": "K-Guard Live", "operator": "Kamal"}

@app.get("/api/k3s/logs/{pod_name}")
async def get_pod_logs(pod_name: str):
    """Récupère les logs pour le dépannage [cite: 2026-02-07]"""
    try:
        # v1 est maintenant bien défini
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace="default", tail_lines=100)
        return {"logs": logs}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/k3s/restart/{namespace}/{pod_name}")
async def restart_pod(namespace: str, pod_name: str):
    """Force le redémarrage d'un pod en le supprimant"""
    try:
        # v1 est maintenant bien défini
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"status": "success", "message": f"Pod {pod_name} is restarting..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}