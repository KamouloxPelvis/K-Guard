from kubernetes import client, config
import datetime

TARGET_NAMESPACES = os.getenv("MONITORED_NAMESPACES", "default").split(",")

def get_k3s_status():   
    try:
        # ... (init config)
        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            if pod.metadata.namespace in TARGET_NAMESPACES:
                # Extraction d'un nom lisible (ex: portfolio-portal au lieu de portfolio-portal-6f7db...)
                display_name = pod.metadata.labels.get('app', pod.metadata.name.split('-')[0])
                
                pod_results.append({
                    "name": display_name,
                    "pod_name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": "SECURE" if pod.status.phase == "Running" else "ALERT",
                    "ip": pod.status.pod_ip or "N/A",
                    "type": "k3s Pod"
                })
        return pod_results 

    except Exception as e:
        print(f"❌ Erreur Health Status: {e}")
        return [{"name": "Cluster", "status": "ALERT", "path": str(e), "type": "Error"}]

def get_cluster_deployments(namespace: str = "all"):
    """Fonction de découverte utilisée par le moteur de scan"""
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    
    try:
        if namespace == "all":
            deployments = apps_v1.list_deployment_for_all_namespaces()
        else:
            deployments = apps_v1.list_namespaced_deployment(namespace)
            
        app_list = []
        target_namespaces = ["default", "blog-prod", "portfolio-prod"]

        for dep in deployments.items:
            if dep.metadata.namespace in target_namespaces:
                app_list.append({
                    "id": dep.metadata.uid,
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "image": dep.spec.template.spec.containers[0].image
                })
        return app_list
    except Exception as e:
        print(f"Erreur Discovery: {e}")
        return []

def trigger_rollout_restart(namespace: str, deployment_name: str):
    """Force un redémarrage (Rolling Update) pour appliquer un patch de sécurité"""
    try:
        config.load_kube_config()
        apps_v1 = client.AppsV1Api()
        
        # On ajoute une annotation avec l'heure actuelle pour forcer Kubernetes à recréer les pods
        now = datetime.datetime.now().isoformat()
        
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now,
                            "kguard.io/restartedAt": now
                        }
                    }
                }
            }
        }
        
        apps_v1.patch_namespaced_deployment(
            name=deployment_name, 
            namespace=namespace, 
            body=body
        )
        print(f"✅ Rollout lancé pour {deployment_name} dans {namespace}")
        return True
    except Exception as e:
        print(f"❌ Erreur technique lors du restart : {e}")
        return False