from fastapi import APIRouter

router = APIRouter()


@router.get("/evaluation/status")
def evaluation_status():
    return {"module": "evaluation", "status": "ready"}