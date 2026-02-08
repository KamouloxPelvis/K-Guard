import os
import bcrypt

from security_manager import run_trivy_scan
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from kubernetes import client, config 
from jose import JWTError, jwt
from dotenv import load_dotenv

from k3s_manager import get_k3s_status 
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Chargement des variables d'environnement
load_dotenv()

# Configuration Sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "une-cle-tres-secrete-par-defaut")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ADMIN_PSEUDO = os.getenv("ADMIN_PSEUDO")
ADMIN_HASH = os.getenv("ADMIN_PASSWORD_HASH")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

app = FastAPI(title="K-Guard API")

# --- K8S CONFIG ---
try:
    config.load_kube_config()
except:
    config.load_incluster_config()
v1 = client.CoreV1Api()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILS SÉCURITÉ ---
def verify_password(plain_password, hashed_password):
    """Vérifie le mot de passe sans passlib pour éviter les bugs Python 3.12"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        # Affiche le début du token reçu pour comparer avec le front
        print(f"DEBUG BACKEND - Reçu: {token[:10]}...") 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("ERREUR: Le token a expiré !")
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.JWTError as e:
        print(f"ERREUR JWT: {str(e)}") # C'est CA qu'on veut voir dans ta console Python
        raise HTTPException(status_code=401, detail=f"Erreur signature: {str(e)}")
    except Exception as e:
        print(f"ERREUR INCONNUE: {str(e)}")
        raise HTTPException(status_code=401, detail="Erreur validation")

# --- ROUTES AUTH ---
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

# --- ROUTES TRIVY --- 
@app.post("/api/security/scan")
async def security_scan(payload: dict, user: dict = Depends(verify_token)):
    # Ici, 'user' contient maintenant ton payload {'sub': 'Kamal', 'exp': ...}
    image_name = payload.get("image") 
    
    if not image_name:
        raise HTTPException(status_code=400, detail="La clé 'image' est manquante dans le payload")
        
    return run_trivy_scan(image_name)

# --- ROUTES K3S ---
@app.get("/api/k3s/health")
async def get_cluster_health():
    return get_k3s_status()

@app.get("/api/k3s/logs/{namespace}/{pod_name}")
async def get_logs(namespace: str, pod_name: str):
    try:
        # On définit quel conteneur on veut inspecter par défaut
        # Pour le blog, c'est "blog-backend"
        container_target = "blog-backend" if "blog" in pod_name else None
        
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_target, # On précise le conteneur ici !
            tail_lines=100
        )
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"ERROR: Unable to fetch logs for {pod_name}. {str(e)}"}

@app.delete("/api/k3s/restart/{namespace}/{pod_name}")
async def restart_pod(namespace: str, pod_name: str, token: str = Depends(verify_token)):
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return {"status": "success", "message": f"Pod {pod_name} is restarting..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"status": "K-Guard Live", "mode": "Production"}