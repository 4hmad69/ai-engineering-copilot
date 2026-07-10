from __future__ import annotations

import streamlit as st

from frontend.components.header import render_page_header
from frontend.utils.config import get_settings


def render_help() -> None:
    settings = get_settings()

    render_page_header(
        "Help and Architecture",
        "Understand the end-to-end workflow, backend integration, and common troubleshooting steps.",
        kicker="Product guide",
    )

    overview_tab, endpoints_tab, troubleshooting_tab = st.tabs(
        ["Workflow", "Backend endpoints", "Troubleshooting"]
    )

    with overview_tab:
        st.markdown(
            """
            ### Recommended workflow

            1. **Upload and Index**: upload a ZIP codebase, inspect files, persist chunks, and generate embeddings.
            2. **Semantic Search**: verify that relevant files and chunks are being retrieved.
            3. **RAG Chat**: ask grounded questions and inspect citations and diagnostics.
            4. **Code Review**: review pasted code or Git diffs without requiring a project.
            5. **Feature Planner**: generate a source-backed implementation plan.
            6. **Documentation**: produce README, architecture, API, or onboarding Markdown.
            7. **Evaluation**: measure retrieval hits and full-answer quality.
            """
        )

        st.markdown("### Current frontend configuration")
        st.code(
            f"FRONTEND_API_BASE_URL={settings.api_base_url}\n"
            f"FRONTEND_REQUEST_TIMEOUT_SECONDS={settings.request_timeout_seconds}",
            language="text",
        )

    with endpoints_tab:
        endpoints = [
            ["GET", "/health", "Backend health"],
            ["GET", "/health/database", "PostgreSQL and pgvector health"],
            ["POST", "/upload/codebase", "Upload and extract a ZIP repository"],
            ["GET", "/projects/{project_id}/record", "Load project metadata"],
            ["GET", "/projects/{project_id}/files", "Inspect project files"],
            ["POST", "/projects/{project_id}/chunks/preview", "Preview chunking"],
            ["POST", "/projects/{project_id}/chunks/persist", "Persist documents and chunks"],
            ["POST", "/projects/{project_id}/embeddings/index", "Generate chunk embeddings"],
            ["POST", "/projects/{project_id}/search/semantic", "Semantic search"],
            ["POST", "/chat/rag/{project_id}", "Grounded RAG answer"],
            ["POST", "/review/code", "Structured code review"],
            ["POST", "/planner/feature/{project_id}", "Feature implementation plan"],
            ["POST", "/documentation/generate/{project_id}", "Documentation generation"],
            ["POST", "/evaluation/run/{project_id}", "RAG evaluation"],
        ]
        st.dataframe(
            endpoints,
            column_config={0: "Method", 1: "Path", 2: "Purpose"},
            use_container_width=True,
            hide_index=True,
        )

    with troubleshooting_tab:
        st.markdown(
            """
            ### Frontend cannot connect to the backend
            - Local mode: confirm FastAPI is running on `http://127.0.0.1:8000`.
            - Docker mode: confirm `.env.docker` uses `FRONTEND_API_BASE_URL=http://backend:8000/api/v1`.

            ### Database health fails
            - Run `docker compose -f docker-compose.full.yml ps`.
            - Confirm the `ai_copilot_postgres` container is healthy.

            ### LLM requests time out
            - Confirm Ollama is running on the host.
            - Reduce Top K and Candidate K.
            - Use a smaller local model during development.

            ### A project page shows no data
            - Load the correct project ID.
            - Persist chunks before generating embeddings.
            - Generate embeddings before semantic search, RAG chat, planning, documentation, or evaluation.
            """
        )
