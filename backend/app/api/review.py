from fastapi import APIRouter

router = APIRouter()


@router.get("/review/status")
def review_status():
    return {"module": "review", "status": "ready"}