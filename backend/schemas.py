import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

from backend.models import UserRole, ClusterStatus, IncidentSeverity, IncidentStatus

# ----------------------------------------------------------------------
# Auth Schemas
# ----------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

# ----------------------------------------------------------------------
# User Schemas
# ----------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    org_name: str  # Create a new organization with the user

class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    org_id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# Organization Schemas
# ----------------------------------------------------------------------

class OrgCreate(BaseModel):
    name: str

class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: str

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# Cluster Schemas
# ----------------------------------------------------------------------

class ClusterCreate(BaseModel):
    name: str

class ClusterResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: ClusterStatus
    last_heartbeat: Optional[datetime]

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# Incident Schemas
# ----------------------------------------------------------------------

class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM

class IncidentResponse(BaseModel):
    id: uuid.UUID
    cluster_id: uuid.UUID
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity
    status: IncidentStatus
    summary: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# Job Schemas
# ----------------------------------------------------------------------

from backend.models import JobStatus, JobType

class JobCreate(BaseModel):
    job_type: JobType = JobType.INVESTIGATION
    payload: Optional[str] = None  # JSON string

class JobStatusUpdate(BaseModel):
    status: JobStatus
    result: Optional[str] = None  # JSON string
    logs: Optional[str] = None

class JobResponse(BaseModel):
    id: uuid.UUID
    cluster_id: uuid.UUID
    job_type: JobType
    status: JobStatus
    payload: Optional[str]
    result: Optional[str]
    logs: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
