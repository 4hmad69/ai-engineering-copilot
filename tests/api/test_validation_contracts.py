from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_code_review_rejects_short_input() -> None:
    response = client.post(
        "/api/v1/review/code",
        json={
            "code_or_diff": "short",
            "review_focus": "Security",
        },
    )

    assert response.status_code == 422


def test_planner_rejects_candidate_k_smaller_than_top_k() -> None:
    response = client.post(
        "/api/v1/planner/feature/11111111-1111-1111-1111-111111111111",
        json={
            "feature_request": "Add authentication to protected API routes.",
            "planning_focus": "Security and testing.",
            "top_k": 10,
            "candidate_k": 5,
            "min_similarity": 0.0,
            "retrieval_strategy": "mmr",
        },
    )

    assert response.status_code == 422


def test_documentation_rejects_unknown_documentation_type() -> None:
    response = client.post(
        "/api/v1/documentation/generate/11111111-1111-1111-1111-111111111111",
        json={
            "documentation_type": "unknown",
            "audience": "developers",
            "extra_instructions": None,
            "top_k": 5,
            "candidate_k": 10,
            "min_similarity": 0.0,
            "retrieval_strategy": "mmr",
        },
    )

    assert response.status_code == 422


def test_evaluation_requires_at_least_one_case() -> None:
    response = client.post(
        "/api/v1/evaluation/run/11111111-1111-1111-1111-111111111111",
        json={
            "cases": [],
            "mode": "retrieval",
            "top_k": 5,
            "candidate_k": 10,
            "min_similarity": 0.0,
            "retrieval_strategy": "mmr",
            "keyword_match_threshold": 0.5,
        },
    )

    assert response.status_code == 422
