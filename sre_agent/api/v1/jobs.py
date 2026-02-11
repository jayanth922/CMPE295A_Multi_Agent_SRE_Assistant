"""Job Queue Router for Agent-SaaS Integration."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend import schemas, crud, models, database
from backend.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Dependency: Get current user (for Dashboard triggering jobs)
async def get_current_user_and_org(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(database.get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await crud.get_user_by_email(db, email=payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Dependency: Get cluster by token (for Agent polling)
async def get_cluster_by_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(database.get_db)
) -> models.Cluster:
    """Extract cluster token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]  # Remove "Bearer "
    cluster = await crud.get_cluster_by_token(db, token)
    if not cluster:
        raise HTTPException(status_code=401, detail="Invalid cluster token")
    return cluster


router = APIRouter(
    prefix="/clusters",
    tags=["jobs"],
)


# ====================================
# Dashboard Endpoints (User-triggered)
# ====================================

@router.post("/{cluster_id}/jobs/trigger", response_model=schemas.JobResponse)
async def trigger_job(
    cluster_id: uuid.UUID,
    job: schemas.JobCreate,
    user: models.User = Depends(get_current_user_and_org),
    db: AsyncSession = Depends(database.get_db)
):
    """Trigger a new job for a cluster (called from Dashboard)."""
    # Verify cluster belongs to user's org
    cluster = await crud.get_cluster_by_id(db, cluster_id)
    if not cluster or cluster.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    new_job = await crud.create_job(db, cluster_id, job)
    return new_job


@router.get("/{cluster_id}/jobs", response_model=list[schemas.JobResponse])
async def list_jobs(
    cluster_id: uuid.UUID,
    user: models.User = Depends(get_current_user_and_org),
    db: AsyncSession = Depends(database.get_db)
):
    """List all jobs for a cluster (called from Dashboard)."""
    cluster = await crud.get_cluster_by_id(db, cluster_id)
    if not cluster or cluster.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return await crud.get_jobs_for_cluster(db, cluster_id)


# ====================================
# Agent Endpoints (Edge Agent polling)
# ====================================

@router.get("/jobs/pending", response_model=Optional[schemas.JobResponse])
async def get_pending_job(
    cluster: models.Cluster = Depends(get_cluster_by_token),
    db: AsyncSession = Depends(database.get_db)
):
    """Get oldest pending job for the calling agent's cluster."""
    job = await crud.get_pending_job_for_cluster(db, cluster.id)
    return job  # Returns None if no pending job


@router.post("/jobs/{job_id}/status", response_model=schemas.JobResponse)
async def update_job_status(
    job_id: uuid.UUID,
    status_update: schemas.JobStatusUpdate,
    cluster: models.Cluster = Depends(get_cluster_by_token),
    db: AsyncSession = Depends(database.get_db)
):
    """Update job status (called by Agent during/after execution)."""
    job = await crud.get_job_by_id(db, job_id)
    if not job or job.cluster_id != cluster.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    updated_job = await crud.update_job_status(db, job_id, status_update)
    return updated_job


@router.post("/jobs/{job_id}/logs")
async def append_job_logs(
    job_id: uuid.UUID,
    logs: str,
    cluster: models.Cluster = Depends(get_cluster_by_token),
    db: AsyncSession = Depends(database.get_db)
):
    """Append log lines to a job (called by Agent for telemetry streaming)."""
    job = await crud.get_job_by_id(db, job_id)
    if not job or job.cluster_id != cluster.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update logs
    status_update = schemas.JobStatusUpdate(status=job.status, logs=logs)
    await crud.update_job_status(db, job_id, status_update)
    return {"status": "ok"}
