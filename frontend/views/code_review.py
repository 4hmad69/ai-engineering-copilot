from __future__ import annotations

import streamlit as st

from frontend.components.badges import render_badge
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug
from frontend.services.api_client import APIClientError, review_code
from frontend.utils.session import add_activity, get_last_result, set_last_result
from frontend.utils.validators import validate_min_length


def _severity_variant(severity: str) -> str:
    normalized = severity.lower()
    if normalized in {"critical", "high"}:
        return "danger"
    if normalized == "medium":
        return "warning"
    if normalized == "low":
        return "info"
    return "muted"


def render_code_review() -> None:
    render_page_header(
        "AI Code Review",
        "Paste source code or a Git diff and receive a structured review covering bugs, security, validation, error handling, maintainability, and tests.",
        kicker="Senior engineering review",
    )

    with st.form("code_review_form"):
        review_focus = st.text_input(
            "Review focus",
            value="Find bugs, security issues, missing tests, and maintainability problems.",
            help="Optional guidance for the reviewer.",
        )
        code_or_diff = st.text_area(
            "Code or Git diff",
            height=380,
            placeholder="Paste code or a Git diff here...",
        )
        submitted = st.form_submit_button("Review code", type="primary")

    if submitted:
        validation_error = validate_min_length(code_or_diff, "Code or diff", 20)
        if validation_error:
            st.warning(validation_error)
            return

        try:
            with st.spinner("Running a structured senior-engineer review..."):
                response = review_code(code_or_diff, review_focus)
                set_last_result("code_review", response)
                add_activity("Code review completed", response.get("overall_risk", "unknown risk"))
            st.success("Review completed.")
        except APIClientError as error:
            render_api_error(error)

    response = get_last_result("code_review")
    if not response:
        return

    summary_columns = st.columns([1.7, 0.3])
    with summary_columns[0]:
        st.subheader("Review summary")
        st.write(response.get("summary", ""))
    with summary_columns[1]:
        st.caption("Overall risk")
        risk = str(response.get("overall_risk", "unknown"))
        render_badge(risk.upper(), _severity_variant(risk))

    issues = response.get("issues", [])
    st.subheader(f"Issues ({len(issues)})")

    if not issues:
        st.success("No major issues were identified in the submitted code.")
    else:
        for index, issue in enumerate(issues, start=1):
            severity = str(issue.get("severity", "unknown"))
            category = issue.get("category", "uncategorized")
            file_path = issue.get("file_path") or "Unknown file"
            line_hint = issue.get("line_hint") or "Unknown section"

            with st.expander(
                f"#{index} | {severity.upper()} | {category} | {file_path} | {line_hint}",
                expanded=severity.lower() in {"critical", "high"},
            ):
                render_badge(severity.upper(), _severity_variant(severity))
                st.markdown("#### Problem")
                st.write(issue.get("problem", ""))
                st.markdown("#### Evidence")
                st.code(issue.get("evidence", ""), language="python")
                st.markdown("#### Recommended fix")
                st.write(issue.get("suggestion", ""))

    detail_tabs = st.tabs(["Missing tests", "Recommended actions", "Positive notes"])
    keys = ["missing_tests", "recommended_actions", "positive_notes"]
    for tab, key in zip(detail_tabs, keys, strict=True):
        with tab:
            items = response.get(key, [])
            if not items:
                st.info("No items returned.")
            for item in items:
                st.write(f"- {item}")

    render_json_debug(response)
