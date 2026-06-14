"""FastAPI entry point for the AegisFlow Multi-Domain simulation API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Include package folder in import search paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from apps.api.routes import router
from apps.api.config import settings

app = FastAPI(
    title="AegisFlow Orchestration API",
    description="Multi-Agent Operational Decision Simulation Platform Backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core session router
app.include_router(router, prefix="/session")

@app.get("/health")
async def health_check():
    """Service status readiness endpoint."""
    return {
        "status": "healthy",
        "environment": settings.env_name,
        "gemini_api_key_configured": settings.gemini_api_key is not None
    }

@app.get("/")
async def root():
    """Root redirect message."""
    return {"message": "AegisFlow Operational Simulation API is active."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
