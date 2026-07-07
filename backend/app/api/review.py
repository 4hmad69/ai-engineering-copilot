from fastapi import APIRouter, Depends

from backend.app.config import Settings, get_settings
from backend.app.schemas.review_schema import CodeReviewRequest, CodeReviewResponse
from backend.app.services.code_review_service import review_code_or_diff

router = APIRouter()


@router.get("/review/status")
def review_status():
    return {"module": "review", "status": "ready"}


@router.post(
    "/review/code",
    response_model=CodeReviewResponse,
)
async def review_code(
    request: CodeReviewRequest,
    settings: Settings = Depends(get_settings),
) -> CodeReviewResponse:
    return await review_code_or_diff(
        request=request,
        settings=settings,
    )