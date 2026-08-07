import os
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.routers.auth import verify_token
from backend.services.wazuh_client import WazuhClientError, wazuh_client
from backend.services.wazuh_indexer_client import (
    WazuhIndexerClientError,
    wazuh_indexer_client,
)

logger = logging.getLogger("K-Guard.Wazuh")

router = APIRouter(
    prefix="/wazuh",
    tags=["Wazuh Endpoint Security"],
    dependencies=[Depends(verify_token)],
)


@router.get("/agents")
async def list_wazuh_agents():
    """Returns normalized endpoint inventory from the Wazuh Manager API."""
    try:
        return await wazuh_client.get_agents()
    except WazuhClientError as error:
        logger.warning("Wazuh endpoint inventory unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wazuh endpoint inventory is temporarily unavailable",
        ) from error


@router.get("/alerts")
async def list_wazuh_alerts(limit: int = Query(default=50, ge=1, le=100)):
    """Returns normalized Wazuh alerts from the Indexer in read-only mode."""
    try:
        return await wazuh_indexer_client.get_alerts(limit=limit)
    except WazuhIndexerClientError as error:
        logger.warning("Wazuh alerts unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wazuh alert stream is temporarily unavailable",
        ) from error


@router.get("/overview")
async def get_wazuh_overview():
    """
    Joins endpoint inventory from Wazuh Manager with alert statistics from
    Wazuh Indexer. Both upstream integrations remain read-only.
    """
    agents_result, alert_summary_result = await asyncio.gather(
        wazuh_client.get_agents(),
        wazuh_indexer_client.get_alert_summary(),
        return_exceptions=True,
    )

    inventory = None
    alerts = {
        "available": False,
        "total": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    if isinstance(agents_result, Exception):
        logger.warning("Wazuh inventory unavailable in overview: %s", agents_result)
    else:
        inventory = agents_result

    if isinstance(alert_summary_result, Exception):
        logger.warning("Wazuh alerts unavailable in overview: %s", alert_summary_result)
    else:
        alerts = {"available": True, **alert_summary_result}

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wazuh endpoint inventory is temporarily unavailable",
        )

    return {
        "connected": True,
        "inventory": inventory,
        "alerts": alerts,
        "posture": {
            "sca_available": False,
            "vulnerabilities_available": False,
            "message": (
                "SCA and vulnerability indexes are not available yet. "
                "K-Guard will display them automatically when Wazuh publishes data."
            ),
        },
    }