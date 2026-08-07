from fastapi import APIRouter, Depends, HTTPException
from .auth import verify_token
import httpx
import os
import logging

router = APIRouter(prefix="/security", tags=["Runtime Security"])
logger = logging.getLogger("k-guard-backend")

ELASTICSEARCH_URL = os.getenv(
    "ELASTICSEARCH_URL",
    "http://elasticsearch-es-http.k-guard.svc.cluster.local:9200"
)
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")

@router.get("/alerts")
async def get_runtime_alerts(user: dict = Depends(verify_token)):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ELASTICSEARCH_URL}/falco-*/_search",
                auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD) if ELASTICSEARCH_PASSWORD else None,
                json={
                    "size": 50,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "_source": True,
                    "query": {"match_all": {}}
                }
            )
            response.raise_for_status()
            data = response.json()

            hits = ((data or {}).get("hits") or {}).get("hits") or []
            safe_hits = [hit for hit in hits if isinstance(hit, dict)]

            return safe_hits

    except httpx.HTTPStatusError as e:
        logger.exception("Security alerts Elasticsearch HTTP error")
        raise HTTPException(
            status_code=500,
            detail=f"Elasticsearch HTTP error: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Security alerts route failed")
        raise HTTPException(
            status_code=500,
            detail="Security stack unreachable"
        )