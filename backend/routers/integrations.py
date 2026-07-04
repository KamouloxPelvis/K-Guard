from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import re
import backend.database
from kubernetes import client, config
from datetime import datetime

router = APIRouter(tags=["Integrations"])

class WebexConfig(BaseModel):
    enabled: bool
    token: str
    room_id: str

def update_fluentbit_config(token, room_id):
    """
    Updates the Kubernetes ConfigMap for Fluent Bit and triggers a rollout restart.
    """
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    
    # 1. Fetch current ConfigMap
    cm = v1.read_namespaced_config_map("fluent-bit-config", "k-guard")
    
    # 2. Update placeholders in .conf
    cm.data["fluent-bit.conf"] = re.sub(
        r"Authorization Bearer [^\n]+", 
        f"Authorization Bearer {token}", 
        cm.data["fluent-bit.conf"]
    )
    
    # 3. Update placeholders in filter.lua
    cm.data["filter.lua"] = cm.data["filter.lua"].replace("ROOM_ID", room_id)
    
    from kubernetes.client import V1ConfigMap

    # Prepare the patch object to update the Fluent Bit ConfigMap.
    # Using V1ConfigMap ensures we adhere to the Kubernetes API schema requirements.
    patch_body = V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata={"name": "fluent-bit-config"},
        data=cm.data  # Apply the updated configuration dictionary
    )

    # Perform a strategic merge patch on the existing ConfigMap.
    # patch_namespaced_config_map is preferred over replace to avoid 
    # resource version conflicts and to ensure atomic updates.
    v1.patch_namespaced_config_map(
        name="fluent-bit-config", 
        namespace="k-guard", 
        body=patch_body
    )

    # 5. Force hot-reload via deployment restart
    patch = {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()}}}}}
    apps_v1.patch_namespaced_daemon_set(
    name="fluent-bit", 
    namespace="k-guard", 
    body={
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()
                    }
                }
            }
        }
    }
)

@router.get("/settings/integrations/webex")
async def get_webex_status():
    try:
        settings = backend.database.get_integration_settings("webex")
        if not settings:
            return {"enabled": False, "configured": False}
        return {
            "enabled": bool(settings['enabled']),
            "configured": bool(settings['token']),
            "room_id": settings['target_id'] or "",
            "token_preview": f"***{settings['token'][-4:]}" if settings['token'] else ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/integrations/webex")
async def update_webex(config: WebexConfig):
    try:
        # 1. Update SQLite database
        conn = backend.database.sqlite3.connect(backend.database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE integrations 
            SET enabled = ?, token = ?, target_id = ?
            WHERE name = 'webex'
        ''', (1 if config.enabled else 0, config.token, config.room_id))
        conn.commit()
        conn.close()

        # 2. Synchronize with Kubernetes
        update_fluentbit_config(config.token, config.room_id)

        return {"status": "success", "message": "Cisco Webex integration synced and pod restarted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")