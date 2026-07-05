from backend.app.config import Settings
from backend.app.prompts.rag_prompt import SYSTEM_PROMPT, build_rag_context, build_user_prompt
from backend.app.schemas.rag_schema import RAGAnswerRequest, RAGAnswerResponse, RAGSource
from backend.app.services.llm_service import generate_structured_rag_answer
from backend.app.services.rag_retrieval_service import RetrievedChunk, retrieve_rag_context_chunks


def _preview_text(text: str, limit: int) -> str:
    cleaned_text = text.strip()

    if len(cleaned_text) <= limit:
        return cleaned_text

    return cleaned_text[:limit].rstrip() + "..."


def _calibrate_confidence(
    llm_confidence: str,
    missing_context: bool,
    chunks: list[RetrievedChunk],
) -> str:
    if missing_context or not chunks:
        return "low"

    top_similarity = chunks[0].similarity_score

    if top_similarity < 0.35:
        return "low"

    if top_similarity < 0.55 and llm_confidence == "high":
        return "medium"

    return llm_confidence


def _build_sources(
    llm_source_ids: list[int],
    llm_source_reasons: dict[str, str],
    chunks: list[RetrievedChunk],
    preview_limit: int,
) -> list[RAGSource]:
    chunk_by_source_id = {chunk.source_id: chunk for chunk in chunks}

    valid_source_ids = [
        source_id
        for source_id in llm_source_ids
        if source_id in chunk_by_source_id
    ]

    if not valid_source_ids and chunks:
        valid_source_ids = [chunks[0].source_id]

    sources: list[RAGSource] = []

    for source_id in valid_source_ids:
        chunk = chunk_by_source_id[source_id]

        sources.append(
            RAGSource(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                lines=f"{chunk.start_line}-{chunk.end_line}",
                similarity_score=chunk.similarity_score,
                reason_used=llm_source_reasons.get(
                    str(source_id),
                    "This source was used as relevant retrieved context.",
                ),
                content_preview=_preview_text(
                    chunk.content,
                    preview_limit,
                ),
            )
        )

    return sources


async def answer_project_question_with_rag(
    project_id: str,
    request: RAGAnswerRequest,
    settings: Settings,
    session,
) -> RAGAnswerResponse:
    chunks = await retrieve_rag_context_chunks(
        project_id=project_id,
        question=request.question,
        top_k=request.top_k,
        min_similarity=request.min_similarity,
        settings=settings,
        session=session,
    )

    if not chunks:
        return RAGAnswerResponse(
            project_id=project_id,
            question=request.question,
            answer=(
                "I could not find enough relevant embedded context to answer this question. "
                "Make sure chunks are persisted and embeddings are indexed for this project."
            ),
            confidence="low",
            missing_context=True,
            sources=[],
            follow_up_questions=[
                "Have you persisted chunks for this project?",
                "Have you generated embeddings for this project?",
            ],
            model=settings.ollama_model,
        )

    context = build_rag_context(
        chunks=chunks,
        max_characters=settings.rag_max_context_characters,
    )

    user_prompt = build_user_prompt(
        question=request.question,
        context=context,
    )

    llm_answer = await generate_structured_rag_answer(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        settings=settings,
    )

    sources = _build_sources(
        llm_source_ids=llm_answer.source_ids,
        llm_source_reasons=llm_answer.source_reasons,
        chunks=chunks,
        preview_limit=settings.rag_context_chunk_preview_limit,
    )

    calibrated_confidence = _calibrate_confidence(
        llm_confidence=llm_answer.confidence,
        missing_context=llm_answer.missing_context,
        chunks=chunks,
    )

    return RAGAnswerResponse(
        project_id=project_id,
        question=request.question,
        answer=llm_answer.answer,
        confidence=calibrated_confidence,
        missing_context=llm_answer.missing_context,
        sources=sources,
        follow_up_questions=llm_answer.follow_up_questions,
        model=settings.ollama_model,
    )