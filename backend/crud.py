from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend import models, schemas, auth
import uuid

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def create_org(db: AsyncSession, org: schemas.OrgCreate):
    # Generate API Key
    api_key = f"org_{uuid.uuid4().hex}"
    db_org = models.Organization(name=org.name, api_key=api_key)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    # Check if org exists or create new? 
    # For now, simplistic flow: Register = New Org + New Admin User
    
    # 1. Create Org
    org_data = schemas.OrgCreate(name=user.org_name)
    db_org = await create_org(db, org_data)

    # 2. Hash password
    hashed_password = auth.get_password_hash(user.password)
    
    # 3. Create User linked to Org
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=models.UserRole.ADMIN,
        org_id=db_org.id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_clusters_for_org(db: AsyncSession, org_id: uuid.UUID):
    result = await db.execute(select(models.Cluster).filter(models.Cluster.org_id == org_id))
    return result.scalars().all()

async def create_cluster(db: AsyncSession, cluster: schemas.ClusterCreate, org_id: uuid.UUID):
    # Generate Cluster Token
    cluster_token = f"cl_{uuid.uuid4().hex}"
    db_cluster = models.Cluster(
        name=cluster.name,
        org_id=org_id,
        token=cluster_token,
        status=models.ClusterStatus.OFFLINE
    )
    db.add(db_cluster)
    await db.commit()
    await db.refresh(db_cluster)
    return db_cluster, cluster_token

async def get_cluster_by_token(db: AsyncSession, token: str):
    result = await db.execute(select(models.Cluster).filter(models.Cluster.token == token))
    return result.scalars().first()

async def get_cluster_by_id(db: AsyncSession, cluster_id: uuid.UUID):
    result = await db.execute(select(models.Cluster).filter(models.Cluster.id == cluster_id))
    return result.scalars().first()

async def update_cluster_heartbeat(db: AsyncSession, cluster_id: uuid.UUID):
    stmt = (
        models.Cluster.__table__
        .update()
        .where(models.Cluster.id == cluster_id)
        .values(
            last_heartbeat=datetime.utcnow(),
            status=models.ClusterStatus.ONLINE
        )
    )
    await db.execute(stmt)
    await db.commit()

async def create_incident(db: AsyncSession, incident: schemas.IncidentCreate, cluster_id: uuid.UUID):
    db_incident = models.Incident(
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        cluster_id=cluster_id
    )
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    return db_incident

async def get_incidents_for_cluster(db: AsyncSession, cluster_id: uuid.UUID):
    result = await db.execute(select(models.Incident).filter(models.Incident.cluster_id == cluster_id).order_by(models.Incident.created_at.desc()))
    return result.scalars().all()

async def delete_cluster(db: AsyncSession, cluster_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    result = await db.execute(select(models.Cluster).filter(models.Cluster.id == cluster_id, models.Cluster.org_id == org_id))
    cluster = result.scalars().first()
    if cluster:
        await db.delete(cluster)
        await db.commit()
        return True
    return False

# ----------------------------------------------------------------------
# Job CRUD
# ----------------------------------------------------------------------

async def create_job(db: AsyncSession, cluster_id: uuid.UUID, job: schemas.JobCreate) -> models.Job:
    db_job = models.Job(
        cluster_id=cluster_id,
        job_type=job.job_type,
        payload=job.payload,
        status=models.JobStatus.PENDING
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

async def get_pending_job_for_cluster(db: AsyncSession, cluster_id: uuid.UUID) -> models.Job | None:
    result = await db.execute(
        select(models.Job)
        .filter(models.Job.cluster_id == cluster_id, models.Job.status == models.JobStatus.PENDING)
        .order_by(models.Job.created_at.asc())
        .limit(1)
    )
    return result.scalars().first()

async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> models.Job | None:
    result = await db.execute(select(models.Job).filter(models.Job.id == job_id))
    return result.scalars().first()

async def update_job_status(db: AsyncSession, job_id: uuid.UUID, status_update: schemas.JobStatusUpdate) -> models.Job | None:
    job = await get_job_by_id(db, job_id)
    if not job:
        return None
    
    job.status = status_update.status
    if status_update.result:
        job.result = status_update.result
    if status_update.logs:
        # Append logs if existing
        job.logs = (job.logs or "") + status_update.logs
    
    if status_update.status == models.JobStatus.RUNNING and not job.started_at:
        job.started_at = datetime.utcnow()
    elif status_update.status in (models.JobStatus.COMPLETED, models.JobStatus.FAILED):
        job.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    return job

    result = await db.execute(
        select(models.Job)
        .filter(models.Job.cluster_id == cluster_id)
        .order_by(models.Job.created_at.desc())
    )
    return result.scalars().all()


async def create_audit_event(
    db: AsyncSession, 
    cluster_id: uuid.UUID, 
    action_type: str, 
    resource_target: str, 
    outcome: str, 
    actor_type: str = "AGENT",
    actor_id: str = "sre-agent",
    details: str = None
):
    """Log an immutable audit event."""
    audit_event = models.AuditEvent(
        cluster_id=cluster_id,
        action_type=action_type,
        resource_target=resource_target,
        outcome=outcome,
        actor_type=actor_type,
        actor_id=actor_id,
        details=details
    )
    db.add(audit_event)
    await db.commit()
    await db.refresh(audit_event)
    return audit_event

async def get_audit_events(db: AsyncSession, cluster_id: uuid.UUID, limit: int = 50):
    """Retrieve audit trail for a cluster."""
    result = await db.execute(
        select(models.AuditEvent)
        .filter(models.AuditEvent.cluster_id == cluster_id)
        .order_by(models.AuditEvent.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
