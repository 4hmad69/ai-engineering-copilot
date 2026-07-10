from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.components.header import render_page_header
from frontend.components.renderers import render_api_error, render_json_debug
from frontend.services.api_client import (
    APIClientError,
    get_project_files,
    get_project_record,
    index_embeddings,
    persist_chunks,
    preview_chunks,
    upload_codebase,
)
from frontend.utils.session import (
    add_activity,
    get_active_project_id,
    get_last_result,
    set_active_project_id,
    set_active_project_record,
    set_last_result,
)


def _refresh_project_record(project_id: str) -> dict[str, Any]:
    record = get_project_record(project_id)
    set_active_project_record(record)
    return record


def _render_file_inspection(response: dict[str, Any]) -> None:
    loadable = response.get("loadable_files_count", response.get("supported_files_count", 0))
    skipped = response.get("skipped_files_count", 0)
    columns = st.columns(3)
    columns[0].metric("Loadable files", loadable)
    columns[1].metric("Skipped files", skipped)
    columns[2].metric("Total files", response.get("total_files_count", loadable + skipped))

    files = response.get("files") or response.get("items") or []
    if isinstance(files, list) and files:
        st.dataframe(files[:200], use_container_width=True, hide_index=True)


def render_upload_index() -> None:
    render_page_header(
        "Upload and Index",
        "Create a project record, inspect the extracted repository, persist source chunks, and generate semantic embeddings.",
        kicker="Project ingestion",
    )

    upload_column, existing_column = st.columns([1.05, 0.95])

    with upload_column:
        with st.container(border=True):
            st.subheader("Upload a new codebase")
            uploaded_file = st.file_uploader(
                "ZIP repository",
                type=["zip"],
                accept_multiple_files=False,
                help="Upload a ZIP archive containing the project source code.",
                key="upload_index_zip",
            )

            upload_clicked = st.button(
                "Upload and create project",
                type="primary",
                use_container_width=True,
                key="upload_index_submit",
            )

            if upload_clicked:
                if uploaded_file is None:
                    st.warning("Select a ZIP file first.")
                else:
                    try:
                        with st.spinner("Uploading and safely extracting the repository..."):
                            response = upload_codebase(
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                            )
                            project_id = str(response["project_id"])
                            record = _refresh_project_record(project_id)
                            set_active_project_id(project_id)
                            set_last_result("upload", response)
                            add_activity(
                                "Project uploaded",
                                record.get("original_filename", uploaded_file.name),
                            )

                        st.success("Project created successfully.")
                        st.code(project_id, language="text")
                        render_json_debug(response)
                    except (APIClientError, KeyError) as error:
                        if isinstance(error, APIClientError):
                            render_api_error(error)
                        else:
                            st.error("The upload response did not contain a project ID.")

    with existing_column:
        with st.container(border=True):
            st.subheader("Load an existing project")
            current_project_id = get_active_project_id()
            entered_project_id = st.text_input(
                "Project ID",
                value=current_project_id,
                placeholder="Paste an existing project ID",
                key="upload_index_existing_project",
            )

            if st.button(
                "Load project record",
                use_container_width=True,
                key="upload_index_load_existing",
            ):
                if not entered_project_id.strip():
                    st.warning("Enter a project ID first.")
                else:
                    try:
                        with st.spinner("Loading project record..."):
                            set_active_project_id(entered_project_id)
                            record = _refresh_project_record(entered_project_id)
                            add_activity(
                                "Project loaded",
                                record.get("original_filename", entered_project_id),
                            )
                        st.success("Project loaded.")
                        render_json_debug(record, "Project record")
                    except APIClientError as error:
                        render_api_error(error)

    st.divider()

    project_id = get_active_project_id()
    if not project_id:
        st.info("Upload a codebase or load an existing project to continue.")
        return

    st.subheader("Indexing pipeline")
    settings_columns = st.columns(2)
    with settings_columns[0]:
        chunk_size = st.slider(
            "Chunk size in lines",
            min_value=20,
            max_value=250,
            value=80,
            step=10,
            key="upload_index_chunk_size",
        )
    with settings_columns[1]:
        overlap = st.slider(
            "Chunk overlap in lines",
            min_value=0,
            max_value=80,
            value=12,
            step=2,
            key="upload_index_overlap",
        )

    if overlap >= chunk_size:
        st.error("Chunk overlap must be smaller than chunk size.")
        return

    action_columns = st.columns(4)

    with action_columns[0]:
        inspect_clicked = st.button(
            "1. Inspect files",
            use_container_width=True,
            key="upload_index_inspect",
        )
    with action_columns[1]:
        preview_clicked = st.button(
            "2. Preview chunks",
            use_container_width=True,
            key="upload_index_preview",
        )
    with action_columns[2]:
        persist_clicked = st.button(
            "3. Persist chunks",
            use_container_width=True,
            key="upload_index_persist",
        )
    with action_columns[3]:
        embed_clicked = st.button(
            "4. Generate embeddings",
            type="primary",
            use_container_width=True,
            key="upload_index_embed",
        )

    if inspect_clicked:
        try:
            with st.spinner("Inspecting supported and skipped files..."):
                response = get_project_files(project_id)
                set_last_result("file_inspection", response)
                add_activity("Files inspected", project_id)
            st.success("File inspection completed.")
        except APIClientError as error:
            render_api_error(error)

    if preview_clicked:
        try:
            with st.spinner("Preparing a chunk preview..."):
                response = preview_chunks(project_id, chunk_size, overlap)
                set_last_result("chunk_preview", response)
                add_activity("Chunk preview generated", project_id)
            st.success("Chunk preview generated.")
        except APIClientError as error:
            render_api_error(error)

    if persist_clicked:
        try:
            with st.spinner("Persisting documents and chunks..."):
                response = persist_chunks(project_id, chunk_size, overlap)
                set_last_result("chunk_persist", response)
                _refresh_project_record(project_id)
                add_activity("Chunks persisted", project_id)
            st.success("Documents and chunks were persisted.")
        except APIClientError as error:
            render_api_error(error)

    if embed_clicked:
        try:
            with st.spinner("Generating embeddings. The first run may download the model..."):
                response = index_embeddings(project_id)
                set_last_result("embedding_index", response)
                _refresh_project_record(project_id)
                add_activity("Embeddings generated", project_id)
            st.success("Project embeddings are ready.")
        except APIClientError as error:
            render_api_error(error)

    inspection_result = get_last_result("file_inspection")
    preview_result = get_last_result("chunk_preview")
    persist_result = get_last_result("chunk_persist")
    embedding_result = get_last_result("embedding_index")

    if any([inspection_result, preview_result, persist_result, embedding_result]):
        st.divider()
        result_tabs = st.tabs(["Files", "Chunk preview", "Persistence", "Embeddings"])

        with result_tabs[0]:
            if inspection_result:
                _render_file_inspection(inspection_result)
                render_json_debug(inspection_result)
            else:
                st.info("Run file inspection to populate this tab.")

        with result_tabs[1]:
            if preview_result:
                st.metric("Prepared chunks", preview_result.get("chunks_count", 0))
                chunks = preview_result.get("chunks") or preview_result.get("preview") or []
                if isinstance(chunks, list) and chunks:
                    st.dataframe(chunks[:100], use_container_width=True, hide_index=True)
                render_json_debug(preview_result)
            else:
                st.info("Create a chunk preview to populate this tab.")

        with result_tabs[2]:
            if persist_result:
                st.success("Latest persistence operation completed.")
                render_json_debug(persist_result)
            else:
                st.info("Persist chunks to populate this tab.")

        with result_tabs[3]:
            if embedding_result:
                st.success("Latest embedding operation completed.")
                render_json_debug(embedding_result)
            else:
                st.info("Generate embeddings to populate this tab.")
