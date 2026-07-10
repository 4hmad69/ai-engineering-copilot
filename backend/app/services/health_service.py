from backend.app.config import Settings
from backend.app.schemas.health_schema import HealthResponse


def get_health_status(settings: Settings) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        app_version=settings.app_version,
    )
