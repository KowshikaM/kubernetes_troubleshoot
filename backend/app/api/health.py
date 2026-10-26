"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(status="healthy", service=get_settings().APP_NAME)
