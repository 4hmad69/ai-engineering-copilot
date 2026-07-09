from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.config import get_frontend_settings
from frontend.state import get_active_project_record, initialize_state
from frontend.ui import render_project_summary
from frontend.views.code_review_view import render_code_review_view
from frontend.views.documentation_view import render_documentation_view
from frontend.views.feature_planner_view import render_feature_planner_view
from frontend.views.indexing_view import render_indexing_view
from frontend.views.rag_chat_view import render_rag_chat_view
from frontend.views.semantic_search_view import render_semantic_search_view
from frontend.views.upload_view import render_upload_view


def render_sidebar() -> None:
    settings = get_frontend_settings()

    st.sidebar.title("AI Engineering Copilot")
    st.sidebar.caption("Agentic RAG for codebases and developer workflows")

    st.sidebar.divider()

    st.sidebar.write("Backend API")
    st.sidebar.code(settings.api_base_url)

    st.sidebar.divider()

    st.sidebar.subheader("Active Project")
    render_project_summary(get_active_project_record())


def main() -> None:
    st.set_page_config(
        page_title="AI Engineering Copilot",
        page_icon="🤖",
        layout="wide",
    )

    initialize_state()
    render_sidebar()

    st.title("AI Engineering Copilot")
    st.write(
        "Upload a codebase, prepare chunks and embeddings, search semantically, "
        "ask grounded RAG questions, review code, plan features, and generate documentation."
    )

    upload_tab, indexing_tab, search_tab, chat_tab, review_tab, planner_tab, docs_tab = st.tabs(
        [
            "Upload Codebase",
            "Prepare Index",
            "Semantic Search",
            "RAG Chat",
            "Code Review",
            "Feature Planner",
            "Documentation",
        ]
    )

    with upload_tab:
        render_upload_view()

    with indexing_tab:
        render_indexing_view()

    with search_tab:
        render_semantic_search_view()

    with chat_tab:
        render_rag_chat_view()

    with review_tab:
        render_code_review_view()

    with planner_tab:
        render_feature_planner_view()

    with docs_tab:
        render_documentation_view()


if __name__ == "__main__":
    main()