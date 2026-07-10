from __future__ import annotations

import streamlit as st

from frontend.components.empty_states import render_project_required
from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_sources
from frontend.services.api_client import APIClientError, rag_chat
from frontend.utils.session import (
    add_activity,
    append_chat_message,
    clear_chat_history,
    get_active_project_id,
    get_chat_history,
)
from frontend.utils.validators import validate_candidate_k


def _render_message_metadata(metadata: dict) -> None:
    if not metadata:
        return

    with st.expander("Answer evidence and diagnostics", expanded=False):
        metric_columns = st.columns(3)
        metric_columns[0].metric("Confidence", metadata.get("confidence", "unknown"))
        metric_columns[1].metric("Missing context", metadata.get("missing_context", False))
        metric_columns[2].metric("Model", metadata.get("model", "unknown"))

        sources = metadata.get("sources", [])
        if sources:
            render_sources(sources, heading="Supporting sources")

        diagnostics = metadata.get("diagnostics")
        if diagnostics:
            st.markdown("#### Retrieval diagnostics")
            st.json(diagnostics)


def render_rag_chat() -> None:
    render_page_header(
        "RAG Chat",
        "Ask grounded questions about an indexed codebase. Every answer is generated from retrieved project context and includes traceable evidence.",
        kicker="Grounded conversation",
    )

    project_id = get_active_project_id()
    if not project_id:
        render_project_required()
        return

    with st.expander("Retrieval controls", expanded=False):
        control_columns = st.columns(4)
        with control_columns[0]:
            top_k = st.slider("Top K", 1, 15, 5, key="rag_chat_top_k")
        with control_columns[1]:
            candidate_k = st.slider("Candidate K", 5, 50, 15, key="rag_chat_candidate_k")
        with control_columns[2]:
            min_similarity = st.slider(
                "Minimum similarity",
                0.0,
                1.0,
                0.0,
                0.05,
                key="rag_chat_min_similarity",
            )
        with control_columns[3]:
            strategy = st.selectbox(
                "Retrieval strategy",
                ["mmr", "similarity"],
                key="rag_chat_strategy",
            )

        if st.button("Clear conversation", key="rag_chat_clear"):
            clear_chat_history()
            st.rerun()

    validation_error = validate_candidate_k(top_k, candidate_k)
    if validation_error:
        st.error(validation_error)
        return

    history = get_chat_history()
    if not history:
        st.info(
            "Try asking: What does this project do? Where is authentication implemented? How does the database session work?"
        )

    for message in history:
        role = message.get("role", "assistant")
        avatar = "user" if role == "user" else "assistant"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message.get("content", ""))
            if role == "assistant":
                _render_message_metadata(message.get("metadata", {}))

    question = st.chat_input(
        "Ask about architecture, files, functions, APIs, bugs, or implementation details..."
    )

    if not question:
        return

    append_chat_message("user", question)

    try:
        with st.spinner("Retrieving project context and generating a grounded answer..."):
            response = rag_chat(
                project_id,
                question,
                top_k,
                candidate_k,
                min_similarity,
                strategy,
            )

        append_chat_message(
            "assistant",
            response.get("answer", "No answer was returned."),
            metadata=response,
        )
        add_activity("RAG question answered", question[:90])
        st.rerun()
    except APIClientError as error:
        render_api_error(error)
