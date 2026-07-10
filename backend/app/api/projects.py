from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.persistence_schema import ProjectRecordResponse
from backend.app.schemas.project_schema import ProjectFilesResponse
from backend.app.services.project_loader_service import list_project_files
from backend.app.services.project_persistence_service import get_project_record_by_id

router = APIRouter()


@router.get(
    "/projects/{project_id}/files",
    response_model=ProjectFilesResponse,
)
def get_project_files(
    project_id: str,
    settings: Settings = Depends(get_settings),
) -> ProjectFilesResponse:
    return list_project_files(
        project_id=project_id,
        settings=settings,
    )


@router.get(
    "/projects/{project_id}/record",
    response_model=ProjectRecordResponse,
)
async def get_project_record(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRecordResponse:
    return await get_project_record_by_id(
        project_id=project_id,
        session=session,
    )
