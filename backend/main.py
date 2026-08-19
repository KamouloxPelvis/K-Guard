import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from backend import database
from backend.network_manager import router as network_router
from backend.routers import auth, integrations, k3s, security, wazuh

base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

app = FastAPI(
    title="🛡️ K-Guard API",
    version="1.5.0",
    description="Backend API for K-Guard: Operational Infrastructure Security & Observability Platform",
)

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Triggers database initialization on application startup."""
    database.init_db()


@app.get("/health", tags=["Infra"])
async def liveness_probe():
    """Liveness Probe for Kubernetes/K3s health checks and monitoring."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


app.include_router(auth.router, prefix="/api")
app.include_router(k3s.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(network_router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(wazuh.router, prefix="/api")


@app.get("/api/health", tags=["Status"])
async def api_heartbeat():
    """Application heartbeat to confirm API reachability for the frontend."""
    return {"status": "online", "message": "K-Guard API is reachable"}


class SPAStaticFiles(StaticFiles):
    """
    Static files handler providing SPA fallback to index.html for client-side routing.
    Delegates all path traversal prevention and static file resolution to Starlette.
    """
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if response.status_code == 404:
            response = await super().get_response("index.html", scope)
        return response


BASE_STATIC_DIR = os.path.abspath("/app/static")
if os.path.isdir(BASE_STATIC_DIR):
    app.mount("/", SPAStaticFiles(directory=BASE_STATIC_DIR, html=True), name="spa")


@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware for request tracing and security auditing."""
    logger = logging.getLogger("K-Guard.Middleware")
    logger.info("Incoming %s request to %s", request.method, request.url.path)
    return await call_next(request)