from dataclasses import dataclass
from uuid import UUID

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.core.exceptions import DatabaseConnectionError, InvalidInputError, ResourceNotFoundError
from backend.app.models.chunk import ChunkRecord
from backend.app.models.project import ProjectRecord
from backend.app.services.embedding_service import generate_query_embedding

@dataclass(frozen=True)
class RetrievedChunk:
    source_id: int
    chunk_id: str
    file_path: str
    file_type: str
    start_line: int
    end_line: int
    similarity_score: float
    distance: float
    content: str


def parse_project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise InvalidInputError(
            "Invalid project_id format.",
            details={"project_id": project_id},
        ) from exc


async def ensure_project_exists(
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


async def retrieve_rag_context_chunks(
    project_id: str,
    question: str,
    top_k: int,
    min_similarity: float,
    settings: Settings,
    session: AsyncSession,
) -> list[RetrievedChunk]:
    project_uuid = parse_project_uuid(project_id)

    try:
        await ensure_project_exists(
            project_uuid=project_uuid,
            project_id=project_id,
            session=session,
        )

        query_embedding = await run_in_threadpool(
            generate_query_embedding,
            question,
            settings,
        )

        distance_expression = ChunkRecord.embedding.cosine_distance(query_embedding)

        result = await session.execute(
            select(
                ChunkRecord,
                distance_expression.label("distance"),
            )
            .where(ChunkRecord.project_id == project_uuid)
            .where(ChunkRecord.is_embedded.is_(True))
            .where(ChunkRecord.embedding.is_not(None))
            .order_by(distance_expression)
            .limit(top_k)
        )

        rows = result.all()

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Failed to retrieve RAG context chunks.",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    retrieved_chunks: list[RetrievedChunk] = []

    for index, row in enumerate(rows, start=1):
        chunk, distance = row
        distance_float = float(distance)
        similarity_score = round(max(0.0, 1.0 - distance_float), 4)

        if similarity_score < min_similarity:
            continue

        retrieved_chunks.append(
            RetrievedChunk(
                source_id=index,
                chunk_id=chunk.chunk_uid,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                similarity_score=similarity_score,
                distance=round(distance_float, 4),
                content=chunk.content,
            )
        )

    return retrieved_chunks