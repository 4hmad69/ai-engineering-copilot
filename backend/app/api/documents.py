from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.document_schema import (
    ChunkingRequest,
    ChunkPreviewResponse,
    LoadedDocumentsResponse,
)
from backend.app.schemas.persistence_schema import PersistedChunksResponse
from backend.app.services.document_loader_service import (
    get_loaded_documents_summary,
    get_project_chunk_preview,
)
from backend.app.services.indexing_persistence_service import persist_project_documents_and_chunks

router = APIRouter()


@router.get(
    "/projects/{project_id}/documents",
    response_model=LoadedDocumentsResponse,
)
def get_project_documents(
    project_id: str,
    settings: Settings = Depends(get_settings),
) -> LoadedDocumentsResponse:
    return get_loaded_documents_summary(
        project_id=project_id,
        settings=settings,
    )


@router.post(
    "/projects/{project_id}/chunks/preview",
    response_model=ChunkPreviewResponse,
)
def preview_project_chunks(
    project_id: str,
    request: ChunkingRequest,
    settings: Settings = Depends(get_settings),
) -> ChunkPreviewResponse:
    return get_project_chunk_preview(
        project_id=project_id,
        request=request,
        settings=settings,
    )


@router.post(
    "/projects/{project_id}/chunks/persist",
    response_model=PersistedChunksResponse,
)
async def persist_project_chunks(
    project_id: str,
    request: ChunkingRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> PersistedChunksResponse:
    return await persist_project_documents_and_chunks(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )
