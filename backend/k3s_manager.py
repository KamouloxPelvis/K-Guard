from backend.database import v1, apps_client
import os
import shutil
import logging

logger = logging.getLogger("k-guard-backend")

SYSTEM_NS = [
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "local-path-storage",
    "cert-manager",
    "ingress-nginx",
]

def get_k3s_status():
    """Retrieves Pod health status for the Dashboard visualization."""
    if not v1:
        logger.warning("K8s Client (v1) not initialized")
        return []

    pod_results = []
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            ns = pod.metadata.namespace

            if ns in SYSTEM_NS:
                continue

            labels = pod.metadata.labels or {}
            annotations = pod.metadata.annotations or {}

            app_label = (
                labels.get("app.kubernetes.io/name")
                or labels.get("app")
                or labels.get("k8s-app")
                or annotations.get("kubernetes.io/created-by")
            )

            if app_label:
                display_name = str(app_label)
            else:
                parts = pod.metadata.name.split("-")
                if len(parts) > 2 and len(parts[-1]) == 5:
                    display_name = "-".join(parts[:-2])
                elif len(parts) > 1 and parts[-1].isdigit():
                    display_name = "-".join(parts[:-1])
                else:
                    display_name = "-".join(parts[:-1]) if len(parts) > 1 else pod.metadata.name

            display_name = display_name.replace("-", " ").title()

            phase = pod.status.phase
            if phase == "Running":
                status_label = "SECURE"
            elif phase == "Pending":
                status_label = "STABILIZING"
            else:
                status_label = "ALERT"

            pod_results.append({
                "name": display_name,
                "pod_name": pod.metadata.name,
                "namespace": ns,
                "status": status_label,
                "ip": pod.status.pod_ip or "N/A",
                "type": "k3s Pod",
                "creation": pod.metadata.creation_timestamp.isoformat()
                if pod.metadata.creation_timestamp else None
            })

        return pod_results

    except Exception:
        logger.exception("Health status collection failed")
        return []

def get_pod_logs(namespace: str, pod_name: str):
    """Retrieves the last 50 lines of logs for a specific pod."""
    if not v1:
        return "⚠️ K8s Client not initialized."

    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        if not pod.spec.containers:
            return "CRITICAL ERROR: No containers found."

        primary_container = pod.spec.containers[0].name
        log_data = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=primary_container,
            tail_lines=50
        )

        if isinstance(log_data, bytes):
            return log_data.decode("utf-8", errors="replace")
        return str(log_data)

    except Exception as e:
        logger.error(f"Log retrieval failed for pod {pod_name} in namespace {namespace}: {str(e)}")
        return f"CRITICAL ERROR: Unable to retrieve logs for {pod_name}."

def get_cluster_deployments():
    """Retrieves deployments for security auditing."""
    if not apps_client:
        logger.warning("K8s AppsClient not initialized")
        return []

    try:
        deps = apps_client.list_deployment_for_all_namespaces()
        app_list = []

        for dep in deps.items:
            ns = dep.metadata.namespace
            if ns in SYSTEM_NS:
                continue

            containers = dep.spec.template.spec.containers or []
            if not containers:
                continue

            app_list.append({
                "id": dep.metadata.uid,
                "name": dep.metadata.name,
                "namespace": ns,
                "image": containers[0].image,
                "status": "Active"
            })

        return app_list

    except Exception:
        logger.exception("Deployment discovery failed")
        return []

def get_storage_stats():
    """Checks disk space on critical mount points (PVC / Root)."""
    paths = ["/", "/app"]
    stats = {}

    for path in paths:
        if os.path.exists(path):
            total, used, free = shutil.disk_usage(path)
            stats[path] = {
                "total_gb": round(total / (2**30), 2),
                "used_gb": round(used / (2**30), 2),
                "free_gb": round(free / (2**30), 2),
                "percent": round((used / total) * 100, 1)
            }

    return stats

def get_node_capacity():
    """Dynamically retrieves K3s node capacity for precise metrics UI."""
    if not v1:
        return {"cpu_cores": 2, "memory_total_ki": 8388608}

    try:
        nodes = v1.list_node().items
        if nodes:
            allocatable = nodes[0].status.allocatable or {}
            cpu = allocatable.get("cpu", "2")
            mem = allocatable.get("memory", "8388608Ki")

            cpu_cores = int(cpu) if not str(cpu).endswith("m") else int(str(cpu).replace("m", "")) / 1000
            mem_ki = int(str(mem).replace("Ki", ""))

            return {"cpu_cores": cpu_cores, "memory_total_ki": mem_ki}

    except Exception:
        logger.exception("Node capacity retrieval failed")

    return {"cpu_cores": 2, "memory_total_ki": 8388608}