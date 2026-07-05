import re
import base64
import backend.database
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from kubernetes import client, config
from datetime import datetime

router = APIRouter(tags=["Integrations"])

class WebexConfig(BaseModel):
    enabled: bool
    token: str
    room_id: str

def update_fluentbit_config(token: str, room_id: str):
    """
    Synchronize the Fluent Bit ConfigMap with UI settings.
    Ensures consistency by dynamically updating the Lua filter configuration.
    """
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # 1. Update the Secret (base64 encoding required by K8s)
    secret_data = {"token": base64.b64encode(token.encode()).decode()}
    v1.patch_namespaced_secret(
        name="webex-secret",
        namespace="k-guard",
        body={"data": secret_data}
    )

    # 2. Update the ConfigMap (the room_id)
    cm = v1.read_namespaced_config_map("fluent-bit-config", "k-guard")
    cm.data["filter.lua"] = re.sub(
        r'new_record\["roomId"\] = "[^"]+"',
        f'new_record["roomId"] = "{room_id}"',
        cm.data["filter.lua"]
    )
    
    # 3. Patch the ConfigMap in the cluster
    v1.patch_namespaced_config_map(
        name="fluent-bit-config", 
        namespace="k-guard", 
        body={"data": cm.data}
    )

    # 4. Trigger a rolling restart of the DaemonSet to apply new configuration
    # The annotation forces K8s to redeploy the pods with updated ConfigMap data
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

@router.post("/settings/integrations/webex")
async def update_webex(config: WebexConfig):
    try:
        # A. Persist settings into the SQLite database
        conn = backend.database.sqlite3.connect(backend.database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE integrations 
            SET enabled = ?, token = ?, target_id = ?
            WHERE name = 'webex'
        ''', (1 if config.enabled else 0, config.token, config.room_id))
        conn.commit()
        conn.close()

        # B. Sync changes with the Kubernetes infrastructure
        update_fluentbit_config(config.token, config.room_id)

        return {"status": "success", "message": "Cisco Webex integration synced and infrastructure updated"}
    except Exception as e:
        # Log error for maintenance tracking
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")