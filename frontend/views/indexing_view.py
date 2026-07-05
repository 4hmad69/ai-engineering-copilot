import streamlit as st

from frontend.api_client import (
    APIClientError,
    get_project_files,
    get_project_record,
    index_embeddings,
    persist_chunks,
    preview_chunks,
)
from frontend.state import (
    get_active_project_id,
    set_active_project_id,
    set_active_project_record,
)
from frontend.ui import (
    render_project_id_input,
    render_project_summary,
    show_api_error,
    show_success_response,
)


def render_indexing_view() -> None:
    st.header("2. Prepare Index")
    st.write("Inspect files, preview chunks, persist chunks, and generate embeddings.")

    current_project_id = get_active_project_id()
    project_id = render_project_id_input(
    current_project_id=current_project_id,
    widget_key="indexing_project_id_input",
)

    if project_id != current_project_id:
        set_active_project_id(project_id)

    if not project_id:
        st.warning("Upload a project first or paste a project ID.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        chunk_size_lines = st.slider(
            "Chunk size in lines",
            min_value=20,
            max_value=250,
            value=80,
            step=10,
        )

    with col_b:
        overlap_lines = st.slider(
            "Overlap lines",
            min_value=0,
            max_value=80,
            value=12,
            step=2,
        )

    if overlap_lines >= chunk_size_lines:
        st.error("Overlap lines must be smaller than chunk size.")
        return

    st.divider()

    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

    with action_col1:
        if st.button("Load Project Record"):
            try:
                record = get_project_record(project_id)
                set_active_project_record(record)
                render_project_summary(record)
            except APIClientError as error:
                show_api_error(error)

    with action_col2:
        if st.button("Inspect Files"):
            try:
                with st.spinner("Inspecting project files..."):
                    files_response = get_project_files(project_id)

                show_success_response("File inspection completed.", files_response)

                loadable = files_response.get("loadable_files_count", 0)
                skipped = files_response.get("skipped_files_count", 0)

                st.metric("Loadable files", loadable)
                st.metric("Skipped files", skipped)

            except APIClientError as error:
                show_api_error(error)

    with action_col3:
        if st.button("Preview Chunks"):
            try:
                with st.spinner("Preparing chunk preview..."):
                    preview_response = preview_chunks(
                        project_id=project_id,
                        chunk_size_lines=chunk_size_lines,
                        overlap_lines=overlap_lines,
                    )

                show_success_response("Chunk preview created.", preview_response)
                st.metric("Chunks", preview_response.get("chunks_count", 0))

            except APIClientError as error:
                show_api_error(error)

    with action_col4:
        if st.button("Persist Chunks", type="primary"):
            try:
                with st.spinner("Persisting documents and chunks..."):
                    persist_response = persist_chunks(
                        project_id=project_id,
                        chunk_size_lines=chunk_size_lines,
                        overlap_lines=overlap_lines,
                    )

                    record = get_project_record(project_id)
                    set_active_project_record(record)

                show_success_response("Chunks persisted successfully.", persist_response)
                render_project_summary(record)

            except APIClientError as error:
                show_api_error(error)

    st.divider()

    if st.button("Generate Embeddings", type="primary"):
        try:
            with st.spinner("Generating embeddings. First run may take longer because the model may download."):
                embedding_response = index_embeddings(project_id)
                record = get_project_record(project_id)
                set_active_project_record(record)

            show_success_response("Embeddings generated successfully.", embedding_response)
            render_project_summary(record)

        except APIClientError as error:
            show_api_error(error)