from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from frontend.config import get_frontend_settings


class APIClientError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


@dataclass(frozen=True)
class APIClient:
    base_url: str
    timeout_seconds: float

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIClientError(
                message="Backend returned a non-JSON response.",
                status_code=response.status_code,
                details=response.text[:700],
            ) from exc

        if response.is_error:
            error_payload = payload.get("error", payload)

            if isinstance(error_payload, dict):
                message = error_payload.get("message", "Backend request failed.")
                details = error_payload.get("details", error_payload)
            else:
                message = "Backend request failed."
                details = error_payload

            raise APIClientError(
                message=message,
                status_code=response.status_code,
                details=details,
            )

        if not isinstance(payload, dict):
            raise APIClientError(
                message="Backend returned an unexpected response shape.",
                status_code=response.status_code,
                details=payload,
            )

        return payload

    def get(self, path: str) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(self._url(path))
        except httpx.HTTPError as exc:
            raise APIClientError(
                message="Could not connect to backend API.",
                details={
                    "error_type": exc.__class__.__name__,
                    "hint": "Make sure the FastAPI backend is running.",
                },
            ) from exc

        return self._handle_response(response)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self._url(path),
                    json=json,
                    files=files,
                )
        except httpx.HTTPError as exc:
            raise APIClientError(
                message="Could not connect to backend API.",
                details={
                    "error_type": exc.__class__.__name__,
                    "hint": "Make sure the FastAPI backend is running.",
                },
            ) from exc

        return self._handle_response(response)


def get_api_client() -> APIClient:
    settings = get_frontend_settings()

    return APIClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )


def upload_codebase(filename: str, content: bytes) -> dict[str, Any]:
    client = get_api_client()

    files = {
        "file": (
            filename,
            content,
            "application/zip",
        )
    }

    return client.post(
        "/upload/codebase",
        files=files,
    )


def get_project_record(project_id: str) -> dict[str, Any]:
    client = get_api_client()

    return client.get(f"/projects/{project_id}/record")


def get_project_files(project_id: str) -> dict[str, Any]:
    client = get_api_client()

    return client.get(f"/projects/{project_id}/files")


def preview_chunks(
    project_id: str,
    chunk_size_lines: int,
    overlap_lines: int,
) -> dict[str, Any]:
    client = get_api_client()

    return client.post(
        f"/projects/{project_id}/chunks/preview",
        json={
            "chunk_size_lines": chunk_size_lines,
            "overlap_lines": overlap_lines,
        },
    )


def persist_chunks(
    project_id: str,
    chunk_size_lines: int,
    overlap_lines: int,
) -> dict[str, Any]:
    client = get_api_client()

    return client.post(
        f"/projects/{project_id}/chunks/persist",
        json={
            "chunk_size_lines": chunk_size_lines,
            "overlap_lines": overlap_lines,
        },
    )


def index_embeddings(project_id: str) -> dict[str, Any]:
    client = get_api_client()

    return client.post(f"/projects/{project_id}/embeddings/index")


def semantic_search(
    project_id: str,
    query: str,
    top_k: int,
) -> dict[str, Any]:
    client = get_api_client()

    return client.post(
        f"/projects/{project_id}/search/semantic",
        json={
            "query": query,
            "top_k": top_k,
        },
    )


def rag_chat(
    project_id: str,
    question: str,
    top_k: int,
    candidate_k: int,
    min_similarity: float,
    retrieval_strategy: str,
) -> dict[str, Any]:
    client = get_api_client()

    return client.post(
        f"/chat/rag/{project_id}",
        json={
            "question": question,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "min_similarity": min_similarity,
            "retrieval_strategy": retrieval_strategy,
        },
    )