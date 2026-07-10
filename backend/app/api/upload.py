from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.upload_schema import UploadCodebaseResponse
from backend.app.services.project_persistence_service import create_project_record_from_upload
from backend.app.services.upload_service import cleanup_project_storage, ingest_codebase_upload

router = APIRouter()


@router.post(
    "/upload/codebase",
    response_model=UploadCodebaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_codebase(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> UploadCodebaseResponse:
    upload_response = await ingest_codebase_upload(
        file=file,
        settings=settings,
    )

    try:
        await create_project_record_from_upload(
            upload_response=upload_response,
            session=session,
        )

    except Exception:
        cleanup_project_storage(
            project_id=upload_response.project_id,
            settings=settings,
        )
        raise

    return upload_response
