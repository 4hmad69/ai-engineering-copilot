import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.schemas.rag_schema import RAGRetrievalDiagnostics, RetrievalStrategy


ComplexityLevel = Literal["low", "medium", "high"]

API_CHANGE_STRING_PATTERN = re.compile(
    r"endpoint=['\"](?P<endpoint>[^'\"]+)['\"]\s+"
    r"method=['\"](?P<method>[^'\"]+)['\"]\s+"
    r"description=['\"](?P<description>[^'\"]+)['\"]"
)


class FeaturePlanRequest(BaseModel):
    feature_request: str = Field(..., min_length=10, max_length=4000)
    planning_focus: str | None = Field(
        default=None,
        max_length=700,
        description=(
            "Optional planning focus, such as security, database design, "
            "tests, or API design."
        ),
    )
    top_k: int = Field(default=7, ge=1, le=15)
    candidate_k: int | None = Field(default=25, ge=5, le=50)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_strategy: RetrievalStrategy = Field(default="mmr")

    @model_validator(mode="after")
    def validate_candidate_k(self) -> "FeaturePlanRequest":
        if self.candidate_k is not None and self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")

        return self


class AffectedFilePlan(BaseModel):
    file_path: str
    reason: str
    change_type: Literal["create", "modify", "review", "unknown"]


class ImplementationStep(BaseModel):
    step_number: int
    title: str
    description: str
    expected_files: list[str] = Field(default_factory=list)


class DatabaseChangePlan(BaseModel):
    change: str
    reason: str | None = None


class APIChangePlan(BaseModel):
    endpoint: str | None = None
    method: str | None = None
    description: str

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, value: Any) -> str | None:
        if value is None:
            return None

        normalized_method = str(value).strip().upper()

        return normalized_method or None


class PlannerSource(BaseModel):
    source_id: int
    chunk_id: str
    file_path: str
    file_type: str
    lines: str
    similarity_score: float
    reason_used: str
    content_preview: str


def _parse_api_change_string(value: str) -> dict[str, Any]:
    cleaned_value = value.strip()

    match = API_CHANGE_STRING_PATTERN.search(cleaned_value)

    if match:
        return {
            "endpoint": match.group("endpoint"),
            "method": match.group("method"),
            "description": match.group("description"),
        }

    return {
        "endpoint": None,
        "method": None,
        "description": cleaned_value,
    }


class FeaturePlanBase(BaseModel):
    feature_summary: str
    affected_files: list[AffectedFilePlan] = Field(default_factory=list)
    implementation_steps: list[ImplementationStep] = Field(default_factory=list)
    database_changes: list[DatabaseChangePlan] = Field(default_factory=list)
    api_changes: list[APIChangePlan] = Field(default_factory=list)
    tests_to_write: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    estimated_complexity: ComplexityLevel

    @field_validator("database_changes", mode="before")
    @classmethod
    def normalize_database_changes(cls, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []

        if not isinstance(value, list):
            return [{"change": str(value)}]

        normalized_changes: list[dict[str, Any]] = []

        for item in value:
            if item is None:
                continue

            if isinstance(item, str):
                normalized_changes.append({"change": item})
                continue

            if isinstance(item, dict):
                if "change" in item:
                    normalized_changes.append(item)
                    continue

                description = item.get("description") or item.get("reason")

                if description:
                    normalized_changes.append(
                        {
                            "change": str(description),
                            "reason": item.get("reason"),
                        }
                    )
                    continue

                normalized_changes.append(
                    {
                        "change": json.dumps(item, ensure_ascii=False),
                    }
                )
                continue

            normalized_changes.append({"change": str(item)})

        return normalized_changes

    @field_validator("api_changes", mode="before")
    @classmethod
    def normalize_api_changes(cls, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []

        if not isinstance(value, list):
            return [_parse_api_change_string(str(value))]

        normalized_changes: list[dict[str, Any]] = []

        for item in value:
            if item is None:
                continue

            if isinstance(item, str):
                normalized_changes.append(_parse_api_change_string(item))
                continue

            if isinstance(item, dict):
                endpoint = item.get("endpoint")
                method = item.get("method")
                description = (
                    item.get("description")
                    or item.get("change")
                    or item.get("reason")
                    or json.dumps(item, ensure_ascii=False)
                )

                normalized_changes.append(
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "description": str(description),
                    }
                )
                continue

            normalized_changes.append(_parse_api_change_string(str(item)))

        return normalized_changes


class FeaturePlanLLMResponse(FeaturePlanBase):
    source_ids: list[int] = Field(default_factory=list)
    source_reasons: dict[str, str] = Field(default_factory=dict)


class FeaturePlanResponse(FeaturePlanBase):
    project_id: str
    feature_request: str
    sources: list[PlannerSource]
    model: str
    diagnostics: RAGRetrievalDiagnostics