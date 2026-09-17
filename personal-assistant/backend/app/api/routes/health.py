"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Check if the service is healthy."""
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/ready", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> HealthResponse:
    """Check if the service is ready to accept requests."""
    # Add database connectivity check here in production
    return HealthResponse(status="ready", version="0.1.0")
