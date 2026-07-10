import json
import re
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from backend.app.config import Settings
from backend.app.core.exceptions import LLMProviderError
from backend.app.schemas.rag_schema import LLMRAGAnswer

JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_text)

        if not isinstance(parsed, dict):
            raise LLMProviderError(
                "LLM response JSON was not an object.",
                details={
                    "raw_response_preview": raw_text[:500],
                },
            )

        return parsed

    except json.JSONDecodeError:
        match = JSON_OBJECT_PATTERN.search(raw_text)

        if match is None:
            raise LLMProviderError(
                "LLM did not return valid JSON.",
                details={
                    "raw_response_preview": raw_text[:500],
                },
            ) from None

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                "LLM returned malformed JSON.",
                details={
                    "raw_response_preview": raw_text[:500],
                },
            ) from exc

        if not isinstance(parsed, dict):
            raise LLMProviderError(
                "LLM response JSON was not an object.",
                details={
                    "raw_response_preview": raw_text[:500],
                },
            ) from None

        return parsed


def validate_json_response[TModel: BaseModel](
    raw_response: str,
    response_model: type[TModel],
) -> TModel:
    parsed_json = _extract_json_object(raw_response)

    try:
        return response_model.model_validate(parsed_json)

    except ValidationError as exc:
        raise LLMProviderError(
            "LLM response did not match the required schema.",
            details={
                "validation_errors": exc.errors(),
                "raw_response_preview": raw_response[:700],
            },
        ) from exc


def _build_json_repair_prompt(raw_response: str) -> str:
    return f"""
The previous response did not match the required JSON schema.

Repair it into valid JSON only.

Previous response:
{raw_response[:2500]}

Return only valid JSON.
"""


def _build_ollama_timeout(settings: Settings) -> httpx.Timeout:
    return httpx.Timeout(
        connect=10.0,
        read=float(settings.ollama_timeout_seconds),
        write=30.0,
        pool=10.0,
    )


async def call_ollama_chat(
    system_prompt: str,
    user_prompt: str,
    settings: Settings,
) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    payload = {
        "model": settings.ollama_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": user_prompt.strip(),
            },
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": settings.llm_temperature,
        },
    }

    timeout = _build_ollama_timeout(settings)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise LLMProviderError(
            "Ollama request timed out. The model may be too slow for the current prompt size.",
            details={
                "ollama_base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "timeout_seconds": settings.ollama_timeout_seconds,
                "hint": (
                    "Increase OLLAMA_TIMEOUT_SECONDS, reduce top_k or candidate_k, "
                    "reduce RAG_MAX_CONTEXT_CHARACTERS, or use a smaller model."
                ),
                "error_type": exc.__class__.__name__,
            },
        ) from exc

    except httpx.ConnectError as exc:
        raise LLMProviderError(
            "Could not connect to Ollama. Make sure Ollama is running.",
            details={
                "ollama_base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "hint": "Run: ollama serve",
                "error_type": exc.__class__.__name__,
            },
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise LLMProviderError(
            "Ollama returned an HTTP error.",
            details={
                "ollama_base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "status_code": exc.response.status_code,
                "response_preview": exc.response.text[:700],
                "hint": f"Run: ollama pull {settings.ollama_model}",
                "error_type": exc.__class__.__name__,
            },
        ) from exc

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

    try:
        data = response.json()
    except ValueError as exc:
        raise LLMProviderError(
            "Ollama returned a non-JSON HTTP response.",
            details={
                "response_preview": response.text[:700],
                "model": settings.ollama_model,
            },
        ) from exc

    if not isinstance(data, dict):
        raise LLMProviderError(
            "Ollama returned an unexpected response structure.",
            details={
                "response_preview": str(data)[:700],
                "model": settings.ollama_model,
            },
        )

    message = data.get("message", {})

    if not isinstance(message, dict):
        raise LLMProviderError(
            "Ollama response did not contain a valid message object.",
            details={
                "response_preview": str(data)[:700],
                "model": settings.ollama_model,
            },
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise LLMProviderError(
            "Ollama returned an empty response.",
            details={
                "model": settings.ollama_model,
                "response_preview": str(data)[:700],
            },
        )

    return content.strip()


async def generate_structured_response[TModel: BaseModel](
    system_prompt: str,
    user_prompt: str,
    response_model: type[TModel],
    settings: Settings,
) -> TModel:
    raw_response = await call_ollama_chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        settings=settings,
    )

    try:
        return validate_json_response(
            raw_response=raw_response,
            response_model=response_model,
        )

    except LLMProviderError:
        repair_response = await call_ollama_chat(
            system_prompt=(
                "You repair malformed JSON responses. "
                "Return only valid JSON matching the schema described by the user."
            ),
            user_prompt=_build_json_repair_prompt(raw_response),
            settings=settings,
        )

        return validate_json_response(
            raw_response=repair_response,
            response_model=response_model,
        )


async def generate_structured_rag_answer(
    system_prompt: str,
    user_prompt: str,
    settings: Settings,
) -> LLMRAGAnswer:
    return await generate_structured_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=LLMRAGAnswer,
        settings=settings,
    )
