from fastapi import APIRouter, status
from app.models.session import SessionCreate, AnswerSubmit, AnswerResponse, UserSession
from app.models.question import QuestionPublic
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(data: SessionCreate) -> dict:
    session_id = await session_service.create_session(data.user_id)
    return {"session_id": session_id, "message": "Session created. Call GET /next to begin."}


@router.get("/{session_id}/next", response_model=QuestionPublic)
async def get_next_question(session_id: str) -> QuestionPublic:
    return await session_service.get_next_question(session_id)


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, data: AnswerSubmit) -> AnswerResponse:
    return await session_service.submit_answer(session_id, data.question_id, data.answer)


@router.get("/{session_id}/status", response_model=UserSession)
async def get_session_status(session_id: str) -> UserSession:
    return await session_service.get_session_status(session_id)
