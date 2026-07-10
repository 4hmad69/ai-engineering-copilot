from uuid import UUID

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.core.exceptions import (
    DatabaseConnectionError,
    InvalidInputError,
    ResourceNotFoundError,
)
from backend.app.models.chunk import ChunkRecord
from backend.app.models.project import ProjectRecord
from backend.app.schemas.embedding_schema import (
    EmbeddingIndexResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from backend.app.services.embedding_service import generate_embeddings, generate_query_embedding


def _parse_project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise InvalidInputError(
            "Invalid project_id format.",
            details={"project_id": project_id},
        ) from exc


def _preview_text(text: str, limit: int) -> str:
    cleaned_text = text.strip()

    if len(cleaned_text) <= limit:
        return cleaned_text

    return cleaned_text[:limit].rstrip() + "..."


async def _ensure_project_exists(
    project_uuid: UUID,
    project_id: str,
    session: AsyncSession,
) -> ProjectRecord:
    project = await session.get(ProjectRecord, project_uuid)

    if project is None:
        raise ResourceNotFoundError(
            "Project record was not found in the database.",
            details={"project_id": project_id},
        )

    return project


async def index_project_chunk_embeddings(
    project_id: str,
    settings: Settings,
    session: AsyncSession,
) -> EmbeddingIndexResponse:
    project_uuid = _parse_project_uuid(project_id)

    try:
        project = await _ensure_project_exists(
            project_uuid=project_uuid,
            project_id=project_id,
            session=session,
        )

        chunks_result = await session.execute(
            select(ChunkRecord)
            .where(ChunkRecord.project_id == project_uuid)
            .order_by(ChunkRecord.file_path, ChunkRecord.start_line)
        )

        chunks = list(chunks_result.scalars().all())

        if not chunks:
            raise InvalidInputError(
                "No chunks found for this project. Persist chunks before generating embeddings.",
                details={"project_id": project_id},
            )

        texts = [chunk.content for chunk in chunks]

        vectors = await run_in_threadpool(
            generate_embeddings,
            texts,
            settings,
        )

        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
            chunk.embedding_model = settings.embedding_model_name
            chunk.embedding_dimension = settings.embedding_dimension
            chunk.is_embedded = True

        project.status = "embedded"

        await session.commit()

        return EmbeddingIndexResponse(
            project_id=project_id,
            chunks_found=len(chunks),
            chunks_embedded=len(vectors),
            embedding_model=settings.embedding_model_name,
            embedding_dimension=settings.embedding_dimension,
            batch_size=settings.embedding_batch_size,
            message="Chunk embeddings generated and saved successfully.",
        )

    except (InvalidInputError, ResourceNotFoundError):
        raise

    except SQLAlchemyError as exc:
        await session.rollback()

        raise DatabaseConnectionError(
            "Failed to save chunk embeddings.",
            details={"error_type": exc.__class__.__name__},
        ) from exc


async def semantic_search_project_chunks(
    project_id: str,
    request: SemanticSearchRequest,
    settings: Settings,
    session: AsyncSession,
) -> SemanticSearchResponse:
    project_uuid = _parse_project_uuid(project_id)

    try:
        await _ensure_project_exists(
            project_uuid=project_uuid,
            project_id=project_id,
            session=session,
        )

        query_embedding = await run_in_threadpool(
            generate_query_embedding,
            request.query,
            settings,
        )

        distance_expression = ChunkRecord.embedding.cosine_distance(query_embedding)

        search_result = await session.execute(
            select(
                ChunkRecord,
                distance_expression.label("distance"),
            )
            .where(ChunkRecord.project_id == project_uuid)
            .where(ChunkRecord.is_embedded.is_(True))
            .where(ChunkRecord.embedding.is_not(None))
            .order_by(distance_expression)
            .limit(request.top_k)
        )

        rows = search_result.all()

        results: list[SemanticSearchResult] = []

        for chunk, distance in rows:
            distance_float = float(distance)
            similarity_score = round(max(0.0, 1.0 - distance_float), 4)

            results.append(
                SemanticSearchResult(
                    chunk_id=chunk.chunk_uid,
                    file_path=chunk.file_path,
                    file_type=chunk.file_type,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    similarity_score=similarity_score,
                    distance=round(distance_float, 4),
                    content_preview=_preview_text(
                        chunk.content,
                        settings.search_preview_character_limit,
                    ),
                )
            )

        return SemanticSearchResponse(
            project_id=project_id,
            query=request.query,
            top_k=request.top_k,
            results_count=len(results),
            embedding_model=settings.embedding_model_name,
            results=results,
        )

    except (InvalidInputError, ResourceNotFoundError):
        raise

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Semantic search failed.",
            details={"error_type": exc.__class__.__name__},
        ) from exc
