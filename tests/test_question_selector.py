"""
Unit tests for the adaptive question selector.
"""

import pytest
from app.models.question import Question
from app.utils.question_selector import select_next_question


def make_question(difficulty: float, topic: str = "Math") -> Question:
    return Question(
        _id="507f1f77bcf86cd799439011",
        text="Sample question",
        options={"A": "1", "B": "2", "C": "3", "D": "4"},
        correct_answer="A",
        difficulty=difficulty,
        topic=topic,
        tags=["test"],
        explanation="Explanation.",
    )


class TestSelectNextQuestion:
    def test_returns_none_for_empty_list(self):
        assert select_next_question(0.5, []) is None

    def test_selects_closest_difficulty(self):
        questions = [make_question(0.2), make_question(0.5), make_question(0.9)]
        selected = select_next_question(0.5, questions)
        assert selected is not None
        assert selected.difficulty == 0.5

    def test_selects_closest_when_exact_match_absent(self):
        questions = [make_question(0.3), make_question(0.7)]
        selected = select_next_question(0.5, questions)
        assert selected is not None
        # Both are equidistant — either is valid, just not None
        assert selected.difficulty in [0.3, 0.7]

    def test_selects_only_available_question(self):
        questions = [make_question(0.8)]
        selected = select_next_question(0.1, questions)
        assert selected is not None
        assert selected.difficulty == 0.8

    def test_selects_hardest_when_ability_is_max(self):
        questions = [make_question(0.2), make_question(0.6), make_question(0.95)]
        selected = select_next_question(1.0, questions)
        assert selected is not None
        assert selected.difficulty == 0.95
