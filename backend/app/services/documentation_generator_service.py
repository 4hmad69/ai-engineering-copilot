from backend.app.config import Settings
from backend.app.prompts.documentation_prompt import (
    SYSTEM_PROMPT,
    build_documentation_prompt,
)
from backend.app.prompts.rag_prompt import build_rag_context
from backend.app.schemas.documentation_schema import (
    DocumentationLLMResponse,
    DocumentationRequest,
    DocumentationResponse,
    DocumentationSource,
)
from backend.app.services.llm_service import generate_structured_response
from backend.app.services.rag_guardrail_service import (
    build_retrieval_diagnostics,
    preview_text,
)
from backend.app.services.rag_retrieval_service import (
    RetrievedChunk,
    retrieve_rag_context_chunks,
)


def _build_markdown_from_sections(
    title: str,
    summary: str,
    sections,
    warnings: list[str],
) -> str:
    markdown_parts: list[str] = [
        f"# {title}",
        "",
        summary.strip(),
        "",
    ]

    for section in sections:
        markdown_parts.extend(
            [
                f"## {section.title}",
                "",
                section.content.strip(),
                "",
            ]
        )

    if warnings:
        markdown_parts.extend(
            [
                "## Warnings And Missing Context",
                "",
            ]
        )

        for warning in warnings:
            markdown_parts.append(f"- {warning}")

        markdown_parts.append("")

    return "\n".join(markdown_parts).strip() + "\n"


def _build_documentation_sources(
    llm_response: DocumentationLLMResponse,
    chunks: list[RetrievedChunk],
    preview_limit: int,
) -> list[DocumentationSource]:
    chunk_by_source_id = {chunk.source_id: chunk for chunk in chunks}

    valid_source_ids = [
        source_id
        for source_id in llm_response.source_ids
        if source_id in chunk_by_source_id
    ]

    if not valid_source_ids and chunks and not llm_response.missing_context:
        valid_source_ids = [chunks[0].source_id]

    sources: list[DocumentationSource] = []

    for source_id in valid_source_ids:
        chunk = chunk_by_source_id[source_id]

        sources.append(
            DocumentationSource(
                source_id=source_id,
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                lines=f"{chunk.start_line}-{chunk.end_line}",
                similarity_score=chunk.similarity_score,
                reason_used=llm_response.source_reasons.get(
                    str(source_id),
                    "This source was used as relevant documentation context.",
                ),
                content_preview=preview_text(
                    chunk.content,
                    preview_limit,
                ),
            )
        )

    return sources


async def generate_project_documentation(
    project_id: str,
    request: DocumentationRequest,
    settings: Settings,
    session,
) -> DocumentationResponse:
    documentation_query = (
        f"{request.documentation_type} documentation for project. "
        f"Audience: {request.audience}. "
        f"{request.extra_instructions or ''}"
    )

    retrieval_result = await retrieve_rag_context_chunks(
        project_id=project_id,
        question=documentation_query,
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
        title = "Documentation Could Not Be Generated"
        summary = (
            "No relevant embedded project context was found. "
            "Persist chunks and generate embeddings before generating documentation."
        )
        warnings = [
            "No retrieved context was available.",
            "The project may not have persisted chunks or indexed embeddings yet.",
        ]

        return DocumentationResponse(
            project_id=project_id,
            documentation_type=request.documentation_type,
            audience=request.audience,
            title=title,
            summary=summary,
            missing_context=True,
            sections=[],
            warnings=warnings,
            generated_markdown=_build_markdown_from_sections(
                title=title,
                summary=summary,
                sections=[],
                warnings=warnings,
            ),
            sources=[],
            model=settings.ollama_model,
            diagnostics=diagnostics,
        )

    context = build_rag_context(
        chunks=chunks,
        max_characters=settings.rag_max_context_characters,
    )

    user_prompt = build_documentation_prompt(
        documentation_type=request.documentation_type,
        audience=request.audience,
        extra_instructions=request.extra_instructions,
        context=context,
    )

    llm_response = await generate_structured_response(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=DocumentationLLMResponse,
        settings=settings,
    )

    markdown = llm_response.generated_markdown or _build_markdown_from_sections(
        title=llm_response.title,
        summary=llm_response.summary,
        sections=llm_response.sections,
        warnings=llm_response.warnings,
    )

    sources = _build_documentation_sources(
        llm_response=llm_response,
        chunks=chunks,
        preview_limit=settings.rag_context_chunk_preview_limit,
    )

    missing_context = llm_response.missing_context or not sources

    warnings = list(llm_response.warnings)

    if not sources:
        warnings.append(
            "The model did not provide valid source IDs, so source support may be incomplete."
        )

    return DocumentationResponse(
        project_id=project_id,
        documentation_type=request.documentation_type,
        audience=request.audience,
        title=llm_response.title,
        summary=llm_response.summary,
        missing_context=missing_context,
        sections=llm_response.sections,
        warnings=warnings,
        generated_markdown=markdown,
        sources=sources,
        model=settings.ollama_model,
        diagnostics=diagnostics,
    )