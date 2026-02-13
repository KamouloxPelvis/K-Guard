from fastapi import APIRouter, Depends, HTTPException, Body
from auth import verify_token
from database import v1, apps_client
from metrics_manager import scale_down_deployment

router = APIRouter(prefix="/api/k3s", tags=["Management"])

@router.delete("/restart/{namespace}/{pod_name}")
async def restart_pod(namespace: str, pod_name: str, user: dict = Depends(verify_token)):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"status": "success", "message": f"Pod {pod_name} supprimé (re-pull en cours)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/remediate/{namespace}/{pod_name}")
async def remediate_pod(namespace: str, pod_name: str, user: dict = Depends(verify_token)):
    """Déclenche une remédiation SRE (Scale Down)"""
    try:
        result = await scale_down_deployment(namespace, pod_name)
        return result
    except Exception as e:
        print(f"❌ Remediate Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/patch-image")
async def patch_deployment_image(
    payload: dict = Body(...), 
    user: dict = Depends(verify_token)
):
    """
    Met à jour l'image d'un déploiement (Remédiation intelligente)
    Format attendu : {"namespace": "...", "deployment": "...", "new_image": "..."}
    """
    namespace = payload.get("namespace")
    deployment_name = payload.get("deployment")
    new_image = payload.get("new_image")

    if not all([namespace, deployment_name, new_image]):
        raise HTTPException(status_code=400, detail="Paramètres manquants (ns, deployment, image)")

    try:
        # 1. On récupère le déploiement actuel pour trouver le conteneur
        deployment = apps_client.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        container_name = deployment.spec.template.spec.containers[0].name

        # 2. Préparation du patch
        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": container_name,
                                "image": new_image
                            }
                        ]
                    }
                }
            }
        }

        # 3. Application du patch sur Kubernetes
        apps_client.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=body
        )

        return {
            "status": "success", 
            "message": f"Mise à jour vers {new_image} lancée pour {deployment_name}"
        }

    except Exception as e:
        print(f"❌ Patch Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Logs du patch en streaming                                                                                                                                                                                            
@router.get("/patch-logs/{namespace}/{deployment_name}")
async def get_patch_events(namespace: str, deployment_name: str, user: dict = Depends(verify_token)):
    """
    Récupère les événements récents liés au déploiement pour simuler un log d'update.
    """
    try:
        # On récupère les événements du namespace filtrés sur le déploiement
        events = v1.list_namespaced_event(namespace)
        relevant_events = [
            f"[{e.last_timestamp}] {e.message}" 
            for e in events.items 
            if deployment_name in e.involved_object.name
        ]
        return {"logs": "\n".join(relevant_events[-15:])} # Les 15 derniers événements
    except Exception as e:
        return {"logs": f"En attente des logs Kubernetes... ({str(e)})"}