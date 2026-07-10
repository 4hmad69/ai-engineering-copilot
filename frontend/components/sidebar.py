from __future__ import annotations

from html import escape

import streamlit as st

from frontend.components.project import render_active_project_summary
from frontend.services.api_client import APIClientError, get_project_record
from frontend.utils.config import get_settings
from frontend.utils.session import (
    clear_active_project,
    get_active_project_id,
    set_active_project_id,
    set_active_project_record,
)

NAVIGATION_ITEMS = [
    "Dashboard",
    "Upload & Index",
    "Semantic Search",
    "RAG Chat",
    "Code Review",
    "Feature Planner",
    "Documentation",
    "Evaluation",
    "Help",
]


def render_sidebar() -> str:
    settings = get_settings()

    st.sidebar.markdown(
        f"""
        <div class="app-brand">
            <div class="app-brand-mark">AI</div>
            <div class="app-brand-name">{escape(settings.app_name)}</div>
        </div>
        <div class="app-brand-copy">
            Grounded engineering intelligence for real codebases.
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_page = st.sidebar.radio(
        "Workspace",
        NAVIGATION_ITEMS,
        key="navigation_page",
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.markdown("#### Active project")

    current_project_id = get_active_project_id()
    entered_project_id = st.sidebar.text_input(
        "Project ID",
        value=current_project_id,
        placeholder="Paste a project ID",
        key="sidebar_project_id_input",
    )

    if entered_project_id != current_project_id:
        set_active_project_id(entered_project_id)

    load_column, clear_column = st.sidebar.columns(2)

    with load_column:
        load_clicked = st.button(
            "Load",
            use_container_width=True,
            key="sidebar_load_project",
        )

    with clear_column:
        clear_clicked = st.button(
            "Clear",
            use_container_width=True,
            key="sidebar_clear_project",
        )

    if load_clicked:
        if not entered_project_id.strip():
            st.sidebar.warning("Enter a project ID first.")
        else:
            try:
                record = get_project_record(entered_project_id.strip())
                set_active_project_record(record)
                st.sidebar.success("Project loaded.")
            except APIClientError as error:
                st.sidebar.error(error.message)

    if clear_clicked:
        clear_active_project()
        st.rerun()

    render_active_project_summary()

    st.sidebar.divider()
    st.sidebar.caption("Backend API")
    st.sidebar.code(settings.api_base_url, language="text")

    return selected_page
