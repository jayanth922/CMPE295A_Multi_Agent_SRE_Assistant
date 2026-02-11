from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend import schemas, crud, models, database
from sre_agent.api.v1.clusters import get_current_user_and_org

# Import the core agent runtime logic
# Note: We need to import this carefully to avoid circular deps if agent_runtime imports this
# Ideally, the background implementation sits in specific module.
# For now, we assume `agent_runtime` is the entrypoint but we need to trigger logic.
# Let's import the background function dynamically or refactor the graph runner.

router = APIRouter(
    prefix="/clusters/{cluster_id}",
    tags=["incidents"],
)

@router.get("/incidents", response_model=List[schemas.IncidentResponse])
async def list_incidents(
    cluster_id: uuid.UUID,
    user: models.User = Depends(get_current_user_and_org),
    db: AsyncSession = Depends(database.get_db)
):
    """List incidents for a cluster."""
    cluster = await crud.get_cluster_by_id(db, cluster_id)
    if not cluster or cluster.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Cluster not found")
        
    return await crud.get_incidents_for_cluster(db, cluster_id)

@router.post("/trigger", response_model=schemas.IncidentResponse)
async def trigger_incident(
    cluster_id: uuid.UUID,
    payload: schemas.IncidentCreate,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_user_and_org),
    db: AsyncSession = Depends(database.get_db)
):
    """Manually trigger the SRE Agent for a cluster."""
    cluster = await crud.get_cluster_by_id(db, cluster_id)
    if not cluster or cluster.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # 1. Create Incident Record
    incident = await crud.create_incident(db, payload, cluster_id)
    
    # 2. Trigger Background Agent
    # We delay the import to avoid top-level circular dependency if any
    try:
        from sre_agent.agent_runtime import run_graph_background_saas
        # We need a new function that handles postgres logging
        background_tasks.add_task(
            run_graph_background_saas, 
            incident_id=incident.id, 
            cluster_id=cluster.id,
            alert_name=payload.title
        )
    except ImportError:
        # Fallback or Log Error if not yet implemented
        pass

    return incident
