from __future__ import annotations

import streamlit as st

from frontend.components.badges import render_status_badge
from frontend.components.cards import render_info_card, render_metric_card
from frontend.components.header import render_page_header
from frontend.services.api_client import (
    APIClientError,
    database_health_check,
    health_check,
)
from frontend.utils.session import (
    get_active_project_record,
    get_activity_log,
    navigate_to,
)


def _health_panel(title: str, loader) -> None:
    with st.container(border=True):
        st.markdown(f"#### {title}")
        try:
            response = loader()
            render_status_badge(str(response.get("status", "healthy")))
            with st.expander("Details", expanded=False):
                st.json(response)
        except APIClientError as error:
            render_status_badge("unhealthy")
            st.error(error.message)


def _quick_action(label: str, destination: str, key: str) -> None:
    if st.button(label, use_container_width=True, key=key):
        navigate_to(destination)
        st.rerun()


def render_dashboard() -> None:
    render_page_header(
        "AI Engineering Copilot",
        "A production workspace for codebase ingestion, semantic retrieval, grounded chat, code review, feature planning, documentation, and RAG evaluation.",
        kicker="Engineering intelligence",
    )

    record = get_active_project_record()

    metric_columns = st.columns(4)
    with metric_columns[0]:
        render_metric_card(
            "Documents",
            record.get("documents_count", 0) if record else 0,
            "Persisted source documents",
        )
    with metric_columns[1]:
        render_metric_card(
            "Chunks",
            record.get("chunks_count", 0) if record else 0,
            "Retrieval-ready code chunks",
        )
    with metric_columns[2]:
        render_metric_card(
            "Extracted files",
            record.get("extracted_files_count", 0) if record else 0,
            "Files discovered during ingestion",
        )
    with metric_columns[3]:
        render_metric_card(
            "Project status",
            record.get("status", "No project") if record else "No project",
            "Current indexing lifecycle",
        )

    st.divider()

    status_column, activity_column = st.columns([1.1, 0.9])

    with status_column:
        st.subheader("System health")
        health_columns = st.columns(2)
        with health_columns[0]:
            _health_panel("Backend API", health_check)
        with health_columns[1]:
            _health_panel("PostgreSQL and pgvector", database_health_check)

        st.subheader("Quick actions")
        action_columns = st.columns(3)
        with action_columns[0]:
            _quick_action("Upload a codebase", "Upload & Index", "dashboard_upload")
        with action_columns[1]:
            _quick_action("Ask the codebase", "RAG Chat", "dashboard_chat")
        with action_columns[2]:
            _quick_action("Run evaluation", "Evaluation", "dashboard_evaluate")

    with activity_column:
        st.subheader("Recent activity")
        activity = get_activity_log()

        if not activity:
            render_info_card(
                "No activity yet",
                "Upload a project or run an AI workflow. Recent actions will appear here for the current session.",
            )
        else:
            with st.container(border=True):
                for item in activity:
                    st.markdown(
                        f"**{item.get('title', 'Activity')}**  \n"
                        f"{item.get('detail', '')}  \n"
                        f"<span class='small-muted'>{item.get('timestamp', '')}</span>",
                        unsafe_allow_html=True,
                    )
                    st.divider()

    st.divider()
    st.subheader("Core workflow")
    workflow_columns = st.columns(3)
    with workflow_columns[0]:
        render_info_card(
            "1. Ingest and index",
            "Upload a ZIP repository, inspect supported files, persist chunks, and generate embeddings.",
        )
    with workflow_columns[1]:
        render_info_card(
            "2. Build with AI",
            "Search semantically, ask grounded questions, review code, plan features, and generate documentation.",
        )
    with workflow_columns[2]:
        render_info_card(
            "3. Measure quality",
            "Evaluate retrieval hits, answer keyword coverage, confidence, and missing-context behavior.",
        )
