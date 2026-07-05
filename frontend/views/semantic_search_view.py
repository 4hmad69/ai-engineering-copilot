import streamlit as st

from frontend.api_client import APIClientError, semantic_search
from frontend.state import get_active_project_id, set_active_project_id
from frontend.ui import render_project_id_input, show_api_error


def render_semantic_search_view() -> None:
    st.header("3. Semantic Search")
    st.write("Search the embedded code chunks using natural language.")

    current_project_id = get_active_project_id()
    project_id = render_project_id_input(
    current_project_id=current_project_id,
    widget_key="semantic_search_project_id_input",
)

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload and index a project first.")
        return

    query = st.text_area(
        "Search query",
        value="Where is the database connection created?",
        height=100,
    )

    top_k = st.slider(
        "Top K results",
        min_value=1,
        max_value=20,
        value=5,
    )

    if st.button("Run Semantic Search", type="primary"):
        if not query.strip():
            st.warning("Please enter a search query.")
            return

        try:
            with st.spinner("Searching embedded chunks..."):
                response = semantic_search(
                    project_id=project_id,
                    query=query,
                    top_k=top_k,
                )

            st.success(f"Found {response.get('results_count', 0)} results.")

            for result in response.get("results", []):
                title = (
                    f"{result.get('file_path', 'unknown')} "
                    f"lines {result.get('start_line')}-{result.get('end_line')}"
                )

                with st.expander(title, expanded=False):
                    st.caption(
                        f"Similarity: {result.get('similarity_score')} | "
                        f"Distance: {result.get('distance')} | "
                        f"Type: {result.get('file_type')}"
                    )
                    st.code(result.get("content_preview", ""), language="python")

        except APIClientError as error:
            show_api_error(error)