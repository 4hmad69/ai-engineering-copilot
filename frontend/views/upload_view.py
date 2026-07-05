import streamlit as st

from frontend.api_client import APIClientError, get_project_record, upload_codebase
from frontend.state import set_active_project_id, set_active_project_record
from frontend.ui import show_api_error, show_success_response


def render_upload_view() -> None:
    st.header("1. Upload Codebase")
    st.write("Upload a zipped codebase. The backend will save it, safely extract it, and create a project record.")

    uploaded_file = st.file_uploader(
        "Upload ZIP file",
        type=["zip"],
        accept_multiple_files=False,
        help="Upload a ZIP archive of the codebase you want to analyze.",
    )

    if uploaded_file is None:
        st.info("Upload a ZIP file to start.")
        return

    st.caption(f"Selected file: {uploaded_file.name}")

    if st.button("Upload and Create Project", type="primary"):
        try:
            with st.spinner("Uploading and extracting codebase..."):
                upload_response = upload_codebase(
                    filename=uploaded_file.name,
                    content=uploaded_file.getvalue(),
                )

                project_id = str(upload_response["project_id"])
                project_record = get_project_record(project_id)

                set_active_project_id(project_id)
                set_active_project_record(project_record)

            show_success_response(
                title="Codebase uploaded successfully.",
                payload=upload_response,
            )

            st.info(f"Active project ID: `{project_id}`")

        except APIClientError as error:
            show_api_error(error)