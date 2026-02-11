from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend import crud, database

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

@router.post("/heartbeat")
async def heartbeat(
    cluster=Depends(get_cluster_via_token),
    db: AsyncSession = Depends(database.get_db)
):
    """Called by the Edge Agent to ping the platform."""
    await crud.update_cluster_heartbeat(db, cluster.id)
    return {"status": "ok", "ack": True}

@router.post("/telemetry")
async def receive_telemetry(
    payload: dict = Body(...),
    cluster=Depends(get_cluster_via_token),
):
    """
    Called by Edge Agent to send metrics, logs, etc.
    For now we just log it, but in real life we'd push to Prometheus/Loki.
    """
    # NOTE: In Phase 2 we will forward this to the Observability stack
    return {"status": "received"}
