import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from kubernetes import client, config

# Managers personnalisés
from k3s_manager import get_k3s_status
from security_manager import run_trivy_scan
from metrics_manager import get_pod_metrics, scale_down_deployment

# Chargement des variables d'environnement
load_dotenv()

# Chargement de la liste des namespaces
MONITORED_NAMESPACES = os.getenv("MONITORED_NAMESPACES", "default").split(",")

# Configuration Sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "une-cle-tres-secrete-par-defaut")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
ADMIN_PSEUDO = os.getenv("ADMIN_PSEUDO")
ADMIN_HASH = os.getenv("ADMIN_PASSWORD_HASH")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

app = FastAPI(
    title="K-Guard API",
    root_path="/k-guard"
)

# --- K8S CONFIG ---
v1 = None
apps_client = None

try:
    config.load_kube_config()
    v1 = client.CoreV1Api()
    apps_client = client.AppsV1Api()
    print("✅ K3s Config loaded from local file")
except Exception as e:
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        apps_client = client.AppsV1Api()
        print("✅ K3s Config loaded from Service Account (In-Cluster)")
    except Exception as e:
        print(f"❌ Failed to load K8s config: {e}")

# --- MIDDLEWARE ---
origins = [
    "http://113.30.191.13:80",
    "http://113.30.191.17:81",
    "http://113.30.191.17",
    "http://localhost:80"
    "http://localhost:81",     
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILS SÉCURITÉ ---
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Erreur signature")

# --- ROUTES AUTH ---
# POST TOKEN
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_PSEUDO or not verify_password(form_data.password, ADMIN_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès refusé : Identifiants incorrects",
        )
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": form_data.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {"status": "K-Guard Live", "mode": "Production"}

# GET STATUS
@app.get("/api/k3s/health")
async def get_cluster_health():
    """Route pour la HealthView"""
    print("DEBUG: Appel Health reçu")
    return get_k3s_status()

# --- ROUTES DECOUVERTE ---
# GET STATUS
@app.get("/api/k3s/status")
async def get_cluster_status(user: dict = Depends(verify_token)):
    try:
        if not v1:
            raise HTTPException(status_code=500, detail="K8s client not initialized")

        # 1. Récupération de la version du cluster
        version_info = client.VersionApi().get_code()
        
        # 2. Récupération des infos du Node (OS, Kernel, IP, Uptime via le premier node du cluster)
        nodes = v1.list_node()
        if not nodes.items:
            return {"status": "Error", "detail": "No nodes found"}
        
        node = nodes.items[0] # On prend le premier master/worker
        node_info = node.status.node_info
        
        # Calcul de l'uptime approximatif depuis la création du node
        creation_time = node.metadata.creation_timestamp
        uptime_delta = datetime.utcnow().replace(tzinfo=None) - creation_time.replace(tzinfo=None)
        uptime_str = f"{uptime_delta.days} days"

        return {
            "cluster_version": version_info.git_version,
            "vps_os": f"{node_info.os_image} ({node_info.kernel_version})",
            "uptime": uptime_str,
            "status": "Ready" if any(c.type == 'Ready' and c.status == 'True' for c in node.status.conditions) else "NotReady"
        }
    except Exception as e:
        print(f"❌ Erreur Status Réel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/k3s/deployments/all")    
async def list_all_deployments():
    """Route de découverte pour la SecurityView (Audit Trivy)"""
    print("🔍 Discovery: Appel reçu sur /api/k3s/deployments/all")
    try:
        if not apps_client: 
            print("❌ Discovery: apps_client n'est pas initialisé")
            return []
        
        # On utilise le manager pour récupérer la liste brute
        from k3s_manager import get_cluster_deployments
        all_deps = get_cluster_deployments()

        system_ns = [
            "kube-system", "kube-public", "kube-node-lease", 
            "local-path-storage", "cert-manager", "ingress-nginx"
        ]
        
        final_list = []
        for dep in all_deps:
            if dep['namespace'] not in system_ns:
                final_list.append({
                    "id": dep.get('id'),
                    "name": dep.get('name'),
                    "namespace": dep.get('namespace'),
                    "image": dep.get('image'),
                    "status": "Active" # Info requise par ton composant SecurityView.vue
                })
        
        print(f"✅ Discovery: {len(final_list)} applications prêtes pour le scan")
        return final_list

    except Exception as e:
        print(f"❌ Discovery Error: {str(e)}")
        return []

# --- ROUTES K3S MONITORING ---

# GET LOGS
@app.get("/api/k3s/logs/{namespace}/{pod_name}")
async def get_logs(namespace: str, pod_name: str):
    global v1
    try:
        if v1 is None: return {"logs": "K8s client not initialized"}
        
        # On ne spécifie pas de container, K8s prendra le premier par défaut
        # C'est beaucoup plus adaptable !
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=100
        )
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"ERROR: {str(e)}"}

# GET METRICS
@app.get("/api/k3s/metrics/{namespace}")
def get_pod_metrics(namespace: str):
    try:
        custom_api = client.CustomObjectsApi()
        # On récupère TOUTES les métriques du namespace sans filtrer le nom ici
        resource = custom_api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="pods"
        )
        
        results = []
        for item in resource.get('items', []):
            pod_name = item['metadata']['name']
            # On prend la première instance de container
            container = item['containers'][0]
            results.append({
                "pod_name": pod_name,
                "cpuUsage": container['usage']['cpu'],    # ex: 250000n
                "memoryUsage": container['usage']['memory'] # ex: 154000Ki
            })
        return results
    except Exception as e:
        print(f"Metrics Error: {e}")
        return []

# --- ROUTES TRIVY --- 
@app.post("/api/security/scan")
async def security_scan(payload: dict, user: dict = Depends(verify_token)):
    image_name = payload.get("image")
    if not image_name:
        raise HTTPException(status_code=400, detail="Image manquante")
    return run_trivy_scan(image_name)

# --- ROUTES GESTION (MCO) ---
@app.delete("/api/k3s/restart/{namespace}/{pod_name}")
async def restart_pod(namespace: str, pod_name: str, user: dict = Depends(verify_token)):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"status": "success", "message": f"Pod {pod_name} supprimé (re-pull en cours)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}