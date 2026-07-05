from typing import Any

import streamlit as st

from frontend.api_client import APIClientError


def show_api_error(error: APIClientError) -> None:
    st.error(error.message)

    if error.status_code:
        st.caption(f"Status code: {error.status_code}")

    if error.details:
        with st.expander("Error details"):
            st.json(error.details)


def show_success_response(title: str, payload: dict[str, Any]) -> None:
    st.success(title)

    with st.expander("Raw response", expanded=False):
        st.json(payload)


def render_project_id_input(
    current_project_id: str,
    widget_key: str,
) -> str:
    return st.text_input(
        "Project ID",
        value=current_project_id,
        placeholder="Paste or upload a project to get a project ID",
        help="This ID connects the frontend to one uploaded codebase.",
        key=widget_key,
    )


def render_project_summary(record: dict[str, Any] | None) -> None:
    if not record:
        st.info("No project record loaded yet.")
        return

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Status", record.get("status", "unknown"))
    col2.metric("Documents", record.get("documents_count", 0))
    col3.metric("Chunks", record.get("chunks_count", 0))
    col4.metric("Files", record.get("extracted_files_count", 0))

    st.caption(f"Original file: {record.get('original_filename', 'unknown')}")


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.info("No sources returned.")
        return

    for source in sources:
        title = (
            f"S{source.get('source_id', '?')} | "
            f"{source.get('file_path', 'unknown')} "
            f"lines {source.get('lines', 'unknown')}"
        )

        with st.expander(title, expanded=False):
            st.write(source.get("reason_used", "No reason provided."))
            st.caption(
                f"Similarity: {source.get('similarity_score')} | "
                f"Type: {source.get('file_type')}"
            )
            st.code(source.get("content_preview", ""), language="python")