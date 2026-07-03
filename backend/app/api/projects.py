from fastapi import APIRouter, Depends

from backend.app.config import Settings, get_settings
from backend.app.schemas.project_schema import ProjectFilesResponse
from backend.app.services.project_loader_service import list_project_files

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