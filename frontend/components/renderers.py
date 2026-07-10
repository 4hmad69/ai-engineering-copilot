from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.services.api_client import APIClientError


def render_api_error(error: APIClientError) -> None:
    st.error(error.message)

    if error.status_code is not None:
        st.caption(f"HTTP status: {error.status_code}")

    if error.retryable:
        st.info("This failure may be temporary. Check service health and retry the action.")

    if error.details:
        with st.expander("Technical details", expanded=False):
            if isinstance(error.details, (dict, list)):
                st.json(error.details)
            else:
                st.code(str(error.details), language="text")


def render_json_debug(payload: dict[str, Any], label: str = "Raw response") -> None:
    with st.expander(label, expanded=False):
        st.json(payload)


def render_sources(sources: list[dict[str, Any]], heading: str = "Sources") -> None:
    st.subheader(heading)

    if not sources:
        st.info("No supporting sources were returned.")
        return

    for source in sources:
        source_id = source.get("source_id", "?")
        file_path = source.get("file_path", "unknown")
        lines = source.get("lines", "unknown")

        with st.expander(
            f"S{source_id} | {file_path} | lines {lines}",
            expanded=False,
        ):
            reason = source.get("reason_used")
            if reason:
                st.write(reason)

            st.caption(
                f"Similarity: {source.get('similarity_score', 'N/A')} | "
                f"Type: {source.get('file_type', 'unknown')}"
            )

            preview = source.get("content_preview")
            if preview:
                st.code(preview, language="python")
