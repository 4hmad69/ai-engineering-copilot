import json

import streamlit as st

from frontend.api_client import APIClientError, run_evaluation
from frontend.state import get_active_project_id, set_active_project_id
from frontend.ui import render_project_id_input, show_api_error


def _default_cases_json() -> str:
    cases = [
        {
            "case_id": "database_session",
            "question": "Where is the database connection created?",
            "expected_files": [
                "backend/app/db/session.py"
            ],
            "expected_answer_keywords": [
                "create_async_engine",
                "async_sessionmaker"
            ],
            "tags": [
                "database",
                "backend"
            ]
        },
        {
            "case_id": "upload_flow",
            "question": "How does codebase upload and extraction work?",
            "expected_files": [
                "backend/app/services/upload_service.py",
                "backend/app/api/upload.py"
            ],
            "expected_answer_keywords": [
                "zip",
                "extract",
                "project_id"
            ],
            "tags": [
                "upload",
                "ingestion"
            ]
        },
        {
            "case_id": "rag_answer",
            "question": "How does the RAG answer flow work?",
            "expected_files": [
                "backend/app/services/rag_answer_service.py",
                "backend/app/services/rag_retrieval_service.py"
            ],
            "expected_answer_keywords": [
                "retrieval",
                "context",
                "answer"
            ],
            "tags": [
                "rag",
                "llm"
            ]
        }
    ]

    return json.dumps(cases, indent=2)


def _parse_cases(raw_cases: str) -> list[dict]:
    parsed = json.loads(raw_cases)

    if isinstance(parsed, dict):
        parsed = parsed.get("cases", [])

    if not isinstance(parsed, list):
        raise ValueError("Evaluation cases must be a JSON list.")

    return parsed


def _render_summary(summary: dict) -> None:
    st.subheader("Evaluation Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Cases", summary.get("total_cases", 0))
    col2.metric("Passed", summary.get("passed_cases", 0))
    col3.metric("Failed", summary.get("failed_cases", 0))
    col4.metric("Pass Rate", summary.get("pass_rate", 0))

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Retrieval Hit Rate", summary.get("retrieval_hit_rate"))
    col6.metric("Avg Top Similarity", summary.get("average_top_similarity"))
    col7.metric("Avg Keyword Coverage", summary.get("average_keyword_coverage"))
    col8.metric("Generated Answers", summary.get("generated_answers_count", 0))


def _render_results_table(results: list[dict]) -> None:
    rows = []

    for result in results:
        rows.append(
            {
                "case_id": result.get("case_id"),
                "passed": result.get("passed"),
                "chunks_used": result.get("chunks_used"),
                "top_similarity": result.get("top_similarity"),
                "retrieval_hit": result.get("retrieval_hit"),
                "keyword_coverage": result.get("keyword_coverage"),
                "confidence": result.get("confidence"),
                "missing_context": result.get("missing_context"),
            }
        )

    st.subheader("Results Table")
    st.dataframe(rows, use_container_width=True)


def _render_case_details(results: list[dict]) -> None:
    st.subheader("Case Details")

    for result in results:
        status = "PASS" if result.get("passed") else "FAIL"
        title = f"{status} | {result.get('case_id')} | {result.get('question')}"

        with st.expander(title, expanded=not result.get("passed", False)):
            failure_reasons = result.get("failure_reasons", [])

            if failure_reasons:
                st.write("Failure reasons:")
                for reason in failure_reasons:
                    st.write(f"- {reason}")

            st.write("Expected files:")
            for file_path in result.get("expected_files", []):
                st.write(f"- `{file_path}`")

            st.write("Expected files found:")
            found_files = result.get("expected_files_found", [])

            if found_files:
                for file_path in found_files:
                    st.write(f"- `{file_path}`")
            else:
                st.write("None.")

            st.write("Source files:")
            source_files = result.get("source_files", [])

            if source_files:
                for file_path in source_files:
                    st.write(f"- `{file_path}`")
            else:
                st.write("None.")

            if result.get("answer"):
                st.write("Generated answer:")
                st.write(result.get("answer"))

            matched_keywords = result.get("matched_keywords", [])
            missing_keywords = result.get("missing_keywords", [])

            if matched_keywords or missing_keywords:
                st.write("Keyword matches:")
                st.json(
                    {
                        "matched": matched_keywords,
                        "missing": missing_keywords,
                        "coverage": result.get("keyword_coverage"),
                    }
                )

            with st.expander("Diagnostics", expanded=False):
                st.json(result.get("diagnostics", {}))


def render_evaluation_view() -> None:
    st.header("8. RAG Evaluation Dashboard")
    st.write(
        "Evaluate retrieval quality and optionally evaluate full RAG answers "
        "against expected files and keywords."
    )

    current_project_id = get_active_project_id()

    project_id = render_project_id_input(
        current_project_id=current_project_id,
        widget_key="evaluation_project_id_input",
    )

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload and index a project first.")
        return

    raw_cases = st.text_area(
        "Evaluation Cases JSON",
        value=_default_cases_json(),
        height=330,
        key="evaluation_cases_input",
        help="Use a JSON list. Each case can include question, expected_files, expected_answer_keywords, and tags.",
    )

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        mode = st.selectbox(
            "Evaluation Mode",
            options=["retrieval", "rag"],
            index=0,
            key="evaluation_mode_select",
        )

    with col_b:
        top_k = st.slider(
            "Top K",
            min_value=1,
            max_value=15,
            value=5,
            key="evaluation_top_k",
        )

    with col_c:
        candidate_k = st.slider(
            "Candidate K",
            min_value=5,
            max_value=50,
            value=15,
            key="evaluation_candidate_k",
        )

    with col_d:
        retrieval_strategy = st.selectbox(
            "Retrieval Strategy",
            options=["mmr", "similarity"],
            index=0,
            key="evaluation_retrieval_strategy",
        )

    col_e, col_f = st.columns(2)

    with col_e:
        min_similarity = st.slider(
            "Min Similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="evaluation_min_similarity",
        )

    with col_f:
        keyword_match_threshold = st.slider(
            "Keyword Match Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            key="evaluation_keyword_threshold",
        )

    if candidate_k < top_k:
        st.error("Candidate K must be greater than or equal to Top K.")
        return

    if mode == "rag":
        st.warning(
            "RAG mode calls the LLM once per case. Use fewer cases if Ollama is slow."
        )

    if st.button("Run Evaluation", type="primary"):
        try:
            cases = _parse_cases(raw_cases)

            with st.spinner("Running evaluation..."):
                response = run_evaluation(
                    project_id=project_id,
                    cases=cases,
                    mode=mode,
                    top_k=top_k,
                    candidate_k=candidate_k,
                    min_similarity=min_similarity,
                    retrieval_strategy=retrieval_strategy,
                    keyword_match_threshold=keyword_match_threshold,
                )

            _render_summary(response.get("summary", {}))
            _render_results_table(response.get("results", []))
            _render_case_details(response.get("results", []))

            with st.expander("Raw response", expanded=False):
                st.json(response)

        except ValueError as error:
            st.error(str(error))

        except json.JSONDecodeError as error:
            st.error("Invalid JSON in evaluation cases.")
            st.caption(str(error))

        except APIClientError as error:
            show_api_error(error)