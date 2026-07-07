from backend.app.config import Settings
from backend.app.prompts.planner_prompt import SYSTEM_PROMPT, build_feature_planner_prompt
from backend.app.prompts.rag_prompt import build_rag_context
from backend.app.schemas.planner_schema import (
    FeaturePlanLLMResponse,
    FeaturePlanRequest,
    FeaturePlanResponse,
    PlannerSource,
)
from backend.app.services.llm_service import generate_structured_response
from backend.app.services.rag_guardrail_service import build_retrieval_diagnostics, preview_text
from backend.app.services.rag_retrieval_service import RetrievedChunk, retrieve_rag_context_chunks


def _build_planner_sources(
    llm_plan: FeaturePlanLLMResponse,
    chunks: list[RetrievedChunk],
    preview_limit: int,
) -> list[PlannerSource]:
    chunk_by_source_id = {chunk.source_id: chunk for chunk in chunks}

    valid_source_ids = [
        source_id
        for source_id in llm_plan.source_ids
        if source_id in chunk_by_source_id
    ]

    if not valid_source_ids and chunks:
        valid_source_ids = [chunks[0].source_id]

    sources: list[PlannerSource] = []

    for source_id in valid_source_ids:
        chunk = chunk_by_source_id[source_id]

        sources.append(
            PlannerSource(
                source_id=source_id,
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                lines=f"{chunk.start_line}-{chunk.end_line}",
                similarity_score=chunk.similarity_score,
                reason_used=llm_plan.source_reasons.get(
                    str(source_id),
                    "This source was used as relevant project context for the plan.",
                ),
                content_preview=preview_text(
                    chunk.content,
                    preview_limit,
                ),
            )
        )

    return sources


async def create_feature_plan(
    project_id: str,
    request: FeaturePlanRequest,
    settings: Settings,
    session,
) -> FeaturePlanResponse:
    retrieval_result = await retrieve_rag_context_chunks(
        project_id=project_id,
        question=request.feature_request,
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

    context = build_rag_context(
        chunks=chunks,
        max_characters=settings.rag_max_context_characters,
    )

    user_prompt = build_feature_planner_prompt(
        feature_request=request.feature_request,
        planning_focus=request.planning_focus,
        context=context,
    )

    llm_plan = await generate_structured_response(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=FeaturePlanLLMResponse,
        settings=settings,
    )

    sources = _build_planner_sources(
        llm_plan=llm_plan,
        chunks=chunks,
        preview_limit=settings.rag_context_chunk_preview_limit,
    )

    return FeaturePlanResponse(
        project_id=project_id,
        feature_request=request.feature_request,
        feature_summary=llm_plan.feature_summary,
        affected_files=llm_plan.affected_files,
        implementation_steps=llm_plan.implementation_steps,
        database_changes=llm_plan.database_changes,
        api_changes=llm_plan.api_changes,
        tests_to_write=llm_plan.tests_to_write,
        risks=llm_plan.risks,
        assumptions=llm_plan.assumptions,
        estimated_complexity=llm_plan.estimated_complexity,
        sources=sources,
        model=settings.ollama_model,
        diagnostics=diagnostics,
    )