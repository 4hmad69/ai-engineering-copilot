from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.schemas.rag_schema import RAGRetrievalDiagnostics, RetrievalStrategy

DocumentationType = Literal["readme", "architecture", "api", "onboarding"]


class DocumentationRequest(BaseModel):
    documentation_type: DocumentationType = Field(default="readme")
    audience: str = Field(
        default="developers",
        min_length=3,
        max_length=200,
        description="Target audience, for example developers, recruiters, maintainers, or new contributors.",
    )
    extra_instructions: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional documentation instructions.",
    )
    top_k: int = Field(default=8, ge=1, le=15)
    candidate_k: int | None = Field(default=25, ge=5, le=50)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_strategy: RetrievalStrategy = Field(default="mmr")

    @model_validator(mode="after")
    def validate_candidate_k(self) -> "DocumentationRequest":
        if self.candidate_k is not None and self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")

        return self


class DocumentationSection(BaseModel):
    title: str
    content: str

    @field_validator("title", "content", mode="before")
    @classmethod
    def stringify_value(cls, value: Any) -> str:
        if value is None:
            return ""

        return str(value)


class DocumentationSource(BaseModel):
    source_id: int
    chunk_id: str
    file_path: str
    file_type: str
    lines: str
    similarity_score: float
    reason_used: str
    content_preview: str


class DocumentationLLMResponse(BaseModel):
    title: str
    summary: str
    missing_context: bool = False
    sections: list[DocumentationSection] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_markdown: str | None = None
    source_ids: list[int] = Field(default_factory=list)
    source_reasons: dict[str, str] = Field(default_factory=dict)

    @field_validator("sections", mode="before")
    @classmethod
    def normalize_sections(cls, value: Any) -> list[dict[str, str]]:
        if value is None:
            return []

        if not isinstance(value, list):
            return [
                {
                    "title": "Generated Documentation",
                    "content": str(value),
                }
            ]

        normalized_sections: list[dict[str, str]] = []

        for index, item in enumerate(value, start=1):
            if item is None:
                continue

            if isinstance(item, str):
                normalized_sections.append(
                    {
                        "title": f"Section {index}",
                        "content": item,
                    }
                )
                continue

            if isinstance(item, dict):
                normalized_sections.append(
                    {
                        "title": str(item.get("title") or f"Section {index}"),
                        "content": str(item.get("content") or item.get("body") or ""),
                    }
                )
                continue

            normalized_sections.append(
                {
                    "title": f"Section {index}",
                    "content": str(item),
                }
            )

        return normalized_sections


class DocumentationResponse(BaseModel):
    project_id: str
    documentation_type: DocumentationType
    audience: str
    title: str
    summary: str
    missing_context: bool
    sections: list[DocumentationSection]
    warnings: list[str]
    generated_markdown: str
    sources: list[DocumentationSource]
    model: str
    diagnostics: RAGRetrievalDiagnostics
