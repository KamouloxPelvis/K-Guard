import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.routers.auth import verify_token
from backend.services.wazuh_client import WazuhClientError, wazuh_client

logger = logging.getLogger("K-Guard.Wazuh")

router = APIRouter(
    prefix="/wazuh",
    tags=["Wazuh Endpoint Security"],
    dependencies=[Depends(verify_token)],
)


@router.get("/agents")
async def list_wazuh_agents():
    """
    Returns normalized endpoint inventory and connection summary from Wazuh.
    Wazuh credentials and its JWT remain exclusively inside the K-Guard pod.
    """
    try:
        return await wazuh_client.get_agents()
    except WazuhClientError as error:
        logger.warning("Wazuh endpoint inventory unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wazuh endpoint inventory is temporarily unavailable",
        ) from error