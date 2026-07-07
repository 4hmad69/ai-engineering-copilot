from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.planner_schema import FeaturePlanRequest, FeaturePlanResponse
from backend.app.services.feature_planner_service import create_feature_plan

router = APIRouter()


@router.get("/planner/status")
def planner_status():
    return {"module": "planner", "status": "ready"}


@router.post(
    "/planner/feature/{project_id}",
    response_model=FeaturePlanResponse,
)
async def plan_feature(
    project_id: str,
    request: FeaturePlanRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> FeaturePlanResponse:
    return await create_feature_plan(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )