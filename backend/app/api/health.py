from fastapi import APIRouter, Depends

from backend.app.config import Settings, get_settings
from backend.app.schemas.health_schema import HealthResponse
from backend.app.services.health_service import get_health_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return get_health_status(settings)