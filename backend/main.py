import os
import bcrypt  # Remplaçant de passlib pour la compatibilité
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from kubernetes import client, config 
from jose import JWTError, jwt
from dotenv import load_dotenv

from k3s_manager import get_k3s_status 

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

def verify_token(token: str = Depends(oauth2_scheme)):
    """Vérifie si le token est valide pour protéger les routes"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

# --- ROUTES AUTH ---
@app.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # On vérifie les identifiants contre le .env
    if form_data.username != ADMIN_PSEUDO or not verify_password(form_data.password, ADMIN_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès refusé : Identifiants incorrects",
        )
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": form_data.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROUTES K3S ---
@app.get("/api/k3s/health")
async def get_cluster_health():
    return get_k3s_status()

@app.get("/api/k3s/logs/{namespace}/{pod_name}")
async def get_pod_logs(namespace: str, pod_name: str, container: str = None, token: str = Depends(verify_token)):
    try:
        params = {"name": pod_name, "namespace": namespace, "tail_lines": 100}
        if container: params["container"] = container
        logs = v1.read_namespaced_pod_log(**params)
        return {"logs": logs}
    except Exception as e:
        return {"error": str(e)}

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