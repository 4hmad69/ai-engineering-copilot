from fastapi import APIRouter

router = APIRouter()


@router.get("/chat/status")
def chat_status():
    return {"module": "chat", "status": "ready"}