from backend.app.config import Settings
from backend.app.prompts.rag_prompt import SYSTEM_PROMPT, build_rag_context, build_user_prompt
from backend.app.schemas.rag_schema import RAGAnswerRequest, RAGAnswerResponse
from backend.app.services.llm_service import generate_structured_rag_answer
from backend.app.services.rag_guardrail_service import (
    build_retrieval_diagnostics,
    build_sources_from_llm_selection,
    calibrate_confidence,
    should_force_missing_context,
)
from backend.app.services.rag_retrieval_service import retrieve_rag_context_chunks


async def answer_project_question_with_rag(
    project_id: str,
    request: RAGAnswerRequest,
    settings: Settings,
    session,
) -> RAGAnswerResponse:
    retrieval_result = await retrieve_rag_context_chunks(
        project_id=project_id,
        question=request.question,
        top_k=request.top_k,
        candidate_k=request.candidate_k,
        min_similarity=request.min_similarity,
        retrieval_strategy=request.retrieval_strategy,
        settings=settings,
        session=session,
    )

    diagnostics = build_retrieval_diagnostics(
        retrieval_result=retrieval_result,
        min_similarity=request.min_similarity,
    )

    chunks = retrieval_result.chunks

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
                "Can you ask a more specific question about a file, route, or function?",
            ],
            model=settings.ollama_model,
            diagnostics=diagnostics,
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

    sources = build_sources_from_llm_selection(
        llm_answer=llm_answer,
        chunks=chunks,
        preview_limit=settings.rag_context_chunk_preview_limit,
    )

    missing_context = should_force_missing_context(
        llm_answer=llm_answer,
        chunks=chunks,
        sources=sources,
        settings=settings,
    )

    confidence = calibrate_confidence(
        llm_answer=llm_answer,
        chunks=chunks,
        settings=settings,
    )

    if missing_context:
        confidence = "low"

    return RAGAnswerResponse(
        project_id=project_id,
        question=request.question,
        answer=llm_answer.answer,
        confidence=confidence,
        missing_context=missing_context,
        sources=sources,
        follow_up_questions=llm_answer.follow_up_questions,
        model=settings.ollama_model,
        diagnostics=diagnostics,
    )