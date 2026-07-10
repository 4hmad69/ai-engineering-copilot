from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.components.badges import render_status_badge
from frontend.utils.session import get_active_project_record


def render_active_project_summary() -> None:
    record = get_active_project_record()

    if not record:
        st.caption("No project record loaded.")
        return

    st.caption(record.get("original_filename", "Unnamed project"))
    render_status_badge(record.get("status", "unknown"))

    column_a, column_b = st.columns(2)
    column_a.metric("Documents", record.get("documents_count", 0))
    column_b.metric("Chunks", record.get("chunks_count", 0))


def project_metric(record: dict[str, Any] | None, key: str, default: Any = 0) -> Any:
    if not record:
        return default

    return record.get(key, default)
