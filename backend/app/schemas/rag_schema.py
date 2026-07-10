from typing import Literal

from pydantic import BaseModel, Field, model_validator

ConfidenceLevel = Literal["high", "medium", "low"]
RetrievalStrategy = Literal["similarity", "mmr"]


class RAGAnswerRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=15)
    candidate_k: int | None = Field(
        default=None,
        ge=5,
        le=50,
        description="Number of candidate chunks to retrieve before final selection.",
    )
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_strategy: RetrievalStrategy = Field(
        default="mmr",
        description="Retrieval strategy: similarity or mmr.",
    )

    @model_validator(mode="after")
    def validate_candidate_k(self) -> "RAGAnswerRequest":
        if self.candidate_k is not None and self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")

        return self


class RAGSource(BaseModel):
    source_id: int
    chunk_id: str
    file_path: str
    file_type: str
    lines: str
    similarity_score: float
    reason_used: str
    content_preview: str


class RAGRetrievalDiagnostics(BaseModel):
    retrieval_strategy: RetrievalStrategy
    candidates_considered: int
    chunks_used: int
    top_similarity: float | None
    average_similarity: float | None
    min_similarity_applied: float


class RAGAnswerResponse(BaseModel):
    project_id: str
    question: str
    answer: str
    confidence: ConfidenceLevel
    missing_context: bool
    sources: list[RAGSource]
    follow_up_questions: list[str]
    model: str
    diagnostics: RAGRetrievalDiagnostics


class LLMRAGAnswer(BaseModel):
    answer: str = Field(..., min_length=1)
    confidence: ConfidenceLevel
    missing_context: bool
    source_ids: list[int] = Field(default_factory=list)
    source_reasons: dict[str, str] = Field(default_factory=dict)
    follow_up_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_missing_context(self) -> "LLMRAGAnswer":
        if self.missing_context and self.confidence == "high":
            self.confidence = "low"

        return self
