from __future__ import annotations

import streamlit as st

from frontend.components.empty_states import render_project_required
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug, render_sources
from frontend.services.api_client import APIClientError, generate_documentation
from frontend.utils.session import (
    add_activity,
    get_active_project_id,
    get_last_result,
    set_last_result,
)
from frontend.utils.validators import validate_candidate_k, validate_min_length


def render_documentation() -> None:
    render_page_header(
        "Documentation Generator",
        "Generate source-grounded README, architecture, API, or onboarding documentation and export it as Markdown.",
        kicker="Technical writing",
    )

    project_id = get_active_project_id()
    if not project_id:
        render_project_required()
        return

    with st.expander("Retrieval controls", expanded=False):
        control_columns = st.columns(4)
        with control_columns[0]:
            top_k = st.slider("Top K", 1, 15, 5, key="docs_top_k")
        with control_columns[1]:
            candidate_k = st.slider("Candidate K", 5, 50, 12, key="docs_candidate_k")
        with control_columns[2]:
            min_similarity = st.slider(
                "Minimum similarity",
                0.0,
                1.0,
                0.0,
                0.05,
                key="docs_min_similarity",
            )
        with control_columns[3]:
            strategy = st.selectbox(
                "Retrieval strategy",
                ["mmr", "similarity"],
                key="docs_strategy",
            )

    validation_error = validate_candidate_k(top_k, candidate_k)
    if validation_error:
        st.error(validation_error)
        return

    with st.form("documentation_form"):
        input_columns = st.columns(2)
        with input_columns[0]:
            documentation_type = st.selectbox(
                "Documentation type",
                ["readme", "architecture", "api", "onboarding"],
            )
        with input_columns[1]:
            audience = st.text_input(
                "Audience",
                value="developers and recruiters",
            )

        extra_instructions = st.text_area(
            "Extra instructions",
            value="Make the documentation clear, accurate, professional, and portfolio-ready.",
            height=100,
        )
        submitted = st.form_submit_button("Generate documentation", type="primary")

    if submitted:
        audience_error = validate_min_length(audience, "Audience", 3)
        if audience_error:
            st.warning(audience_error)
            return

        try:
            with st.spinner("Retrieving project context and writing documentation..."):
                response = generate_documentation(
                    project_id,
                    documentation_type,
                    audience,
                    extra_instructions,
                    top_k,
                    candidate_k,
                    min_similarity,
                    strategy,
                )
                set_last_result("documentation", response)
                add_activity("Documentation generated", documentation_type)
            st.success("Documentation generated.")
        except APIClientError as error:
            render_api_error(error)

    response = get_last_result("documentation")
    if not response:
        return

    summary_columns = st.columns([1.7, 0.3])
    with summary_columns[0]:
        st.subheader(response.get("title", "Generated documentation"))
        st.write(response.get("summary", ""))
    with summary_columns[1]:
        st.metric("Sections", len(response.get("sections", [])))

    warnings = response.get("warnings", [])
    if warnings:
        with st.expander("Warnings and missing context", expanded=True):
            for warning in warnings:
                st.write(f"- {warning}")

    markdown = response.get("generated_markdown", "")
    preview_tab, source_tab = st.tabs(["Markdown preview", "Sources"])

    with preview_tab:
        if markdown:
            st.markdown(markdown)
            st.download_button(
                "Download Markdown",
                data=markdown.encode("utf-8"),
                file_name=f"{response.get('documentation_type', 'project')}_documentation.md",
                mime="text/markdown",
                key="docs_download",
            )
        else:
            st.warning("The backend did not return generated Markdown.")

    with source_tab:
        render_sources(response.get("sources", []))

    render_json_debug(response)
