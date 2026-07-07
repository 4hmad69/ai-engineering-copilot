import streamlit as st

from frontend.api_client import APIClientError, plan_feature
from frontend.state import get_active_project_id, set_active_project_id
from frontend.ui import render_project_id_input, show_api_error


def _render_string_list_section(title: str, items: list[str]) -> None:
    st.subheader(title)

    if not items:
        st.info("None.")
        return

    for item in items:
        st.write(f"- {item}")


def _render_database_changes(items: list[dict]) -> None:
    st.subheader("Database Changes")

    if not items:
        st.info("None.")
        return

    for index, item in enumerate(items, start=1):
        change = item.get("change", "")
        reason = item.get("reason")

        with st.expander(f"Database change {index}", expanded=False):
            st.write(change)

            if reason:
                st.caption(f"Reason: {reason}")


def _render_api_changes(items: list[dict]) -> None:
    st.subheader("API Changes")

    if not items:
        st.info("None.")
        return

    for index, item in enumerate(items, start=1):
        endpoint = item.get("endpoint") or "unknown endpoint"
        method = item.get("method") or "UNKNOWN"
        description = item.get("description", "")

        with st.expander(f"{method} {endpoint}", expanded=False):
            st.write(description)


def render_feature_planner_view() -> None:
    st.header("6. Feature Planner")
    st.write("Create a retrieval-grounded implementation plan for a new feature.")

    current_project_id = get_active_project_id()

    project_id = render_project_id_input(
        current_project_id=current_project_id,
        widget_key="feature_planner_project_id_input",
    )

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload and index a project first.")
        return

    feature_request = st.text_area(
        "Feature request",
        value="Add JWT authentication with login and protected routes.",
        height=130,
        key="feature_planner_request_input",
    )

    planning_focus = st.text_input(
        "Planning focus",
        value="Focus on backend architecture, API changes, database changes, and tests.",
        key="feature_planner_focus_input",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        top_k = st.slider(
            "Top K",
            min_value=1,
            max_value=15,
            value=7,
            key="feature_planner_top_k",
        )

    with col2:
        candidate_k = st.slider(
            "Candidate K",
            min_value=5,
            max_value=50,
            value=25,
            key="feature_planner_candidate_k",
        )

    with col3:
        min_similarity = st.slider(
            "Min Similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="feature_planner_min_similarity",
        )

    with col4:
        retrieval_strategy = st.selectbox(
            "Retrieval Strategy",
            options=["mmr", "similarity"],
            index=0,
            key="feature_planner_retrieval_strategy",
        )

    if candidate_k < top_k:
        st.error("Candidate K must be greater than or equal to Top K.")
        return

    if st.button("Create Feature Plan", type="primary"):
        if len(feature_request.strip()) < 10:
            st.warning("Please enter a clearer feature request.")
            return

        try:
            with st.spinner("Retrieving context and creating feature plan..."):
                response = plan_feature(
                    project_id=project_id,
                    feature_request=feature_request,
                    planning_focus=planning_focus,
                    top_k=top_k,
                    candidate_k=candidate_k,
                    min_similarity=min_similarity,
                    retrieval_strategy=retrieval_strategy,
                )

            st.subheader("Feature Summary")
            st.write(response.get("feature_summary", ""))

            st.metric(
                "Estimated Complexity",
                response.get("estimated_complexity", "unknown"),
            )

            st.subheader("Affected Files")
            affected_files = response.get("affected_files", [])

            if not affected_files:
                st.info("No affected files identified.")
            else:
                for file_plan in affected_files:
                    with st.expander(
                        (
                            f"{file_plan.get('change_type', 'unknown').upper()} | "
                            f"{file_plan.get('file_path', 'unknown')}"
                        ),
                        expanded=False,
                    ):
                        st.write(file_plan.get("reason", ""))

            st.subheader("Implementation Steps")
            steps = response.get("implementation_steps", [])

            if not steps:
                st.info("No implementation steps returned.")
            else:
                for step in steps:
                    with st.expander(
                        f"Step {step.get('step_number')}: {step.get('title')}",
                        expanded=True,
                    ):
                        st.write(step.get("description", ""))

                        expected_files = step.get("expected_files", [])
                        if expected_files:
                            st.write("Expected files:")
                            for file_path in expected_files:
                                st.write(f"- `{file_path}`")

            _render_database_changes(response.get("database_changes", []))
            _render_api_changes(response.get("api_changes", []))
            _render_string_list_section("Tests To Write", response.get("tests_to_write", []))
            _render_string_list_section("Risks", response.get("risks", []))
            _render_string_list_section("Assumptions", response.get("assumptions", []))

            st.subheader("Sources")
            sources = response.get("sources", [])

            if not sources:
                st.info("No sources returned.")
            else:
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

            with st.expander("Retrieval diagnostics", expanded=False):
                st.json(response.get("diagnostics", {}))

            with st.expander("Raw response", expanded=False):
                st.json(response)

        except APIClientError as error:
            show_api_error(error)