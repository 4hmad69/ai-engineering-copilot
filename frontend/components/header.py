from __future__ import annotations

from html import escape

import streamlit as st


def render_page_header(title: str, subtitle: str, kicker: str = "AI workspace") -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-kicker">{escape(kicker)}</div>
            <h1 class="hero-title">{escape(title)}</h1>
            <div class="hero-subtitle">{escape(subtitle)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
