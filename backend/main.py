import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend import database
from backend.network_manager import router as network_router
from backend.routers import auth, integrations, k3s, security, wazuh

base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

app = FastAPI(
    title="🛡️ K-Guard API",
    version="1.6.0",
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


BASE_STATIC_DIR = Path("/app/static").resolve()


@app.get("/{rest_of_path:path}", tags=["Frontend"])
async def serve_frontend(rest_of_path: str):
    """
    Serves the Single Page Application while preventing path traversal.
    """
    requested_path = os.path.normpath(rest_of_path)

    if requested_path.startswith("..") or requested_path.startswith("/"):
        return JSONResponse(
            status_code=403,
            content={"error": "Security Violation: Invalid Path"},
        )

    candidate_path = (BASE_STATIC_DIR / requested_path).resolve()

    if not str(candidate_path).startswith(str(BASE_STATIC_DIR)):
        return JSONResponse(
            status_code=403,
            content={"error": "Security Violation: Access Denied"},
        )

    if candidate_path.is_file():
        return FileResponse(path=candidate_path)

    return FileResponse(path=(BASE_STATIC_DIR / "index.html").resolve())


@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware for request tracing and security auditing."""
    logger = logging.getLogger("K-Guard.Middleware")
    logger.info("Incoming %s request to %s", request.method, request.url.path)
    return await call_next(request)