import streamlit as st

from frontend.api_client import APIClientError, generate_documentation
from frontend.state import get_active_project_id, set_active_project_id
from frontend.ui import render_project_id_input, show_api_error


def _render_sources(sources: list[dict]) -> None:
    st.subheader("Sources")

    if not sources:
        st.info("No sources returned.")
        return

    for source in sources:
        with st.expander(
            (
                f"S{source.get('source_id')} | "
                f"{source.get('file_path')} lines {source.get('lines')}"
            ),
            expanded=False,
        ):
            st.write(source.get("reason_used", ""))
            st.caption(
                f"Similarity: {source.get('similarity_score')} | "
                f"Type: {source.get('file_type')}"
            )
            st.code(source.get("content_preview", ""), language="python")


def render_documentation_view() -> None:
    st.header("7. Documentation Generator")
    st.write("Generate retrieval-grounded README, architecture, API, or onboarding documentation.")

    current_project_id = get_active_project_id()

    project_id = render_project_id_input(
        current_project_id=current_project_id,
        widget_key="documentation_project_id_input",
    )

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload and index a project first.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        documentation_type = st.selectbox(
            "Documentation Type",
            options=["readme", "architecture", "api", "onboarding"],
            index=0,
            key="documentation_type_select",
        )

    with col_b:
        audience = st.text_input(
            "Audience",
            value="developers and recruiters",
            key="documentation_audience_input",
        )

    extra_instructions = st.text_area(
        "Extra Instructions",
        value=(
            "Make the documentation clear, professional, and suitable for a portfolio project."
        ),
        height=100,
        key="documentation_extra_instructions_input",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        top_k = st.slider(
            "Top K",
            min_value=1,
            max_value=15,
            value=8,
            key="documentation_top_k",
        )

    with col2:
        candidate_k = st.slider(
            "Candidate K",
            min_value=5,
            max_value=50,
            value=25,
            key="documentation_candidate_k",
        )

    with col3:
        min_similarity = st.slider(
            "Min Similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="documentation_min_similarity",
        )

    with col4:
        retrieval_strategy = st.selectbox(
            "Retrieval Strategy",
            options=["mmr", "similarity"],
            index=0,
            key="documentation_retrieval_strategy",
        )

    if candidate_k < top_k:
        st.error("Candidate K must be greater than or equal to Top K.")
        return

    if st.button("Generate Documentation", type="primary"):
        try:
            with st.spinner("Retrieving context and generating documentation..."):
                response = generate_documentation(
                    project_id=project_id,
                    documentation_type=documentation_type,
                    audience=audience,
                    extra_instructions=extra_instructions,
                    top_k=top_k,
                    candidate_k=candidate_k,
                    min_similarity=min_similarity,
                    retrieval_strategy=retrieval_strategy,
                )

            st.subheader(response.get("title", "Generated Documentation"))
            st.write(response.get("summary", ""))

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric(
                "Missing Context",
                str(response.get("missing_context", False)),
            )
            metric_col2.metric("Model", response.get("model", "unknown"))
            metric_col3.metric(
                "Sections",
                len(response.get("sections", [])),
            )

            warnings = response.get("warnings", [])
            if warnings:
                st.warning("Some warnings were returned.")
                for warning in warnings:
                    st.write(f"- {warning}")

            markdown = response.get("generated_markdown", "")

            st.subheader("Markdown Preview")
            st.markdown(markdown)

            st.download_button(
                label="Download Markdown",
                data=markdown.encode("utf-8"),
                file_name=f"{documentation_type}_documentation.md",
                mime="text/markdown",
            )

            _render_sources(response.get("sources", []))

            with st.expander("Retrieval diagnostics", expanded=False):
                st.json(response.get("diagnostics", {}))

            with st.expander("Raw response", expanded=False):
                st.json(response)

        except APIClientError as error:
            show_api_error(error)