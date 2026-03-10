from fastapi import APIRouter
from app.api.v1.endpoints import questions, sessions

router = APIRouter(prefix="/api/v1")
router.include_router(questions.router)
router.include_router(sessions.router)
