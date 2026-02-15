from database import v1, apps_client

# Namespaces à ignorer
SYSTEM_NS = ["kube-system", "kube-public", "kube-node-lease", "local-path-storage", "cert-manager", "ingress-nginx"]

def get_k3s_status():
    """Récupère l'état de santé des Pods pour le Dashboard"""
    if not v1:
        print("⚠️ K8s Client (v1) non initialisé")
        return []
    
    pod_results = []
    try:
        # On scanne tous les namespaces (autorisé par le clusterRole RBAC)
        pods = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pods.items:
            ns = pod.metadata.namespace
            
            if ns not in SYSTEM_NS:
                # 1. Gestion du nom d'affichage vs nom technique unique
                app_label = pod.metadata.labels.get('app')
                display_name = app_label if app_label else pod.metadata.name.split('-')[0]
                
                # 2. Mapping intelligent des statuts pour éviter les fausses alertes
                phase = pod.status.phase
                if phase == "Running":
                    status_label = "SECURE"
                elif phase == "Pending":
                    status_label = "STABILIZING" # Moins alarmant que ALERT
                else:
                    status_label = "ALERT"

                pod_results.append({
                    "name": display_name,         # Pour l'affichage UI
                    "pod_name": pod.metadata.name, # Identifiant unique pour les logs
                    "namespace": ns,
                    "status": status_label,
                    "ip": pod.status.pod_ip or "N/A",
                    "type": "k3s Pod",
                    "creation": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                })
        return pod_results 
    except Exception as e:
        print(f"❌ Erreur Health Status: {e}")
        return []

def get_cluster_deployments():
    """Récupère les déploiements pour l'audit de sécurité (Trivy)"""
    if not apps_client:
        print("⚠️ K8s AppsClient non initialisé")
        return []
        
    try:
        deps = apps_client.list_deployment_for_all_namespaces()
        app_list = []
        for dep in deps.items:
            ns = dep.metadata.namespace
            if ns not in SYSTEM_NS:
                # On récupère l'image du premier conteneur (standard pour nos apps)
                container_image = dep.spec.template.spec.containers[0].image
                
                app_list.append({
                    "id": dep.metadata.uid,
                    "name": dep.metadata.name,
                    "namespace": ns,
                    "image": container_image,
                    "status": "Active" 
                })
        return app_list
    except Exception as e:
        print(f"❌ Discovery Error: {e}")
        return []