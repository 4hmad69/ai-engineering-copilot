from fastapi import APIRouter

router = APIRouter()


@router.get("/planner/status")
def planner_status():
    return {"module": "planner", "status": "ready"}