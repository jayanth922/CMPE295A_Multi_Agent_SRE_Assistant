from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import engine
from backend.routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB is ready (alembic should handle schema)
    # We could trigger migration here, but better to do it via CI/CD or separate command
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="SRE SaaS Platform API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS (Allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "sre-saas-platform"}
