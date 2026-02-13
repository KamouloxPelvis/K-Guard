from fastapi import APIRouter, Depends, HTTPException
from auth import verify_token
from security_manager import run_trivy_scan

router = APIRouter(prefix="/api/security", tags=["Security"])

# Scan de vulnérabilité Trivy
@router.post("/scan")
async def security_scan(payload: dict, user: dict = Depends(verify_token)):
    image_name = payload.get("image")
    if not image_name:
        raise HTTPException(status_code=400, detail="Image manquante")
    return run_trivy_scan(image_name)