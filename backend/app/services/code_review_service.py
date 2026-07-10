from backend.app.config import Settings
from backend.app.prompts.review_prompt import SYSTEM_PROMPT, build_review_prompt
from backend.app.schemas.review_schema import (
    CodeReviewLLMResponse,
    CodeReviewRequest,
    CodeReviewResponse,
)
from backend.app.services.llm_service import generate_structured_response


async def review_code_or_diff(
    request: CodeReviewRequest,
    settings: Settings,
) -> CodeReviewResponse:
    user_prompt = build_review_prompt(
        code_or_diff=request.code_or_diff,
        review_focus=request.review_focus,
    )

    llm_review = await generate_structured_response(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=CodeReviewLLMResponse,
        settings=settings,
    )

    return CodeReviewResponse(
        summary=llm_review.summary,
        overall_risk=llm_review.overall_risk,
        issues=llm_review.issues,
        missing_tests=llm_review.missing_tests,
        recommended_actions=llm_review.recommended_actions,
        positive_notes=llm_review.positive_notes,
        model=settings.ollama_model,
    )
