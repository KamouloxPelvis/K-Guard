from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import des routeurs (Note le changement ici)
import auth
from routers import k3s, security, remediation 

load_dotenv()

app = FastAPI(
    title="K-Guard API",
    root_path="/k-guard"
)

# --- CORS CONFIG ---
origins = [
    "http://113.30.191.17",
    "http://113.30.191.17:5173",
    "http://113.30.191.17:5173/k-guard",
    "http://k-guard.devopsnotes.org",
    "https://k-guard.devopsnotes.org",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUSION DES ROUTES ---
app.include_router(auth.router)         # Routes /api/token
app.include_router(k3s.router)          # Routes /api/k3s/... (Monitoring)
app.include_router(remediation.router)  # Routes /api/k3s/restart & remediate
app.include_router(security.router)     # Routes /api/security/...

@app.get("/")
async def root():
    return {"status": "K-Guard Live", "mode": "Modular Production"}