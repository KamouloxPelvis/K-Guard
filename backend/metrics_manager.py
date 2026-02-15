from fastapi import HTTPException
from database import v1, apps_client
from kubernetes import client

def parse_cpu(cpu_raw):
    """Convertit les nanocores (n) ou millicores (m) en millicores (entier)"""
    if cpu_raw.endswith('n'):
        return int(cpu_raw.replace('n', '')) // 1000000
    if cpu_raw.endswith('m'):
        return int(cpu_raw.replace('m', ''))
    return int(cpu_raw)

def parse_memory(mem_raw):
    """Convertit Ki, Mi, Gi en MegaBytes (MiB)"""
    if mem_raw.endswith('Ki'):
        return int(mem_raw.replace('Ki', '')) // 1024
    if mem_raw.endswith('Mi'):
        return int(mem_raw.replace('Mi', ''))
    if mem_raw.endswith('Gi'):
        return int(mem_raw.replace('Gi', '')) * 1024
    return int(mem_raw) // 1024

def get_pod_metrics(namespace: str = "default"):
    """Récupère les métriques CPU/RAM réelles via metrics.k8s.io"""
    try:
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
            # On prend la conso du premier conteneur
            usage = item["containers"][0]["usage"]
            
            parsed_metrics.append({
                "pod_name": name,
                "cpuUsage": parse_cpu(usage["cpu"]),
                "memoryUsage": parse_memory(usage["memory"])
            })
        return parsed_metrics
    except Exception as e:
        print(f"❌ Erreur Metrics (Le Metrics-Server est-il installé ?): {str(e)}")
        return []

async def scale_down_deployment(namespace: str, pod_name: str):
    """Remédiation : Réduit le nombre de réplicas à 1 (ou 0 pour stopper)"""
    try:
        # Essayer de trouver le déploiement parent via les owner_references
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        if not pod.metadata.owner_references:
            raise Exception("Pod sans parent (ReplicaSet/Deployment)")
            
        # On remonte du Pod -> ReplicaSet -> Deployment
        rs_name = pod.metadata.owner_references[0].name
        deployment_name = "-".join(rs_name.split("-")[:-1]) # Plus robuste
        
        body = {"spec": {"replicas": 1}}
        apps_client.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        return {"status": "success", "message": f"Remédiation lancée : {deployment_name} stabilisé à 1 replica."}
    except Exception as e:
        print(f"❌ Scale Down Fail: {e}")
        raise HTTPException(status_code=500, detail=f"Échec de la remédiation : {str(e)}")