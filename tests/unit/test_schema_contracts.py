import pytest
from pydantic import ValidationError

from backend.app.schemas.documentation_schema import DocumentationLLMResponse
from backend.app.schemas.planner_schema import FeaturePlanLLMResponse
from backend.app.schemas.rag_schema import RAGAnswerRequest
from backend.app.schemas.review_schema import CodeReviewLLMResponse


def test_rag_request_rejects_candidate_k_smaller_than_top_k() -> None:
    with pytest.raises(ValidationError):
        RAGAnswerRequest(
            question="Where is the database configured?",
            top_k=5,
            candidate_k=4,
            min_similarity=0.0,
            retrieval_strategy="mmr",
        )


def test_rag_request_accepts_valid_candidate_k() -> None:
    request = RAGAnswerRequest(
        question="Where is the database configured?",
        top_k=5,
        candidate_k=15,
        min_similarity=0.0,
        retrieval_strategy="mmr",
    )

    assert request.candidate_k == 15
    assert request.top_k == 5


def test_review_llm_response_does_not_require_runtime_model_metadata() -> None:
    response = CodeReviewLLMResponse(
        summary="The code contains a hardcoded secret.",
        overall_risk="high",
        issues=[],
        missing_tests=[],
        recommended_actions=[],
        positive_notes=[],
    )

    assert response.overall_risk == "high"


def test_planner_normalizes_structured_api_change_string() -> None:
    response = FeaturePlanLLMResponse(
        feature_summary="Add authentication.",
        estimated_complexity="medium",
        api_changes=[
            ("endpoint='/api/v1/auth/login' method='POST' description='Create a login endpoint.'")
        ],
    )

    assert len(response.api_changes) == 1
    assert response.api_changes[0].endpoint == "/api/v1/auth/login"
    assert response.api_changes[0].method == "POST"
    assert response.api_changes[0].description == "Create a login endpoint."


def test_documentation_normalizes_string_sections() -> None:
    response = DocumentationLLMResponse(
        title="Project Documentation",
        summary="Generated documentation.",
        sections=["Overview content"],
    )

    assert len(response.sections) == 1
    assert response.sections[0].title == "Section 1"
    assert response.sections[0].content == "Overview content"
