# k3s_manager.py

from kubernetes import client, config
import os
import datetime

SYSTEM_NS = ["kube-system", "kube-public", "kube-node-lease", "local-path-storage", "cert-manager", "ingress-nginx"]

def _get_api_client(api_type="core"):
    """Helper pour garantir que le client K8s est toujours chargé"""
    try:
        # Tente de charger la config si ce n'est pas fait
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
            
        if api_type == "apps":
            return client.AppsV1Api()
        return client.CoreV1Api()
    except Exception as e:
        print(f"❌ K8s Client Error: {e}")
        return None

def get_k3s_status():
    v1 = _get_api_client("core")
    if not v1: return []
    
    pod_results = []
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            ns = pod.metadata.namespace
            if ns not in SYSTEM_NS:
                # On récupère le label 'app' ou le début du nom du pod
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

def get_cluster_deployments(namespace: str = "all"):
    apps_v1 = _get_api_client("apps")
    if not apps_v1: return []
    
    try:
        # On liste les deployments pour le moteur Trivy
        deps = apps_v1.list_deployment_for_all_namespaces()
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