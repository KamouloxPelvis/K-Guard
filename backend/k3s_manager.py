from database import v1, apps_client

SYSTEM_NS = ["kube-system", "kube-public", "kube-node-lease", "local-path-storage", "cert-manager", "ingress-nginx"]

def get_k3s_status():
    if not v1: return []
    
    pod_results = []
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            ns = pod.metadata.namespace
            if ns not in SYSTEM_NS:
                display_name = pod.metadata.labels.get('app', pod.metadata.name.split('-')[0])
                pod_results.append({
                    "name": display_name,
                    "pod_name": pod.metadata.name,
                    "namespace": ns,
                    "status": "SECURE" if pod.status.phase == "Running" else "ALERT",
                    "ip": pod.status.pod_ip or "N/A",
                    "type": "k3s Pod"
                })
        return pod_results 
    except Exception as e:
        print(f"❌ Erreur Health Status: {e}")
        return []

def get_cluster_deployments():
    if not apps_client: return []
    try:
        deps = apps_client.list_deployment_for_all_namespaces()
        app_list = []
        for dep in deps.items:
            ns = dep.metadata.namespace
            if ns not in SYSTEM_NS:
                app_list.append({
                    "id": dep.metadata.uid,
                    "name": dep.metadata.name,
                    "namespace": ns,
                    "image": dep.spec.template.spec.containers[0].image,
                    "status": "Active" 
                })
        return app_list
    except Exception as e:
        print(f"❌ Discovery Error: {e}")
        return []