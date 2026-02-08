from kubernetes import client, config
import os

def get_k3s_status():
    try:
        # En local, on utilise le fichier kubeconfig
        # Sur le VPS, on pourra utiliser config.load_incluster_config()
        config.load_kube_config() 
        v1 = client.CoreV1Api()
        
        # On cible les namespaces ou noms d'apps existant dans le vps
        apps_to_watch = ["blog-devopsnotes", "portfolio-portal"]
        pod_results = []

        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            for app_name in apps_to_watch:
                if app_name in pod.metadata.name:
                    pod_results.append({
                        "name": app_name,
                        "pod_name": pod.metadata.name,
                        "status": "SECURE" if pod.status.phase == "Running" else "ALERT",
                        "ip": pod.status.pod_ip,
                        "type": "k3s Pod"
                    })
        return pod_results
    except Exception as e:
        return [{"name": "Cluster", "status": "ALERT", "path": str(e), "type": "Error"}]