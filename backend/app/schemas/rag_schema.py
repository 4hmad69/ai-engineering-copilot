from typing import Literal

from pydantic import BaseModel, Field, model_validator


ConfidenceLevel = Literal["high", "medium", "low"]


class RAGAnswerRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=15)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGSource(BaseModel):
    chunk_id: str
    file_path: str
    file_type: str
    lines: str
    similarity_score: float
    reason_used: str
    content_preview: str


class RAGAnswerResponse(BaseModel):
    project_id: str
    question: str
    answer: str
    confidence: ConfidenceLevel
    missing_context: bool
    sources: list[RAGSource]
    follow_up_questions: list[str]
    model: str


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