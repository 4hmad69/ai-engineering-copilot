import streamlit as st


PROJECT_ID_KEY = "active_project_id"
PROJECT_RECORD_KEY = "active_project_record"


def initialize_state() -> None:
    if PROJECT_ID_KEY not in st.session_state:
        st.session_state[PROJECT_ID_KEY] = ""

    if PROJECT_RECORD_KEY not in st.session_state:
        st.session_state[PROJECT_RECORD_KEY] = None


def get_active_project_id() -> str:
    return str(st.session_state.get(PROJECT_ID_KEY, "")).strip()


def set_active_project_id(project_id: str) -> None:
    st.session_state[PROJECT_ID_KEY] = project_id.strip()


def get_active_project_record():
    return st.session_state.get(PROJECT_RECORD_KEY)


def set_active_project_record(record) -> None:
    st.session_state[PROJECT_RECORD_KEY] = record


def clear_active_project() -> None:
    st.session_state[PROJECT_ID_KEY] = ""
    st.session_state[PROJECT_RECORD_KEY] = None