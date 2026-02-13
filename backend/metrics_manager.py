from fastapi import HTTPException
from database import v1  # On utilise v1 pour l'accès API si besoin
from kubernetes import client

def get_pod_metrics(namespace: str = "default"):
    try:
        # On peut garder l'initialisation locale ici car CustomObjectsApi 
        # est moins souvent utilisé, mais il utilise la config déjà chargée
        custom_api = client.CustomObjectsApi()
        metrics = custom_api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="pods"
        )
        
        parsed_metrics = []
        for item in metrics.get("items", []):
            name = item["metadata"]["name"]
            cpu_raw = item["containers"][0]["usage"]["cpu"]
            mem_raw = item["containers"][0]["usage"]["memory"]
            
            parsed_metrics.append({
                "pod_name": name,
                "cpuUsage": cpu_raw,
                "memoryUsage": mem_raw
            })
        return parsed_metrics
    except Exception as e:
        print(f"❌ Erreur Metrics: {str(e)}")
        return []

async def scale_down_deployment(namespace: str, pod_name: str):
    # On utilise l'apps_client qu'on va importer de database
    from database import apps_client 
    try:
        # Logique de matching du nom de deployment
        deployment_name = "-".join(pod_name.split("-")[:-2]) 
        
        body = {"spec": {"replicas": 1}}
        apps_client.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        return {"status": "success", "message": f"Scaling down {deployment_name}..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scale down failed: {str(e)}")