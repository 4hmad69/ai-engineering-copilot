from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from frontend.utils.formatters import format_number


def render_metric_card(
    label: str,
    value: Any,
    helper: str | None = None,
) -> None:
    helper_html = f'<div class="metric-helper">{escape(helper)}</div>' if helper else ""
    st.markdown(
        f"""
        <div class="metric-shell">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(format_number(value))}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="surface-card">
            <div class="surface-title">{escape(title)}</div>
            <div class="surface-copy">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
