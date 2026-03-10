from typing import Any
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)


class Question(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    text: str
    options: dict[str, str]
    correct_answer: str
    difficulty: float
    topic: str
    tags: list[str]
    explanation: str

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: float) -> float:
        if not (0.1 <= v <= 1.0):
            raise ValueError("difficulty must be between 0.1 and 1.0")
        return v

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: str, info: Any) -> str:
        return v.upper()

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


class QuestionCreate(BaseModel):
    text: str
    options: dict[str, str]
    correct_answer: str
    difficulty: float
    topic: str
    tags: list[str]
    explanation: str


class QuestionPublic(BaseModel):
    """Question model without the correct_answer — safe to send to the client."""
    id: str
    text: str
    options: dict[str, str]
    difficulty: float
    topic: str
    tags: list[str]
