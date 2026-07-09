from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.evaluation_schema import (
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from backend.app.services.evaluation_service import run_project_evaluation

router = APIRouter()


@router.get("/evaluation/status")
def evaluation_status():
    return {"module": "evaluation", "status": "ready"}


@router.post(
    "/evaluation/run/{project_id}",
    response_model=EvaluationRunResponse,
)
async def run_evaluation(
    project_id: str,
    request: EvaluationRunRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> EvaluationRunResponse:
    return await run_project_evaluation(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )