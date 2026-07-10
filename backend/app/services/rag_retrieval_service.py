from dataclasses import dataclass
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
from backend.app.schemas.rag_schema import RetrievalStrategy
from backend.app.services.embedding_service import generate_query_embedding
from backend.app.services.retrieval_ranking_service import (
    RankedCandidate,
    coerce_vector_to_float_list,
    select_mmr_candidates,
)


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


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]
    retrieval_strategy: RetrievalStrategy
    candidates_considered: int
    top_similarity: float | None
    average_similarity: float | None


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


def _calculate_similarity_from_distance(distance: float) -> float:
    return round(max(0.0, 1.0 - distance), 4)


def _build_retrieved_chunks(
    selected_candidates: list[RankedCandidate],
    min_similarity: float,
) -> list[RetrievedChunk]:
    retrieved_chunks: list[RetrievedChunk] = []

    for source_id, candidate in enumerate(selected_candidates, start=1):
        chunk: ChunkRecord = candidate.item

        if candidate.similarity_score < min_similarity:
            continue

        retrieved_chunks.append(
            RetrievedChunk(
                source_id=source_id,
                chunk_id=chunk.chunk_uid,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                similarity_score=candidate.similarity_score,
                distance=round(candidate.distance, 4),
                content=chunk.content,
            )
        )

    return retrieved_chunks


def _build_retrieval_result(
    chunks: list[RetrievedChunk],
    retrieval_strategy: RetrievalStrategy,
    candidates_considered: int,
) -> RetrievalResult:
    if not chunks:
        return RetrievalResult(
            chunks=[],
            retrieval_strategy=retrieval_strategy,
            candidates_considered=candidates_considered,
            top_similarity=None,
            average_similarity=None,
        )

    similarities = [chunk.similarity_score for chunk in chunks]

    return RetrievalResult(
        chunks=chunks,
        retrieval_strategy=retrieval_strategy,
        candidates_considered=candidates_considered,
        top_similarity=max(similarities),
        average_similarity=round(sum(similarities) / len(similarities), 4),
    )


async def retrieve_rag_context_chunks(
    project_id: str,
    question: str,
    top_k: int,
    candidate_k: int | None,
    min_similarity: float,
    retrieval_strategy: RetrievalStrategy,
    settings: Settings,
    session: AsyncSession,
) -> RetrievalResult:
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

        candidate_limit = candidate_k or settings.rag_retrieval_candidate_k

        if retrieval_strategy == "similarity":
            candidate_limit = top_k

        candidate_limit = max(top_k, min(candidate_limit, 50))

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
            .limit(candidate_limit)
        )

        rows = result.all()

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Failed to retrieve RAG context chunks.",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    candidates: list[RankedCandidate] = []

    for chunk, distance in rows:
        embedding = coerce_vector_to_float_list(chunk.embedding)

        if not embedding:
            continue

        distance_float = float(distance)

        candidates.append(
            RankedCandidate(
                item=chunk,
                embedding=embedding,
                distance=distance_float,
                similarity_score=_calculate_similarity_from_distance(distance_float),
            )
        )

    if retrieval_strategy == "mmr":
        selected_candidates = select_mmr_candidates(
            candidates=candidates,
            query_embedding=query_embedding,
            top_k=top_k,
            lambda_mult=settings.rag_mmr_lambda,
        )
    else:
        selected_candidates = candidates[:top_k]

    retrieved_chunks = _build_retrieved_chunks(
        selected_candidates=selected_candidates,
        min_similarity=min_similarity,
    )

    return _build_retrieval_result(
        chunks=retrieved_chunks,
        retrieval_strategy=retrieval_strategy,
        candidates_considered=len(candidates),
    )
