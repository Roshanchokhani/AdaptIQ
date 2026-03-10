from typing import Optional
from fastapi import APIRouter, status
from app.models.question import Question, QuestionCreate
from app.services import question_service

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_question(data: QuestionCreate) -> dict:
    question_id = await question_service.create_question(data)
    return {"id": question_id, "message": "Question created successfully."}


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_questions() -> dict:
    count = await question_service.seed_questions()
    if count == 0:
        return {"message": "Questions already seeded. No new questions added."}
    return {"message": f"Successfully seeded {count} questions."}


@router.get("/", response_model=list[Question])
async def list_questions(
    topic: Optional[str] = None,
    min_difficulty: Optional[float] = None,
    max_difficulty: Optional[float] = None,
) -> list[Question]:
    return await question_service.list_questions(topic, min_difficulty, max_difficulty)


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str) -> Question:
    return await question_service.get_question_by_id(question_id)


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
async def delete_question(question_id: str) -> dict:
    await question_service.delete_question(question_id)
    return {"message": f"Question '{question_id}' deleted."}
