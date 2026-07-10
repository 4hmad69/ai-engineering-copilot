from __future__ import annotations

from html import escape

import streamlit as st


def render_badge(label: str, variant: str = "muted") -> None:
    allowed = {"success", "warning", "danger", "info", "muted"}
    safe_variant = variant if variant in allowed else "muted"
    st.markdown(
        f'<span class="status-badge badge-{safe_variant}">{escape(label)}</span>',
        unsafe_allow_html=True,
    )


def render_status_badge(status: str | None) -> None:
    normalized = (status or "unknown").strip().lower()

    if normalized in {"ready", "healthy", "completed", "embedded", "chunked", "ok"}:
        render_badge(status or "healthy", "success")
    elif normalized in {"pending", "processing", "warning", "starting"}:
        render_badge(status or "pending", "warning")
    elif normalized in {"failed", "error", "unhealthy", "down"}:
        render_badge(status or "failed", "danger")
    elif normalized in {"unknown", "none"}:
        render_badge(status or "unknown", "muted")
    else:
        render_badge(status or "active", "info")
