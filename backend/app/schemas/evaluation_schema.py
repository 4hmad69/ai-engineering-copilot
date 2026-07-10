from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.schemas.rag_schema import (
    ConfidenceLevel,
    RAGRetrievalDiagnostics,
    RetrievalStrategy,
)

EvaluationMode = Literal["retrieval", "rag"]


class EvaluationCase(BaseModel):
    case_id: str | None = Field(default=None, max_length=80)
    question: str = Field(..., min_length=3, max_length=2000)
    expected_files: list[str] = Field(default_factory=list)
    expected_answer_keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator(
        "expected_files",
        "expected_answer_keywords",
        "tags",
        mode="before",
    )
    @classmethod
    def normalize_string_list(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            return [value]

        return value


class EvaluationRunRequest(BaseModel):
    cases: list[EvaluationCase] = Field(..., min_length=1, max_length=20)
    mode: EvaluationMode = Field(
        default="retrieval",
        description="retrieval is faster; rag also generates answers using the LLM.",
    )
    top_k: int = Field(default=5, ge=1, le=15)
    candidate_k: int | None = Field(default=15, ge=5, le=50)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_strategy: RetrievalStrategy = Field(default="mmr")
    keyword_match_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_candidate_k(self) -> "EvaluationRunRequest":
        if self.candidate_k is not None and self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")

        return self


class EvaluationCaseResult(BaseModel):
    case_id: str
    question: str
    tags: list[str]

    mode: EvaluationMode
    passed: bool
    failure_reasons: list[str]

    expected_files: list[str]
    expected_files_found: list[str]
    expected_files_missing: list[str]
    retrieval_hit: bool | None

    source_files: list[str]
    chunks_used: int
    top_similarity: float | None
    average_similarity: float | None

    answer: str | None = None
    confidence: ConfidenceLevel | None = None
    missing_context: bool | None = None
    keyword_coverage: float | None = None
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)

    diagnostics: RAGRetrievalDiagnostics


class EvaluationSummary(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    retrieval_hit_rate: float | None
    average_top_similarity: float | None
    average_keyword_coverage: float | None
    generated_answers_count: int


class EvaluationRunResponse(BaseModel):
    project_id: str
    mode: EvaluationMode
    summary: EvaluationSummary
    results: list[EvaluationCaseResult]
