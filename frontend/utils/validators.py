from __future__ import annotations

import json
from typing import Any


def validate_project_id(project_id: str) -> str | None:
    if not project_id.strip():
        return "Upload a project or enter a project ID first."

    return None


def validate_min_length(value: str, label: str, minimum: int) -> str | None:
    if len(value.strip()) < minimum:
        return f"{label} must contain at least {minimum} characters."

    return None


def validate_candidate_k(top_k: int, candidate_k: int) -> str | None:
    if candidate_k < top_k:
        return "Candidate K must be greater than or equal to Top K."

    return None


def parse_json_list(raw_value: str) -> list[dict[str, Any]]:
    parsed = json.loads(raw_value)

    if isinstance(parsed, dict):
        parsed = parsed.get("cases", [])

    if not isinstance(parsed, list):
        raise ValueError("Evaluation input must be a JSON list of cases.")

    if not parsed:
        raise ValueError("Add at least one evaluation case.")

    invalid_items = [index for index, item in enumerate(parsed) if not isinstance(item, dict)]

    if invalid_items:
        raise ValueError("Every evaluation case must be a JSON object.")

    return parsed
