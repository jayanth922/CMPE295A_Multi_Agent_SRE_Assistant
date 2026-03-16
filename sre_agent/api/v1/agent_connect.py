import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Body

from backend.rate_limit import rate_limit
from sqlalchemy.ext.asyncio import AsyncSession

from backend import crud, database

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["agent-connect"],
)

async def get_cluster_via_token(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(database.get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    cluster = await crud.get_cluster_by_token(db, token)
    if not cluster:
        raise HTTPException(status_code=403, detail="Invalid Cluster Token")
    return cluster

@router.post("/heartbeat", dependencies=[Depends(rate_limit(30, 60))])
async def heartbeat(
    cluster=Depends(get_cluster_via_token),
    db: AsyncSession = Depends(database.get_db)
):
    """Called by the Edge Agent to ping the platform."""
    await crud.update_cluster_heartbeat(db, cluster.id)
    return {"status": "ok", "ack": True}

@router.post("/telemetry", dependencies=[Depends(rate_limit(60, 60))])
async def receive_telemetry(
    payload: dict = Body(...),
    cluster=Depends(get_cluster_via_token),
):
    """
    Receive telemetry from Edge Agent (metrics, logs, events).

    Forwards data to configured observability backends:
    - Prometheus (via remote-write or push gateway)
    - Loki (via push API)
    Falls back to logging when backends are not configured.
    """
    telemetry_type = payload.get("type", "unknown")
    data = payload.get("data", {})

    # Forward metrics to Prometheus Pushgateway if configured
    prometheus_push_url = os.getenv("PROMETHEUS_PUSHGATEWAY_URL", "")
    if telemetry_type == "metrics" and prometheus_push_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{prometheus_push_url}/metrics/job/sre-agent/cluster/{cluster.id}",
                    content=data.get("payload", ""),
                    headers={"Content-Type": "text/plain"},
                )
                logger.info(f"Forwarded metrics to Pushgateway for cluster {cluster.id}")
        except Exception as e:
            logger.warning(f"Failed to forward metrics to Pushgateway: {e}")

    # Forward logs to Loki if configured
    loki_push_url = os.getenv("LOKI_PUSH_URL", "")
    if telemetry_type == "logs" and loki_push_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{loki_push_url}/loki/api/v1/push",
                    json=data,
                    headers={"Content-Type": "application/json"},
                )
                logger.info(f"Forwarded logs to Loki for cluster {cluster.id}")
        except Exception as e:
            logger.warning(f"Failed to forward logs to Loki: {e}")

    # Always log the telemetry receipt for audit purposes
    logger.info(
        f"Telemetry received: type={telemetry_type} cluster={cluster.id} "
        f"keys={list(data.keys()) if isinstance(data, dict) else 'raw'}"
    )

    return {"status": "received", "type": telemetry_type}
