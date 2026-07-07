import streamlit as st

from frontend.api_client import APIClientError, review_code
from frontend.ui import show_api_error


def _render_issue(issue: dict) -> None:
    severity = issue.get("severity", "unknown")
    category = issue.get("category", "unknown")
    file_path = issue.get("file_path") or "unknown file"
    line_hint = issue.get("line_hint") or "unknown section"

    title = f"{severity.upper()} | {category} | {file_path} | {line_hint}"

    with st.expander(title, expanded=severity in {"high", "critical"}):
        st.write("Problem")
        st.write(issue.get("problem", ""))

        st.write("Evidence")
        st.code(issue.get("evidence", ""), language="python")

        st.write("Suggestion")
        st.write(issue.get("suggestion", ""))


def render_code_review_view() -> None:
    st.header("5. AI Code Review")
    st.write("Paste code or a Git diff. The system will return a structured senior-engineer review.")

    review_focus = st.text_input(
        "Review focus",
        value="Find bugs, security issues, missing tests, and maintainability problems.",
        key="code_review_focus_input",
    )

    code_or_diff = st.text_area(
        "Code or Git diff",
        height=360,
        placeholder="Paste code or git diff here...",
        key="code_review_input",
    )

    if st.button("Review Code", type="primary"):
        if len(code_or_diff.strip()) < 20:
            st.warning("Please paste at least 20 characters of code or diff.")
            return

        try:
            with st.spinner("Reviewing code..."):
                response = review_code(
                    code_or_diff=code_or_diff,
                    review_focus=review_focus,
                )

            st.subheader("Summary")
            st.write(response.get("summary", ""))

            st.metric("Overall Risk", response.get("overall_risk", "unknown"))

            issues = response.get("issues", [])

            st.subheader(f"Issues Found: {len(issues)}")

            if not issues:
                st.success("No major issues found.")
            else:
                for issue in issues:
                    _render_issue(issue)

            missing_tests = response.get("missing_tests", [])
            if missing_tests:
                st.subheader("Missing Tests")
                for test in missing_tests:
                    st.write(f"- {test}")

            recommended_actions = response.get("recommended_actions", [])
            if recommended_actions:
                st.subheader("Recommended Actions")
                for action in recommended_actions:
                    st.write(f"- {action}")

            positive_notes = response.get("positive_notes", [])
            if positive_notes:
                st.subheader("Positive Notes")
                for note in positive_notes:
                    st.write(f"- {note}")

            with st.expander("Raw response", expanded=False):
                st.json(response)

        except APIClientError as error:
            show_api_error(error)