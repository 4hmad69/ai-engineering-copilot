from __future__ import annotations

import streamlit as st

from frontend.components.empty_states import render_project_required
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug
from frontend.services.api_client import APIClientError, semantic_search
from frontend.utils.session import (
    add_activity,
    get_active_project_id,
    get_last_result,
    set_last_result,
)
from frontend.utils.validators import validate_min_length


def render_semantic_search() -> None:
    render_page_header(
        "Semantic Search",
        "Search embedded source chunks with natural-language queries before involving the language model.",
        kicker="Vector retrieval",
    )

    project_id = get_active_project_id()
    if not project_id:
        render_project_required()
        return

    with st.form("semantic_search_form"):
        query = st.text_area(
            "Search query",
            value="Where is the database connection created?",
            height=110,
            help="Describe the code, behavior, function, route, or architecture you want to locate.",
        )
        top_k = st.slider("Results to return", 1, 20, 5)
        submitted = st.form_submit_button("Run semantic search", type="primary")

    if submitted:
        validation_error = validate_min_length(query, "Search query", 3)
        if validation_error:
            st.warning(validation_error)
            return

        try:
            with st.spinner("Searching embedded source chunks..."):
                response = semantic_search(project_id, query, top_k)
                set_last_result("semantic_search", response)
                add_activity("Semantic search completed", query[:90])
            st.success(f"Returned {response.get('results_count', 0)} results.")
        except APIClientError as error:
            render_api_error(error)

    response = get_last_result("semantic_search")
    if not response:
        st.info("Run a search to inspect the most relevant code chunks.")
        return

    results = response.get("results", [])
    if not results:
        st.warning("The backend returned no semantic matches.")
        render_json_debug(response)
        return

    for rank, result in enumerate(results, start=1):
        file_path = result.get("file_path", "unknown")
        start_line = result.get("start_line", "?")
        end_line = result.get("end_line", "?")
        similarity = result.get("similarity_score", "N/A")

        with st.expander(
            f"#{rank} | {file_path} | lines {start_line}-{end_line} | similarity {similarity}",
            expanded=rank == 1,
        ):
            st.caption(
                f"File type: {result.get('file_type', 'unknown')} | "
                f"Distance: {result.get('distance', 'N/A')}"
            )
            st.code(result.get("content_preview", ""), language="python")

    render_json_debug(response)
