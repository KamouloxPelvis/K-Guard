from kubernetes import client
from fastapi import HTTPException

def get_pod_metrics(namespace: str = "default"):
    """Récupère les métriques CPU/RAM brutes du metrics-server"""
    try:
        # On utilise l'API Custom Objects pour accéder aux métriques (metrics.k8s.io)
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
            # k8s renvoie des strings comme "2500000n" (nano) ou "150Mi"
            cpu_raw = item["containers"][0]["usage"]["cpu"]
            mem_raw = item["containers"][0]["usage"]["memory"]
            
            parsed_metrics.append({
                "name": name,
                "cpuUsage": cpu_raw,
                "memoryUsage": mem_raw,
                "status": "active"
            })
        return parsed_metrics
    except Exception as e:
        print(f"Erreur Metrics: {str(e)}")
        return []
        
        parsed_metrics = []
        for item in metrics.get("items", []):
            name = item["metadata"]["name"]
            # Récupération brute
            cpu_raw = item["containers"][0]["usage"]["cpu"] # ex: "5333569n"
            mem_raw = item["containers"][0]["usage"]["memory"] # ex: "137876Ki"

            # --- CONVERSION CPU (%) ---
            # 1 Core = 1,000,000,000n. On calcule le % sur 1 Core.
            cpu_val = int(cpu_raw.replace('n', ''))
            cpu_percent = round((cpu_val / 1000000000) * 100, 2)

            # --- CONVERSION RAM (Go) ---
            # 1 Go = 1,048,576 Ki (1024 * 1024)
            mem_val = int(mem_raw.replace('Ki', ''))
            mem_gb = round(mem_val / 1048576, 3)
            # On estime un % de RAM (ex: sur 2Go de quota pour le pod)
            mem_percent = Math.min(round((mem_gb / 2) * 100, 1), 100) 

            parsed_metrics.append({
                "name": name,
                "cpuUsage": f"{cpu_percent}%",
                "cpuPercent": cpu_percent, # Pour la barre de progression
                "memoryUsage": f"{mem_gb} Go",
                "memPercent": mem_percent # Pour la barre de progression
            })
        return parsed_metrics
    except Exception as e:
        print(f"Erreur Metrics: {str(e)}")
        return []

async def scale_down_deployment(namespace: str, pod_name: str):
    """Logique de remédiation : réduit la charge en diminuant les réplicas"""
    apps_v1 = client.AppsV1Api()
    try:
        # On tente de trouver le déploiement associé au pod (logique simplifiée)
        # On matche par préfixe ; ex: "blog-devopsnotes"
        deployment_name = "-".join(pod_name.split("-")[:-2]) 
        
        body = {"spec": {"replicas": 1}} # On force à 1 pour baisser la charge
        apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        return {"status": "success", "message": f"Scaling down {deployment_name}..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scale down failed: {str(e)}")