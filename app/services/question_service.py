import json
import os
from typing import Optional
from bson import ObjectId
from app.core.database import get_db
from app.core.exceptions import QuestionNotFoundError
from app.models.question import Question, QuestionCreate


async def create_question(data: QuestionCreate) -> str:
    db = get_db()
    doc = data.model_dump()
    doc["correct_answer"] = doc["correct_answer"].upper()
    result = await db["questions"].insert_one(doc)
    return str(result.inserted_id)


async def get_question_by_id(question_id: str) -> Question:
    db = get_db()
    doc = await db["questions"].find_one({"_id": ObjectId(question_id)})
    if not doc:
        raise QuestionNotFoundError(question_id)
    return Question.model_validate(doc)


async def list_questions(
    topic: Optional[str] = None,
    min_difficulty: Optional[float] = None,
    max_difficulty: Optional[float] = None,
) -> list[Question]:
    db = get_db()
    query: dict = {}
    if topic:
        query["topic"] = topic
    if min_difficulty is not None or max_difficulty is not None:
        query["difficulty"] = {}
        if min_difficulty is not None:
            query["difficulty"]["$gte"] = min_difficulty
        if max_difficulty is not None:
            query["difficulty"]["$lte"] = max_difficulty

    cursor = db["questions"].find(query)
    docs = await cursor.to_list(length=None)
    return [Question.model_validate(doc) for doc in docs]


async def get_available_questions(excluded_ids: list[str]) -> list[Question]:
    """Fetch all questions not yet answered in the current session."""
    db = get_db()
    excluded_object_ids = [ObjectId(eid) for eid in excluded_ids]
    cursor = db["questions"].find({"_id": {"$nin": excluded_object_ids}})
    docs = await cursor.to_list(length=None)
    return [Question.model_validate(doc) for doc in docs]


async def delete_question(question_id: str) -> bool:
    db = get_db()
    result = await db["questions"].delete_one({"_id": ObjectId(question_id)})
    if result.deleted_count == 0:
        raise QuestionNotFoundError(question_id)
    return True


async def seed_questions() -> int:
    """Load questions from data/seed_questions.json and insert into MongoDB."""
    db = get_db()

    seed_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed_questions.json")
    seed_path = os.path.normpath(seed_path)

    with open(seed_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in questions:
        q["correct_answer"] = q["correct_answer"].upper()

    existing_count = await db["questions"].count_documents({})
    if existing_count > 0:
        return 0

    result = await db["questions"].insert_many(questions)
    return len(result.inserted_ids)


async def ensure_indexes() -> None:
    db = get_db()
    await db["questions"].create_index([("difficulty", 1), ("topic", 1)])
    await db["user_sessions"].create_index([("user_id", 1)])
    await db["user_sessions"].create_index([("is_complete", 1)])
