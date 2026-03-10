from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.question import PyObjectId


class QuestionAttempt(BaseModel):
    question_id: str
    difficulty: float
    topic: str
    is_correct: bool
    ability_before: float
    ability_after: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StudyPlan(BaseModel):
    assessment: str
    steps: list[dict]


class UserSession(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    user_id: str
    current_ability: float
    attempts: list[QuestionAttempt] = []
    answered_question_ids: list[str] = []
    is_complete: bool = False
    study_plan: Optional[StudyPlan] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


class SessionCreate(BaseModel):
    user_id: str


class AnswerSubmit(BaseModel):
    question_id: str
    answer: str


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    ability_before: float
    ability_after: float
    questions_answered: int
    session_complete: bool
    study_plan: Optional[StudyPlan] = None
