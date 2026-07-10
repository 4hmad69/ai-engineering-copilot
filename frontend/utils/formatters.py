from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def format_number(value: Any, default: str = "0") -> str:
    if value is None:
        return default

    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")

    return str(value)


def format_percentage(value: Any) -> str:
    if value is None:
        return "N/A"

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)

    return f"{numeric * 100:.1f}%"


def truncate(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""

    cleaned = " ".join(value.split())

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[: limit - 3].rstrip() + "..."


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
