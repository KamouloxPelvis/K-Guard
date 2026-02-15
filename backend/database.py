from kubernetes import client, config
import os

# Initialisation des variables globales
v1 = None
apps_client = None

def init_k8s():
    """Tente de charger la config K8s (Locale ou In-Cluster)"""
    global v1, apps_client
    
    # On évite de ré-initialiser si c'est déjà fait
    if v1 is not None:
        return

    try:
        # 1. Tentative locale (Kubeconfig)
        config.load_kube_config()
        v1 = client.CoreV1Api()
        apps_client = client.AppsV1Api()
        print("✅ K3s Config: Local Kubeconfig loaded")
    except Exception:
        try:
            # 2. Tentative In-Cluster (ServiceAccount dans le Pod)
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            apps_client = client.AppsV1Api()
            print("✅ K3s Config: In-Cluster Service Account loaded")
        except Exception as e:
            print(f"❌ Critical: Failed to load K8s config: {e}")
            v1 = None
            apps_client = None

# Initialisation au chargement du module
init_k8s()