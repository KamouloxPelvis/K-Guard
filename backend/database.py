from kubernetes import client, config

# Initialisation des variables globales
v1 = None
apps_client = None

def init_k8s():
    """Tente de charger la config K8s (Locale ou In-Cluster)"""
    global v1, apps_client
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        apps_client = client.AppsV1Api()
        print("✅ K3s Config loaded from local file")
    except Exception:
        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            apps_client = client.AppsV1Api()
            print("✅ K3s Config loaded from Service Account (In-Cluster)")
        except Exception as e:
            print(f"❌ Failed to load K8s config: {e}")

# On initialise immédiatement à l'import
init_k8s()