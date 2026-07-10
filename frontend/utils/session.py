from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.utils.config import get_settings
from frontend.utils.formatters import utc_timestamp

ACTIVE_PROJECT_ID = "active_project_id"
ACTIVE_PROJECT_RECORD = "active_project_record"
NAVIGATION_PAGE = "navigation_page"
CHAT_HISTORY = "rag_chat_history"
ACTIVITY_LOG = "activity_log"
LAST_RESULTS = "last_results"

DEFAULT_PAGE = "Dashboard"


def initialize_session_state() -> None:
    defaults: dict[str, Any] = {
        ACTIVE_PROJECT_ID: "",
        ACTIVE_PROJECT_RECORD: None,
        NAVIGATION_PAGE: DEFAULT_PAGE,
        CHAT_HISTORY: [],
        ACTIVITY_LOG: [],
        LAST_RESULTS: {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate_to(page_name: str) -> None:
    st.session_state[NAVIGATION_PAGE] = page_name


def get_active_project_id() -> str:
    return str(st.session_state.get(ACTIVE_PROJECT_ID, "")).strip()


def set_active_project_id(project_id: str) -> None:
    normalized = project_id.strip()
    previous = get_active_project_id()

    if normalized != previous:
        st.session_state[ACTIVE_PROJECT_RECORD] = None
        st.session_state[CHAT_HISTORY] = []

    st.session_state[ACTIVE_PROJECT_ID] = normalized


def get_active_project_record() -> dict[str, Any] | None:
    record = st.session_state.get(ACTIVE_PROJECT_RECORD)
    return record if isinstance(record, dict) else None


def set_active_project_record(record: dict[str, Any] | None) -> None:
    st.session_state[ACTIVE_PROJECT_RECORD] = record


def clear_active_project() -> None:
    st.session_state[ACTIVE_PROJECT_ID] = ""
    st.session_state[ACTIVE_PROJECT_RECORD] = None
    st.session_state[CHAT_HISTORY] = []


def get_chat_history() -> list[dict[str, Any]]:
    history = st.session_state.get(CHAT_HISTORY, [])
    return history if isinstance(history, list) else []


def append_chat_message(
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    settings = get_settings()
    history = list(get_chat_history())
    history.append(
        {
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
    )
    st.session_state[CHAT_HISTORY] = history[-settings.max_chat_messages :]


def clear_chat_history() -> None:
    st.session_state[CHAT_HISTORY] = []


def add_activity(title: str, detail: str = "") -> None:
    activity = list(st.session_state.get(ACTIVITY_LOG, []))
    activity.insert(
        0,
        {
            "title": title,
            "detail": detail,
            "timestamp": utc_timestamp(),
        },
    )
    st.session_state[ACTIVITY_LOG] = activity[:12]


def get_activity_log() -> list[dict[str, str]]:
    activity = st.session_state.get(ACTIVITY_LOG, [])
    return activity if isinstance(activity, list) else []


def set_last_result(key: str, value: dict[str, Any]) -> None:
    results = dict(st.session_state.get(LAST_RESULTS, {}))
    results[key] = value
    st.session_state[LAST_RESULTS] = results


def get_last_result(key: str) -> dict[str, Any] | None:
    results = st.session_state.get(LAST_RESULTS, {})

    if not isinstance(results, dict):
        return None

    value = results.get(key)
    return value if isinstance(value, dict) else None
