from typing import Literal

from pydantic import BaseModel, Field


ReviewSeverity = Literal["low", "medium", "high", "critical"]
ReviewCategory = Literal[
    "bug",
    "security",
    "performance",
    "maintainability",
    "testing",
    "style",
    "architecture",
    "data_validation",
    "error_handling",
]


class CodeReviewRequest(BaseModel):
    code_or_diff: str = Field(..., min_length=20, max_length=60000)
    review_focus: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Optional review focus, such as security, bugs, tests, "
            "or FastAPI best practices."
        ),
    )


class CodeReviewIssue(BaseModel):
    severity: ReviewSeverity
    category: ReviewCategory
    file_path: str | None = Field(
        default=None,
        description="File path if visible from the diff or pasted code.",
    )
    line_hint: str | None = Field(
        default=None,
        description="Approximate line number or code section.",
    )
    problem: str
    evidence: str
    suggestion: str


class CodeReviewBase(BaseModel):
    summary: str
    overall_risk: Literal["low", "medium", "high", "critical"]
    issues: list[CodeReviewIssue] = Field(default_factory=list)
    missing_tests: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    positive_notes: list[str] = Field(default_factory=list)


class CodeReviewLLMResponse(CodeReviewBase):
    """Exact structure expected from the LLM.

    The LLM should only return review content.
    Runtime metadata, such as model name, is added by the backend.
    """


class CodeReviewResponse(CodeReviewBase):
    model: str