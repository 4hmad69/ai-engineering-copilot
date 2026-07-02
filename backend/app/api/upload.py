from fastapi import APIRouter

router = APIRouter()


@router.get("/upload/status")
def upload_status():
    return {"module": "upload", "status": "ready"}