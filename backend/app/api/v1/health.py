from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import check_database_connection

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database_connected: bool


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/live", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """System health check endpoint verifying application execution status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0"
    )


@router.get("/readiness", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
@router.get("/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check():
    """System readiness check endpoint verifying database connectivity."""
    db_connected = await check_database_connection()
    return ReadinessResponse(
        status="ready" if db_connected else "degraded",
        database_connected=db_connected
    )
