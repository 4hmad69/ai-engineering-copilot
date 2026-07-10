from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

FRONTEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(FRONTEND_ROOT / ".env", override=False)


@dataclass(frozen=True, slots=True)
class FrontendSettings:
    app_name: str
    api_base_url: str
    request_timeout_seconds: float
    max_chat_messages: int


@lru_cache(maxsize=1)
def get_settings() -> FrontendSettings:
    return FrontendSettings(
        app_name=os.getenv("FRONTEND_APP_NAME", "AI Engineering Copilot"),
        api_base_url=os.getenv(
            "FRONTEND_API_BASE_URL",
            "http://127.0.0.1:8000/api/v1",
        ).rstrip("/"),
        request_timeout_seconds=float(
            os.getenv("FRONTEND_REQUEST_TIMEOUT_SECONDS", "300")
        ),
        max_chat_messages=max(
            10,
            int(os.getenv("FRONTEND_MAX_CHAT_MESSAGES", "40")),
        ),
    )
