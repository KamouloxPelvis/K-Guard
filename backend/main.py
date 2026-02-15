from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

import auth
from routers import k3s, scan, remediation 

load_dotenv()

app = FastAPI(
    title="🛡️ K-Guard API",
    root_path="/k-guard"
)

# CORS Dynamique
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
origins += ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)         
api_router.include_router(k3s.router)          
api_router.include_router(scan.router)
api_router.include_router(remediation.router)  

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "k-guard-backend"}

@app.get("/")
async def root():
    return {"message": "🛡️ K-Guard API is Online"}