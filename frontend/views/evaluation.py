from __future__ import annotations

import json

import streamlit as st

from frontend.components.empty_states import render_project_required
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug
from frontend.services.api_client import APIClientError, run_evaluation
from frontend.utils.formatters import format_percentage
from frontend.utils.session import add_activity, get_active_project_id, get_last_result, set_last_result
from frontend.utils.validators import parse_json_list, validate_candidate_k


def _starter_cases() -> str:
    return json.dumps(
        [
            {
                "case_id": "project_overview",
                "question": "What is the main purpose of this project?",
                "expected_files": [],
                "expected_answer_keywords": [],
                "tags": ["overview"],
            },
            {
                "case_id": "database_location",
                "question": "Where is the database connection configured?",
                "expected_files": [],
                "expected_answer_keywords": [],
                "tags": ["database"],
            },
        ],
        indent=2,
    )


def render_evaluation() -> None:
    render_page_header(
        "RAG Evaluation",
        "Measure retrieval hits and full-answer quality with repeatable test cases, expected files, and keyword thresholds.",
        kicker="Quality assurance",
    )

    project_id = get_active_project_id()
    if not project_id:
        render_project_required()
        return

    st.info(
        "Expected file paths are project-specific. Add them only after confirming the exact paths returned by semantic search."
    )

    raw_cases = st.text_area(
        "Evaluation cases JSON",
        value=_starter_cases(),
        height=300,
        help="Each case may include question, expected_files, expected_answer_keywords, and tags.",
        key="evaluation_cases_json",
    )

    control_columns = st.columns(4)
    with control_columns[0]:
        mode = st.selectbox("Mode", ["retrieval", "rag"], key="evaluation_mode")
    with control_columns[1]:
        top_k = st.slider("Top K", 1, 15, 5, key="evaluation_top_k")
    with control_columns[2]:
        candidate_k = st.slider("Candidate K", 5, 50, 15, key="evaluation_candidate_k")
    with control_columns[3]:
        strategy = st.selectbox(
            "Retrieval strategy",
            ["mmr", "similarity"],
            key="evaluation_strategy",
        )

    threshold_columns = st.columns(2)
    with threshold_columns[0]:
        min_similarity = st.slider(
            "Minimum similarity",
            0.0,
            1.0,
            0.0,
            0.05,
            key="evaluation_min_similarity",
        )
    with threshold_columns[1]:
        keyword_threshold = st.slider(
            "Keyword match threshold",
            0.0,
            1.0,
            0.5,
            0.05,
            key="evaluation_keyword_threshold",
        )

    validation_error = validate_candidate_k(top_k, candidate_k)
    if validation_error:
        st.error(validation_error)
        return

    if mode == "rag":
        st.warning("RAG mode calls the local LLM once for every case and can take several minutes.")

    if st.button("Run evaluation", type="primary", key="evaluation_run"):
        try:
            cases = parse_json_list(raw_cases)
            with st.spinner("Running evaluation cases..."):
                response = run_evaluation(
                    project_id,
                    cases,
                    mode,
                    top_k,
                    candidate_k,
                    min_similarity,
                    strategy,
                    keyword_threshold,
                )
                set_last_result("evaluation", response)
                add_activity("Evaluation completed", f"{len(cases)} cases in {mode} mode")
            st.success("Evaluation completed.")
        except json.JSONDecodeError as error:
            st.error("The evaluation JSON is invalid.")
            st.caption(str(error))
        except ValueError as error:
            st.error(str(error))
        except APIClientError as error:
            render_api_error(error)

    response = get_last_result("evaluation")
    if not response:
        return

    summary = response.get("summary", {})
    metric_columns = st.columns(5)
    metric_columns[0].metric("Cases", summary.get("total_cases", 0))
    metric_columns[1].metric("Passed", summary.get("passed_cases", 0))
    metric_columns[2].metric("Failed", summary.get("failed_cases", 0))
    metric_columns[3].metric("Pass rate", format_percentage(summary.get("pass_rate")))
    metric_columns[4].metric(
        "Retrieval hit rate",
        format_percentage(summary.get("retrieval_hit_rate")),
    )

    rows = []
    for result in response.get("results", []):
        rows.append(
            {
                "case_id": result.get("case_id"),
                "passed": result.get("passed"),
                "retrieval_hit": result.get("retrieval_hit"),
                "chunks_used": result.get("chunks_used"),
                "top_similarity": result.get("top_similarity"),
                "keyword_coverage": result.get("keyword_coverage"),
                "confidence": result.get("confidence"),
            }
        )

    st.subheader("Case results")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    for result in response.get("results", []):
        status = "PASS" if result.get("passed") else "FAIL"
        with st.expander(
            f"{status} | {result.get('case_id')} | {result.get('question')}",
            expanded=not bool(result.get("passed")),
        ):
            failure_reasons = result.get("failure_reasons", [])
            if failure_reasons:
                st.markdown("#### Failure reasons")
                for reason in failure_reasons:
                    st.write(f"- {reason}")

            if result.get("answer"):
                st.markdown("#### Generated answer")
                st.write(result.get("answer"))

            st.markdown("#### Retrieved source files")
            source_files = result.get("source_files", [])
            if source_files:
                for file_path in source_files:
                    st.write(f"- `{file_path}`")
            else:
                st.write("None")

            st.json(result.get("diagnostics", {}))

    result_json = json.dumps(response, indent=2)
    st.download_button(
        "Download evaluation JSON",
        data=result_json.encode("utf-8"),
        file_name="rag_evaluation_results.json",
        mime="application/json",
        key="evaluation_download",
    )
    render_json_debug(response)
