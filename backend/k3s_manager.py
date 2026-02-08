from kubernetes import client, config
import os

def get_k3s_status():   
    try:
        # Configuration de l'accès au cluster
        config.load_kube_config() 
        v1 = client.CoreV1Api()
        
        apps_to_watch = ["blog-devopsnotes", "portfolio-portal"]
        pod_results = []

        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            for app_name in apps_to_watch:
                if app_name in pod.metadata.name:
                    pod_results.append({
                        "name": app_name,
                        "pod_name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": "SECURE" if pod.status.phase == "Running" else "ALERT",
                        "ip": pod.status.pod_ip,
                        "type": "k3s Pod"
                    })
        return pod_results 

    except Exception as e:
        # On aligne bien le except avec le try
        return [{"name": "Cluster", "status": "ALERT", "path": str(e), "type": "Error"}]