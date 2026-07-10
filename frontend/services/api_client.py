from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from frontend.utils.config import get_settings

HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class APIClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        details: Any | None = None,
        retryable: bool = False,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details
        self.retryable = retryable
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class APIClient:
    base_url: str
    timeout_seconds: float

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=10.0,
            read=self.timeout_seconds,
            write=60.0,
            pool=10.0,
        )

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 204 or not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise APIClientError(
                "The backend returned an invalid response.",
                status_code=response.status_code,
                details={"response_preview": response.text[:1000]},
            ) from exc

        if response.is_error:
            error_payload = payload.get("error", payload) if isinstance(payload, dict) else payload

            if isinstance(error_payload, dict):
                message = str(error_payload.get("message", "Backend request failed."))
                details = error_payload.get("details", error_payload)
            else:
                message = "Backend request failed."
                details = error_payload

            raise APIClientError(
                message,
                status_code=response.status_code,
                details=details,
                retryable=response.status_code >= 500,
            )

        if not isinstance(payload, dict):
            raise APIClientError(
                "The backend returned an unexpected response shape.",
                status_code=response.status_code,
                details=payload,
            )

        return payload

    def request(
        self,
        method: HTTPMethod,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        transport = httpx.HTTPTransport(retries=2)

        try:
            with httpx.Client(
                timeout=self._timeout(),
                transport=transport,
                follow_redirects=True,
            ) as client:
                response = client.request(
                    method,
                    self._url(path),
                    json=json_body,
                    files=files,
                    params=params,
                    headers={"Accept": "application/json"},
                )
        except httpx.TimeoutException as exc:
            raise APIClientError(
                "The request timed out before the backend finished.",
                details={
                    "hint": "Retry the action. For LLM operations, reduce context settings or use a smaller model.",
                    "error_type": exc.__class__.__name__,
                },
                retryable=True,
            ) from exc
        except httpx.ConnectError as exc:
            raise APIClientError(
                "The frontend could not connect to the backend API.",
                details={
                    "hint": "Confirm the FastAPI container or local backend is running and healthy.",
                    "api_base_url": self.base_url,
                    "error_type": exc.__class__.__name__,
                },
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise APIClientError(
                "A network error occurred while contacting the backend.",
                details={"error_type": exc.__class__.__name__},
                retryable=True,
            ) from exc

        return self._parse_response(response)

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request("POST", path, json_body=json_body, files=files)


def get_api_client() -> APIClient:
    settings = get_settings()
    return APIClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )


def health_check() -> dict[str, Any]:
    return get_api_client().get("/health")


def database_health_check() -> dict[str, Any]:
    return get_api_client().get("/health/database")


def upload_codebase(filename: str, content: bytes) -> dict[str, Any]:
    return get_api_client().post(
        "/upload/codebase",
        files={"file": (filename, content, "application/zip")},
    )


def get_project_record(project_id: str) -> dict[str, Any]:
    return get_api_client().get(f"/projects/{project_id}/record")


def get_project_files(project_id: str) -> dict[str, Any]:
    return get_api_client().get(f"/projects/{project_id}/files")


def preview_chunks(
    project_id: str,
    chunk_size_lines: int,
    overlap_lines: int,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/projects/{project_id}/chunks/preview",
        json_body={
            "chunk_size_lines": chunk_size_lines,
            "overlap_lines": overlap_lines,
        },
    )


def persist_chunks(
    project_id: str,
    chunk_size_lines: int,
    overlap_lines: int,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/projects/{project_id}/chunks/persist",
        json_body={
            "chunk_size_lines": chunk_size_lines,
            "overlap_lines": overlap_lines,
        },
    )


def index_embeddings(project_id: str) -> dict[str, Any]:
    return get_api_client().post(f"/projects/{project_id}/embeddings/index")


def semantic_search(
    project_id: str,
    query: str,
    top_k: int,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/projects/{project_id}/search/semantic",
        json_body={"query": query, "top_k": top_k},
    )


def rag_chat(
    project_id: str,
    question: str,
    top_k: int,
    candidate_k: int,
    min_similarity: float,
    retrieval_strategy: str,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/chat/rag/{project_id}",
        json_body={
            "question": question,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "min_similarity": min_similarity,
            "retrieval_strategy": retrieval_strategy,
        },
    )


def review_code(code_or_diff: str, review_focus: str | None) -> dict[str, Any]:
    return get_api_client().post(
        "/review/code",
        json_body={
            "code_or_diff": code_or_diff,
            "review_focus": review_focus,
        },
    )


def plan_feature(
    project_id: str,
    feature_request: str,
    planning_focus: str | None,
    top_k: int,
    candidate_k: int,
    min_similarity: float,
    retrieval_strategy: str,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/planner/feature/{project_id}",
        json_body={
            "feature_request": feature_request,
            "planning_focus": planning_focus,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "min_similarity": min_similarity,
            "retrieval_strategy": retrieval_strategy,
        },
    )


def generate_documentation(
    project_id: str,
    documentation_type: str,
    audience: str,
    extra_instructions: str | None,
    top_k: int,
    candidate_k: int,
    min_similarity: float,
    retrieval_strategy: str,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/documentation/generate/{project_id}",
        json_body={
            "documentation_type": documentation_type,
            "audience": audience,
            "extra_instructions": extra_instructions,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "min_similarity": min_similarity,
            "retrieval_strategy": retrieval_strategy,
        },
    )


def run_evaluation(
    project_id: str,
    cases: list[dict[str, Any]],
    mode: str,
    top_k: int,
    candidate_k: int,
    min_similarity: float,
    retrieval_strategy: str,
    keyword_match_threshold: float,
) -> dict[str, Any]:
    return get_api_client().post(
        f"/evaluation/run/{project_id}",
        json_body={
            "cases": cases,
            "mode": mode,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "min_similarity": min_similarity,
            "retrieval_strategy": retrieval_strategy,
            "keyword_match_threshold": keyword_match_threshold,
        },
    )
