import os
import logging
import asyncio
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from kubernetes import client, config
from backend.sentinel_audit import audit_cluster_security
from backend.sentinel_plan import build_hardening_plan
from backend.routers.auth import verify_token

router = APIRouter(tags=["Network Sentinel"])

# --- CONFIGURATION ---
# Note: In a production environment, avoid executing ansible-playbook from within a pod.
# Consider using an Ansible Operator or a dedicated CI/CD trigger instead.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANSIBLE_PATH = Path(
    os.getenv(
        "SENTINEL_ANSIBLE_PATH",
        str(PROJECT_ROOT / "infra/ansible/playbooks/harden_policies.yml"),
    )
)

REMOVE_ANSIBLE_PATH = Path(
    os.getenv(
        "SENTINEL_REMOVE_ANSIBLE_PATH",
        str(
            PROJECT_ROOT
            / "infra/ansible/playbooks/remove_hardened_policies.yml"
        ),
    )
)

def load_k8s_config():
    """Initializes in-cluster Kubernetes configuration."""
    try:
        config.load_incluster_config()
        return True
    except Exception as e:
        logging.error("Failed to load In-Cluster K8s config: %s", str(e))
        return False
@router.get("/sentinel/hardening/plan")
async def get_hardening_plan():
    """
    Read-only hardening plan.
    This endpoint never changes Kubernetes resources.
    """
    try:
        return await asyncio.to_thread(build_hardening_plan)
    except Exception as error:
        logging.error("Error building Sentinel hardening plan: %s", error)
        return JSONResponse(
            status_code=503,
            content={
                "read_only": True,
                "error": "Sentinel hardening plan unavailable",
            },
        )


@router.get("/sentinel/status")
async def get_network_policy_status():
    """
    Read-only Kubernetes security posture assessment.
    This endpoint never mutates cluster state.
    """
    try:
        return await asyncio.to_thread(audit_cluster_security)
    except Exception as error:
        logging.error("Error running Sentinel security audit: %s", error)
        return JSONResponse(
            status_code=503,
            content={
                "deployed": False,
                "securityScore": 0,
                "security_score": None,
                "coverage": 0,
                "confidence": 0,
                "error": "Sentinel security audit unavailable",
            },
        )


async def _run_sentinel_playbook(playbook_path: Path) -> dict[str, Any]:
    if not playbook_path.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Sentinel playbook not found: {playbook_path}",
        )

    ansible_binary = shutil.which("ansible-playbook")

    if not ansible_binary:
        raise HTTPException(
            status_code=503,
            detail="ansible-playbook is not available",
        )

    command = [
        ansible_binary,
        "-i",
        "localhost,",
        "-c",
        "local",
        str(playbook_path),
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=180,
        )
    except asyncio.TimeoutError as error:
        process.kill()
        await process.wait()
        raise HTTPException(
            status_code=504,
            detail="Sentinel playbook execution timed out",
        ) from error

    result = {
        "return_code": process.returncode,
        "changed": process.returncode == 0,
        "stdout": stdout.decode("utf-8", errors="replace")[-12000:],
        "stderr": stderr.decode("utf-8", errors="replace")[-12000:],
        "playbook": str(playbook_path),
    }

    if process.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=result,
        )

    return result


@router.post("/sentinel/activate")
async def activate_sentinel(user: dict = Depends(verify_token)):
    result = await _run_sentinel_playbook(ANSIBLE_PATH)

    audit = await asyncio.to_thread(audit_cluster_security)

    return {
        "action": "activate",
        "result": result,
        "audit": audit,
    }


@router.post("/sentinel/deactivate")
async def deactivate_sentinel(user: dict = Depends(verify_token)):
    result = await _run_sentinel_playbook(REMOVE_ANSIBLE_PATH)

    audit = await asyncio.to_thread(audit_cluster_security)

    return {
        "action": "deactivate",
        "result": result,
        "audit": audit,
    }


async def fetch_namespace_data(namespace: str, v1: client.CoreV1Api, net_v1: client.NetworkingV1Api) -> Dict[str, Any]:
    """
    Fetches pods and network policies for a single namespace concurrently.
    """
    try:
        pods = await asyncio.to_thread(v1.list_namespaced_pod, namespace)
        policies = await asyncio.to_thread(net_v1.list_namespaced_network_policy, namespace)
        
        namespace_nodes = []
        for pod in pods.items:
            labels = pod.metadata.labels or {}
            role = labels.get("app", labels.get("k8s-app", "generic"))
            
            namespace_nodes.append({
                "id": pod.metadata.name,
                "name": pod.metadata.name,
                "namespace": namespace,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip or "0.0.0.0",
                "role": role,
                "is_hardened": len(policies.items) > 0
            })
        return {"nodes": namespace_nodes}
    except Exception as e:
        logging.error("Error fetching data for namespace %s: %s", namespace, e)
        return {"nodes": []}

@router.get("/sentinel/map")
async def get_network_map():
    """
    Generates a dynamic map of network flows using parallelized discovery.
    """
    v1 = client.CoreV1Api()
    net_v1 = client.NetworkingV1Api()
    
    try:
        all_ns = await asyncio.to_thread(v1.list_namespace)
        target_ns = [
            n.metadata.name for n in all_ns.items 
            if not n.metadata.name.startswith(("kube-", "local-path-", "node-lease", "ingress-nginx"))
        ]

        results = await asyncio.gather(*[fetch_namespace_data(ns, v1, net_v1) for ns in target_ns])
        nodes = [node for res in results for node in res["nodes"]]
        
        # Build edges representing flow discovery
        edges = []
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                if node_a["namespace"] == node_b["namespace"]:
                    edges.append({
                        "source": node_a["id"],
                        "target": node_b["id"],
                        "label": "Intra-NS Flow"
                    })
                    
        return {"nodes": nodes, "edges": edges, "namespaces": target_ns}
    except Exception as e:
        logging.error("CRITICAL: Network Map failed due to: %s", str(e), exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"error": "SRE Discovery failed", "message": "An internal error occurred while processing the network map."}
        )