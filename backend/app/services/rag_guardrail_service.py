from backend.app.config import Settings
from backend.app.schemas.rag_schema import LLMRAGAnswer, RAGRetrievalDiagnostics, RAGSource
from backend.app.services.rag_retrieval_service import RetrievalResult, RetrievedChunk


def preview_text(text: str, limit: int) -> str:
    cleaned_text = text.strip()

    if len(cleaned_text) <= limit:
        return cleaned_text

    return cleaned_text[:limit].rstrip() + "..."


def calibrate_confidence(
    llm_answer: LLMRAGAnswer,
    chunks: list[RetrievedChunk],
    settings: Settings,
) -> str:
    if llm_answer.missing_context or not chunks:
        return "low"

    top_similarity = chunks[0].similarity_score

    if top_similarity < settings.rag_min_answer_similarity:
        return "low"

    if top_similarity < 0.35 and llm_answer.confidence == "high":
        return "medium"

    return llm_answer.confidence


def build_sources_from_llm_selection(
    llm_answer: LLMRAGAnswer,
    chunks: list[RetrievedChunk],
    preview_limit: int,
) -> list[RAGSource]:
    chunk_by_source_id = {chunk.source_id: chunk for chunk in chunks}

    valid_source_ids = [
        source_id for source_id in llm_answer.source_ids if source_id in chunk_by_source_id
    ]

    if not valid_source_ids and chunks and not llm_answer.missing_context:
        valid_source_ids = [chunks[0].source_id]

    sources: list[RAGSource] = []

    for source_id in valid_source_ids:
        chunk = chunk_by_source_id[source_id]

        sources.append(
            RAGSource(
                source_id=source_id,
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                lines=f"{chunk.start_line}-{chunk.end_line}",
                similarity_score=chunk.similarity_score,
                reason_used=llm_answer.source_reasons.get(
                    str(source_id),
                    "This source was selected because it was relevant retrieved context.",
                ),
                content_preview=preview_text(chunk.content, preview_limit),
            )
        )

    return sources


def should_force_missing_context(
    llm_answer: LLMRAGAnswer,
    chunks: list[RetrievedChunk],
    sources: list[RAGSource],
    settings: Settings,
) -> bool:
    if not chunks:
        return True

    if chunks[0].similarity_score < settings.rag_min_answer_similarity:
        return True

    if not sources and not llm_answer.missing_context:
        return True

    return llm_answer.missing_context


def build_retrieval_diagnostics(
    retrieval_result: RetrievalResult,
    min_similarity: float,
) -> RAGRetrievalDiagnostics:
    return RAGRetrievalDiagnostics(
        retrieval_strategy=retrieval_result.retrieval_strategy,
        candidates_considered=retrieval_result.candidates_considered,
        chunks_used=len(retrieval_result.chunks),
        top_similarity=retrieval_result.top_similarity,
        average_similarity=retrieval_result.average_similarity,
        min_similarity_applied=min_similarity,
    )
