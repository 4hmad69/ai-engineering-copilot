from __future__ import annotations

import streamlit as st

from frontend.components.empty_states import render_project_required
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug, render_sources
from frontend.services.api_client import APIClientError, plan_feature
from frontend.utils.session import add_activity, get_active_project_id, get_last_result, set_last_result
from frontend.utils.validators import validate_candidate_k, validate_min_length


def _render_list(title: str, items: list) -> None:
    st.subheader(title)
    if not items:
        st.info("None returned.")
        return

    for item in items:
        if isinstance(item, dict):
            with st.container(border=True):
                for key, value in item.items():
                    st.markdown(f"**{key.replace('_', ' ').title()}**")
                    st.write(value)
        else:
            st.write(f"- {item}")


def render_feature_planner() -> None:
    render_page_header(
        "Feature Planner",
        "Convert a feature request into an implementation-ready plan grounded in retrieved project files.",
        kicker="Architecture planning",
    )

    project_id = get_active_project_id()
    if not project_id:
        render_project_required()
        return

    with st.expander("Retrieval controls", expanded=False):
        control_columns = st.columns(4)
        with control_columns[0]:
            top_k = st.slider("Top K", 1, 15, 7, key="planner_top_k")
        with control_columns[1]:
            candidate_k = st.slider("Candidate K", 5, 50, 20, key="planner_candidate_k")
        with control_columns[2]:
            min_similarity = st.slider(
                "Minimum similarity",
                0.0,
                1.0,
                0.0,
                0.05,
                key="planner_min_similarity",
            )
        with control_columns[3]:
            strategy = st.selectbox(
                "Retrieval strategy",
                ["mmr", "similarity"],
                key="planner_strategy",
            )

    validation_error = validate_candidate_k(top_k, candidate_k)
    if validation_error:
        st.error(validation_error)
        return

    with st.form("feature_planner_form"):
        feature_request = st.text_area(
            "Feature request",
            value="Add JWT authentication with login, token creation, and protected routes.",
            height=140,
        )
        planning_focus = st.text_input(
            "Planning focus",
            value="Focus on backend architecture, API changes, database changes, and tests.",
        )
        submitted = st.form_submit_button("Create feature plan", type="primary")

    if submitted:
        length_error = validate_min_length(feature_request, "Feature request", 10)
        if length_error:
            st.warning(length_error)
            return

        try:
            with st.spinner("Retrieving code context and building the implementation plan..."):
                response = plan_feature(
                    project_id,
                    feature_request,
                    planning_focus,
                    top_k,
                    candidate_k,
                    min_similarity,
                    strategy,
                )
                set_last_result("feature_plan", response)
                add_activity("Feature plan generated", feature_request[:90])
            st.success("Feature plan generated.")
        except APIClientError as error:
            render_api_error(error)

    response = get_last_result("feature_plan")
    if not response:
        return

    summary_columns = st.columns([1.7, 0.3])
    with summary_columns[0]:
        st.subheader("Feature summary")
        st.write(response.get("feature_summary", ""))
    with summary_columns[1]:
        st.metric("Complexity", response.get("estimated_complexity", "unknown"))

    st.subheader("Affected files")
    affected_files = response.get("affected_files", [])
    if not affected_files:
        st.info("No affected files were identified.")
    for item in affected_files:
        with st.expander(
            f"{str(item.get('change_type', 'unknown')).upper()} | {item.get('file_path', 'unknown')}",
            expanded=False,
        ):
            st.write(item.get("reason", ""))

    st.subheader("Implementation steps")
    steps = response.get("implementation_steps", [])
    if not steps:
        st.info("No implementation steps were returned.")
    for step in steps:
        with st.expander(
            f"Step {step.get('step_number', '?')}: {step.get('title', 'Untitled step')}",
            expanded=True,
        ):
            st.write(step.get("description", ""))
            expected_files = step.get("expected_files", [])
            if expected_files:
                st.markdown("**Expected files**")
                for file_path in expected_files:
                    st.write(f"- `{file_path}`")

    plan_tabs = st.tabs(["Database", "API", "Tests", "Risks", "Assumptions"])
    sections = [
        ("Database changes", "database_changes"),
        ("API changes", "api_changes"),
        ("Tests to write", "tests_to_write"),
        ("Risks", "risks"),
        ("Assumptions", "assumptions"),
    ]
    for tab, (title, key) in zip(plan_tabs, sections, strict=True):
        with tab:
            _render_list(title, response.get(key, []))

    render_sources(response.get("sources", []))
    render_json_debug(response)
