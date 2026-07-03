from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.app.config import Settings, get_settings
from backend.app.schemas.upload_schema import UploadCodebaseResponse
from backend.app.services.upload_service import ingest_codebase_upload

router = APIRouter()


@router.post(
    "/upload/codebase",
    response_model=UploadCodebaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_codebase(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> UploadCodebaseResponse:
    return await ingest_codebase_upload(
        file=file,
        settings=settings,
    )