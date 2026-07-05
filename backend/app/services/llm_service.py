import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from backend.app.config import Settings
from backend.app.core.exceptions import LLMProviderError
from backend.app.schemas.rag_schema import LLMRAGAnswer

JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_text)

        if not isinstance(parsed, dict):
            raise ValueError("LLM response JSON was not an object.")

        return parsed

    except json.JSONDecodeError:
        match = JSON_OBJECT_PATTERN.search(raw_text)

        if match is None:
            raise LLMProviderError(
                "LLM did not return valid JSON.",
                details={"raw_response_preview": raw_text[:500]},
            )

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                "LLM returned malformed JSON.",
                details={"raw_response_preview": raw_text[:500]},
            ) from exc

        if not isinstance(parsed, dict):
            raise LLMProviderError(
                "LLM response JSON was not an object.",
                details={"raw_response_preview": raw_text[:500]},
            )

        return parsed


async def call_ollama_chat(
    system_prompt: str,
    user_prompt: str,
    settings: Settings,
) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": settings.llm_temperature,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise LLMProviderError(
            "Failed to call Ollama. Make sure Ollama is running and the model is available.",
            details={
                "ollama_base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "hint": f"Run: ollama pull {settings.ollama_model}",
                "error_type": exc.__class__.__name__,
            },
        ) from exc

    data = response.json()

    message = data.get("message", {})
    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise LLMProviderError(
            "Ollama returned an empty response.",
            details={"model": settings.ollama_model},
        )

    return content


async def generate_structured_rag_answer(
    system_prompt: str,
    user_prompt: str,
    settings: Settings,
) -> LLMRAGAnswer:
    raw_response = await call_ollama_chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        settings=settings,
    )

    parsed_json = _extract_json_object(raw_response)

    try:
        return LLMRAGAnswer.model_validate(parsed_json)

    except ValidationError as exc:
        raise LLMProviderError(
            "LLM response did not match the required RAG answer schema.",
            details={
                "validation_errors": exc.errors(),
                "raw_response_preview": raw_response[:700],
            },
        ) from exc