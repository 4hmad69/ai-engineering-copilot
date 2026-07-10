from collections.abc import Callable
from pathlib import Path

import streamlit as st

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

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PageRenderer = Callable[[], None]

PAGE_RENDERERS: dict[str, PageRenderer] = {
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


def load_css() -> None:
    css_path = PROJECT_ROOT / "frontend" / "styles" / "custom.css"

    if not css_path.is_file():
        return

    css_content = css_path.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css_content}</style>",
        unsafe_allow_html=True,
    )


def render_selected_page(selected_page: str) -> None:
    renderer = PAGE_RENDERERS.get(selected_page, render_dashboard)
    renderer()


def main() -> None:
    settings = get_settings()

    st.set_page_config(
        page_title=settings.app_name,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_css()
    initialize_session_state()

    selected_page = render_sidebar()
    render_selected_page(selected_page)


if __name__ == "__main__":
    main()
