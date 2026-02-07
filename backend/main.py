import os

from fastapi import FastAPI
from kubernetes import client, config
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="K-Guard K3s Operator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Pour le dev, on autorise tout
    allow_methods=["*"],
    allow_headers=["*"],
)
# On charge la config k3s
# Quand on lance l'API sur le VPS, il va chercher ~/.kube/config

try:
    config.load_kube_config()
except Exception:
    # Chemin exact sur Ubuntu avec k3s
    kube_path = "/etc/rancher/k3s/k3s.yaml"
    if os.path.exists(kube_path):
        os.environ["KUBECONFIG"] = kube_path
        config.load_kube_config()
    else:
        print("Alerte: Fichier k3s.yaml introuvable")

v1 = client.CoreV1Api()

@app.get("/")
async def root():
    return {"message": "K-Guard API is Live", "docs": "/docs"}

@app.get("/api/k3s/health")
async def get_cluster_health():
    """Récupère l'état de santé réel des apps de Kamal"""
    monitored_apps = ["blog-devopsnotes", "portfolio-portal", "k-guard"]
    results = []
    
    try:
        # On récupère tous les pods du namespace 'default' (ou celui que tu utilises)
        pods = v1.list_pod_for_all_namespaces(watch=False)
        
        for pod in pods.items:
            # On vérifie si le pod appartient à une de tes apps
            for app_name in monitored_apps:
                if app_name in pod.metadata.name:
                    results.append({
                        "app": app_name,
                        "pod_name": pod.metadata.name,
                        "status": pod.status.phase, # Running, Pending, Failed...
                        "restarts": pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0,
                        "image": pod.spec.containers[0].image,
                        "health_score": "SECURE" if pod.status.phase == "Running" else "ALERT"
                    })
        return results
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/k3s/logs/{pod_name}")
async def get_pod_logs(pod_name: str):
    """Récupère les 50 dernières lignes de logs pour le dépannage"""
    try:
        # On cherche dans quel namespace est le pod
        pods = v1.list_pod_for_all_namespaces(watch=False)
        namespace = "default"
        for p in pods.items:
            if p.metadata.name == pod_name:
                namespace = p.metadata.namespace
        
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=50)
        return {"pod": pod_name, "logs": logs}
    except Exception as e:
        return {"error": str(e)}    