from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.database_schema import DatabaseHealthResponse
from backend.app.schemas.health_schema import HealthResponse
from backend.app.services.database_service import get_database_health
from backend.app.services.health_service import get_health_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    return get_health_status(settings)


@router.get("/health/database", response_model=DatabaseHealthResponse)
async def database_health_check(
    session: AsyncSession = Depends(get_db_session),
) -> DatabaseHealthResponse:
    return await get_database_health(session)
