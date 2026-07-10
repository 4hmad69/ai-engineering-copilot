from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.schemas.rag_schema import RAGAnswerRequest, RAGAnswerResponse
from backend.app.services.rag_answer_service import answer_project_question_with_rag

router = APIRouter()


@router.get("/chat/status")
def chat_status():
    return {"module": "chat", "status": "ready"}


@router.post(
    "/chat/rag/{project_id}",
    response_model=RAGAnswerResponse,
)
async def ask_project_question_with_rag(
    project_id: str,
    request: RAGAnswerRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
) -> RAGAnswerResponse:
    return await answer_project_question_with_rag(
        project_id=project_id,
        request=request,
        settings=settings,
        session=session,
    )
