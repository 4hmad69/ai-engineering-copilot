from __future__ import annotations

from html import escape

import streamlit as st


def render_empty_state(title: str, message: str) -> None:
    st.markdown(
        f"""
        <div class="empty-shell">
            <div class="empty-title">{escape(title)}</div>
            <div class="empty-copy">{escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_project_required() -> None:
    render_empty_state(
        "No active project",
        "Open Upload & Index to upload a ZIP codebase, or load an existing project ID from the sidebar.",
    )
