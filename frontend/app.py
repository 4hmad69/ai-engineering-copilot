from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.components.sidebar import render_sidebar
from frontend.utils.config import get_settings
from frontend.utils.session import initialize_session_state
from frontend.views.code_review import render_code_review
from frontend.views.dashboard import render_dashboard
from frontend.views.documentation import render_documentation
from frontend.views.evaluation import render_evaluation
from frontend.views.feature_planner import render_feature_planner
from frontend.views.help import render_help
from frontend.views.rag_chat import render_rag_chat
from frontend.views.semantic_search import render_semantic_search
from frontend.views.upload_index import render_upload_index


def _load_css() -> None:
    css_path = PROJECT_ROOT / "frontend" / "styles" / "custom.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def main() -> None:
    settings = get_settings()

    st.set_page_config(
        page_title=settings.app_name,
        page_icon="AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _load_css()
    initialize_session_state()

    selected_page = render_sidebar()

    page_renderers = {
        "Dashboard": render_dashboard,
        "Upload & Index": render_upload_index,
        "Semantic Search": render_semantic_search,
        "RAG Chat": render_rag_chat,
        "Code Review": render_code_review,
        "Feature Planner": render_feature_planner,
        "Documentation": render_documentation,
        "Evaluation": render_evaluation,
        "Help": render_help,
    }

    page_renderers.get(selected_page, render_dashboard)()


if __name__ == "__main__":
    main()
