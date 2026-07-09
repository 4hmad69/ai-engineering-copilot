from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.documentation_schema import (
    DocumentationRequest,
    DocumentationResponse,
)
from backend.app.services.documentation_generator_service import (
    generate_project_documentation,
)

router = APIRouter()


@router.get("/documentation/status")
def documentation_status():
    return {"module": "documentation", "status": "ready"}


@router.post(
    "/documentation/generate/{project_id}",
    response_model=DocumentationResponse,
)
async def generate_documentation(
    project_id: str,
    request: DocumentationRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentationResponse:
    return await generate_project_documentation(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )