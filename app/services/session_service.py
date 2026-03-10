"""
Session Service — orchestrates the adaptive testing loop.

All session state transitions flow through this module:
  create_session → get_next_question → submit_answer (repeat) → complete
"""

from datetime import datetime
from bson import ObjectId
from app.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    SessionNotFoundError,
    SessionCompleteError,
    DuplicateAnswerError,
    NoQuestionsAvailableError,
)
from app.models.session import UserSession, QuestionAttempt, AnswerResponse, StudyPlan
from app.models.question import Question, QuestionPublic
from app.services import question_service
from app.services import insight_service
from app.utils.irt import update_ability
from app.utils.question_selector import select_next_question


async def _get_session(session_id: str) -> tuple[UserSession, dict]:
    """Fetch raw session doc and parse into UserSession model."""
    db = get_db()
    doc = await db["user_sessions"].find_one({"_id": ObjectId(session_id)})
    if not doc:
        raise SessionNotFoundError(session_id)
    return UserSession.model_validate(doc), doc


async def create_session(user_id: str) -> str:
    """Create a new adaptive testing session for the given user."""
    db = get_db()
    doc = {
        "user_id": user_id,
        "current_ability": settings.ABILITY_INITIAL,
        "attempts": [],
        "answered_question_ids": [],
        "is_complete": False,
        "study_plan": None,
        "started_at": datetime.utcnow(),
        "completed_at": None,
    }
    result = await db["user_sessions"].insert_one(doc)
    return str(result.inserted_id)


async def get_next_question(session_id: str) -> QuestionPublic:
    """
    Select the most informative next question for the student's current ability.

    Uses b-matching: picks the unanswered question whose difficulty is closest
    to the student's current theta.
    """
    session, _ = await _get_session(session_id)

    if session.is_complete:
        raise SessionCompleteError()

    available = await question_service.get_available_questions(session.answered_question_ids)
    next_q = select_next_question(session.current_ability, available)

    if next_q is None:
        raise NoQuestionsAvailableError()

    return QuestionPublic(
        id=str(next_q.id),
        text=next_q.text,
        options=next_q.options,
        difficulty=next_q.difficulty,
        topic=next_q.topic,
        tags=next_q.tags,
    )


async def submit_answer(session_id: str, question_id: str, answer: str) -> AnswerResponse:
    """
    Process a student's answer and update session state.

    Steps:
      1. Validate session is active and question hasn't been answered.
      2. Determine correctness.
      3. Update ability via IRT gradient step.
      4. Persist the attempt to MongoDB atomically.
      5. Trigger AI insights after AI_INSIGHT_TRIGGER answers.
      6. Mark session complete after MAX_QUESTIONS_PER_SESSION answers.
    """
    db = get_db()
    session, _ = await _get_session(session_id)

    if session.is_complete:
        raise SessionCompleteError()

    if question_id in session.answered_question_ids:
        raise DuplicateAnswerError(question_id)

    question = await question_service.get_question_by_id(question_id)

    is_correct = answer.upper() == question.correct_answer
    ability_before = session.current_ability
    ability_after = update_ability(ability_before, question.difficulty, is_correct)

    attempt = QuestionAttempt(
        question_id=question_id,
        difficulty=question.difficulty,
        topic=question.topic,
        is_correct=is_correct,
        ability_before=ability_before,
        ability_after=ability_after,
    )

    updated_attempts = session.attempts + [attempt]
    updated_answered_ids = session.answered_question_ids + [question_id]
    questions_answered = len(updated_attempts)

    is_complete = questions_answered >= settings.MAX_QUESTIONS_PER_SESSION
    completed_at = datetime.utcnow() if is_complete else None

    update_doc: dict = {
        "$set": {
            "current_ability": ability_after,
            "is_complete": is_complete,
            "completed_at": completed_at,
        },
        "$push": {
            "attempts": attempt.model_dump(),
            "answered_question_ids": question_id,
        },
    }

    await db["user_sessions"].update_one({"_id": ObjectId(session_id)}, update_doc)

    study_plan: StudyPlan | None = None

    if questions_answered == settings.AI_INSIGHT_TRIGGER:
        study_plan = await insight_service.generate_study_plan(updated_attempts, ability_after)
        await db["user_sessions"].update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"study_plan": study_plan.model_dump()}},
        )

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        ability_before=ability_before,
        ability_after=ability_after,
        questions_answered=questions_answered,
        session_complete=is_complete,
        study_plan=study_plan,
    )


async def get_session_status(session_id: str) -> UserSession:
    """Return full session state including study plan if generated."""
    session, _ = await _get_session(session_id)
    return session
