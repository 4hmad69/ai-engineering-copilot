import streamlit as st

from frontend.api_client import APIClientError, rag_chat
from frontend.state import get_active_project_id, set_active_project_id
from frontend.ui import render_project_id_input, render_sources, show_api_error


def render_rag_chat_view() -> None:
    st.header("4. RAG Chat")
    st.write("Ask grounded questions about the uploaded codebase.")

    current_project_id = get_active_project_id()
    project_id = render_project_id_input(
    current_project_id=current_project_id,
    widget_key="rag_chat_project_id_input",
)

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload and index a project first.")
        return

    question = st.text_area(
        "Question",
        value="What does this project do?",
        height=120,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        top_k = st.slider("Top K", min_value=1, max_value=15, value=5)

    with col2:
        candidate_k = st.slider("Candidate K", min_value=5, max_value=50, value=20)

    with col3:
        min_similarity = st.slider(
            "Min Similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
        )

    with col4:
        retrieval_strategy = st.selectbox(
            "Retrieval Strategy",
            options=["mmr", "similarity"],
            index=0,
        )

    if candidate_k < top_k:
        st.error("Candidate K must be greater than or equal to Top K.")
        return

    if st.button("Ask RAG", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
            return

        try:
            with st.spinner("Retrieving context and generating answer..."):
                response = rag_chat(
                    project_id=project_id,
                    question=question,
                    top_k=top_k,
                    candidate_k=candidate_k,
                    min_similarity=min_similarity,
                    retrieval_strategy=retrieval_strategy,
                )

            st.subheader("Answer")
            st.write(response.get("answer", ""))

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Confidence", response.get("confidence", "unknown"))
            metric_col2.metric("Missing Context", str(response.get("missing_context", False)))
            metric_col3.metric("Model", response.get("model", "unknown"))

            diagnostics = response.get("diagnostics", {})
            with st.expander("Retrieval diagnostics", expanded=False):
                st.json(diagnostics)

            st.subheader("Sources")
            render_sources(response.get("sources", []))

            follow_ups = response.get("follow_up_questions", [])
            if follow_ups:
                st.subheader("Follow-up Questions")
                for follow_up in follow_ups:
                    st.write(f"- {follow_up}")

            with st.expander("Raw response", expanded=False):
                st.json(response)

        except APIClientError as error:
            show_api_error(error)