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
app = FastAPI(title="K-Guard API")

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
@app.post("/api/token")
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

# --- ROUTES DECOUVERTE ---
# GET STATUS
@app.get("/api/k3s/status")
async def get_cluster_status(user: dict = Depends(verify_token)):
    try:
        # On simule ou on récupère les vraies infos
        return {
            "cluster_version": "v1.28.2+k3s1",
            "vps_os": "Ubuntu 22.04 LTS",
            "uptime": "12 days",
            "status": "Ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET DEPLOYMENTS
# Dans main.py
@app.get("/api/k3s/deployments/all")
async def list_all_deployments():
    try:
        if not apps_client: return []
        
        # On récupère tous les namespaces définis dans l'env
        # S'il n'y a rien, on laisse la liste vide
        env_ns = os.getenv("MONITORED_NAMESPACES", "")
        monitored = env_ns.split(",") if env_ns else []

        deps = apps_client.list_deployment_for_all_namespaces()
        app_list = []
        
        # Namespaces système à ignorer pour rester propre (optionnel)
        system_ns = ["kube-system", "kube-public", "kube-node-lease", "local-path-storage"]

        for dep in deps.items:
            ns = dep.metadata.namespace
            
            # LOGIQUE : 
            # 1. Si l'utilisateur a spécifié des namespaces -> on filtre
            # 2. Sinon -> on affiche tout sauf le système
            if monitored:
                should_add = ns in monitored
            else:
                should_add = ns not in system_ns

            if should_add:
                app_list.append({
                    "id": dep.metadata.uid,
                    "name": dep.metadata.name,
                    "namespace": ns,
                    "image": dep.spec.template.spec.containers[0].image
                })
        return app_list
    except Exception as e:
        print(f"❌ Discovery Error: {e}")
        return []

# --- ROUTES TRIVY --- 
@app.post("/api/security/scan")
async def security_scan(payload: dict, user: dict = Depends(verify_token)):
    image_name = payload.get("image")
    if not image_name:
        raise HTTPException(status_code=400, detail="Image manquante")
    return run_trivy_scan(image_name)

# --- ROUTES K3S MONITORING ---
# GET STATUS
@app.get("/api/k3s/health")
async def get_cluster_health():
    return get_k3s_status()

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

# --- ROUTES GESTION (MCO) ---
@app.delete("/api/k3s/restart/{namespace}/{pod_name}")
async def restart_pod(namespace: str, pod_name: str, user: dict = Depends(verify_token)):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"status": "success", "message": f"Pod {pod_name} supprimé (re-pull en cours)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}