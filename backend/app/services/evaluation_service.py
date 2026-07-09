from statistics import mean
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.schemas.evaluation_schema import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSummary,
)
from backend.app.schemas.rag_schema import RAGAnswerRequest
from backend.app.services.rag_answer_service import answer_project_question_with_rag
from backend.app.services.rag_guardrail_service import build_retrieval_diagnostics
from backend.app.services.rag_retrieval_service import (
    RetrievedChunk,
    retrieve_rag_context_chunks,
)


def _normalize_text(value: str) -> str:
    return value.strip().lower().replace("\\", "/")


def _safe_average(values: Iterable[float | None]) -> float | None:
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return None

    return round(mean(clean_values), 4)


def _source_file_matches_expected(source_file: str, expected_file: str) -> bool:
    normalized_source = _normalize_text(source_file)
    normalized_expected = _normalize_text(expected_file)

    return (
        normalized_source == normalized_expected
        or normalized_source.endswith(normalized_expected)
        or normalized_expected in normalized_source
    )


def _calculate_expected_file_matches(
    expected_files: list[str],
    source_files: list[str],
) -> tuple[list[str], list[str]]:
    found_files: list[str] = []
    missing_files: list[str] = []

    for expected_file in expected_files:
        if any(
            _source_file_matches_expected(
                source_file=source_file,
                expected_file=expected_file,
            )
            for source_file in source_files
        ):
            found_files.append(expected_file)
        else:
            missing_files.append(expected_file)

    return found_files, missing_files


def _calculate_keyword_matches(
    answer: str | None,
    expected_keywords: list[str],
) -> tuple[float | None, list[str], list[str]]:
    if not expected_keywords:
        return None, [], []

    answer_text = _normalize_text(answer or "")

    matched_keywords: list[str] = []
    missing_keywords: list[str] = []

    for keyword in expected_keywords:
        normalized_keyword = _normalize_text(keyword)

        if normalized_keyword and normalized_keyword in answer_text:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    coverage = round(len(matched_keywords) / len(expected_keywords), 4)

    return coverage, matched_keywords, missing_keywords


def _build_failure_reasons(
    expected_files: list[str],
    expected_files_missing: list[str],
    chunks_used: int,
    mode: str,
    missing_context: bool | None,
    keyword_coverage: float | None,
    keyword_match_threshold: float,
) -> list[str]:
    failure_reasons: list[str] = []

    if chunks_used == 0:
        failure_reasons.append("No chunks were retrieved.")

    if expected_files and expected_files_missing:
        failure_reasons.append(
            "One or more expected files were not found in retrieved sources."
        )

    if mode == "rag" and missing_context:
        failure_reasons.append("RAG answer reported missing context.")

    if (
        mode == "rag"
        and keyword_coverage is not None
        and keyword_coverage < keyword_match_threshold
    ):
        failure_reasons.append(
            "Generated answer did not meet the expected keyword coverage threshold."
        )

    return failure_reasons


def _get_source_files_from_chunks(chunks: list[RetrievedChunk]) -> list[str]:
    return sorted({chunk.file_path for chunk in chunks})


def _get_case_id(case: EvaluationCase, index: int) -> str:
    if case.case_id:
        return case.case_id

    return f"case_{index}"


async def _evaluate_single_case(
    project_id: str,
    case: EvaluationCase,
    case_index: int,
    request: EvaluationRunRequest,
    settings: Settings,
    session: AsyncSession,
) -> EvaluationCaseResult:
    retrieval_result = await retrieve_rag_context_chunks(
        project_id=project_id,
        question=case.question,
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
    source_files = _get_source_files_from_chunks(chunks)

    expected_files_found, expected_files_missing = _calculate_expected_file_matches(
        expected_files=case.expected_files,
        source_files=source_files,
    )

    retrieval_hit = None

    if case.expected_files:
        retrieval_hit = len(expected_files_missing) == 0

    answer: str | None = None
    confidence = None
    missing_context = None
    keyword_coverage = None
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []

    if request.mode == "rag":
        rag_response = await answer_project_question_with_rag(
            project_id=project_id,
            request=RAGAnswerRequest(
                question=case.question,
                top_k=request.top_k,
                candidate_k=request.candidate_k,
                min_similarity=request.min_similarity,
                retrieval_strategy=request.retrieval_strategy,
            ),
            settings=settings,
            session=session,
        )

        answer = rag_response.answer
        confidence = rag_response.confidence
        missing_context = rag_response.missing_context

        (
            keyword_coverage,
            matched_keywords,
            missing_keywords,
        ) = _calculate_keyword_matches(
            answer=answer,
            expected_keywords=case.expected_answer_keywords,
        )

    failure_reasons = _build_failure_reasons(
        expected_files=case.expected_files,
        expected_files_missing=expected_files_missing,
        chunks_used=len(chunks),
        mode=request.mode,
        missing_context=missing_context,
        keyword_coverage=keyword_coverage,
        keyword_match_threshold=request.keyword_match_threshold,
    )

    passed = len(failure_reasons) == 0

    return EvaluationCaseResult(
        case_id=_get_case_id(case, case_index),
        question=case.question,
        tags=case.tags,
        mode=request.mode,
        passed=passed,
        failure_reasons=failure_reasons,
        expected_files=case.expected_files,
        expected_files_found=expected_files_found,
        expected_files_missing=expected_files_missing,
        retrieval_hit=retrieval_hit,
        source_files=source_files,
        chunks_used=len(chunks),
        top_similarity=retrieval_result.top_similarity,
        average_similarity=retrieval_result.average_similarity,
        answer=answer,
        confidence=confidence,
        missing_context=missing_context,
        keyword_coverage=keyword_coverage,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        diagnostics=diagnostics,
    )


def _build_summary(results: list[EvaluationCaseResult]) -> EvaluationSummary:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    failed_cases = total_cases - passed_cases

    retrieval_results = [
        result for result in results if result.retrieval_hit is not None
    ]

    retrieval_hit_rate = None

    if retrieval_results:
        retrieval_hit_rate = round(
            sum(1 for result in retrieval_results if result.retrieval_hit)
            / len(retrieval_results),
            4,
        )

    generated_answers_count = sum(
        1 for result in results if result.answer is not None
    )

    return EvaluationSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        pass_rate=round(passed_cases / total_cases, 4) if total_cases else 0.0,
        retrieval_hit_rate=retrieval_hit_rate,
        average_top_similarity=_safe_average(
            result.top_similarity for result in results
        ),
        average_keyword_coverage=_safe_average(
            result.keyword_coverage for result in results
        ),
        generated_answers_count=generated_answers_count,
    )


async def run_project_evaluation(
    project_id: str,
    request: EvaluationRunRequest,
    settings: Settings,
    session: AsyncSession,
) -> EvaluationRunResponse:
    results: list[EvaluationCaseResult] = []

    for index, case in enumerate(request.cases, start=1):
        result = await _evaluate_single_case(
            project_id=project_id,
            case=case,
            case_index=index,
            request=request,
            settings=settings,
            session=session,
        )

        results.append(result)

    return EvaluationRunResponse(
        project_id=project_id,
        mode=request.mode,
        summary=_build_summary(results),
        results=results,
    )