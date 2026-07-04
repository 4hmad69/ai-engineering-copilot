from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.embedding_schema import (
    EmbeddingIndexResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from backend.app.services.semantic_search_service import (
    index_project_chunk_embeddings,
    semantic_search_project_chunks,
)

router = APIRouter()


@router.post(
    "/projects/{project_id}/embeddings/index",
    response_model=EmbeddingIndexResponse,
)
async def index_project_embeddings(
    project_id: str,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> EmbeddingIndexResponse:
    return await index_project_chunk_embeddings(
        project_id=project_id,
        settings=settings,
        session=session,
    )


@router.post(
    "/projects/{project_id}/search/semantic",
    response_model=SemanticSearchResponse,
)
async def semantic_search(
    project_id: str,
    request: SemanticSearchRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> SemanticSearchResponse:
    return await semantic_search_project_chunks(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )