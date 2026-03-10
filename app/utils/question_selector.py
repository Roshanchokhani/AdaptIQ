"""
Adaptive question selection via b-matching.

For the 1PL model, Fisher information I(theta) = P*(1-P) is maximized when
the item difficulty b equals the student's current ability theta. Therefore,
selecting the item with difficulty closest to theta maximizes information gain
per question — this is the "b-matching" or "maximum information" CAT strategy.
"""

from typing import Optional
from app.models.question import Question


def select_next_question(
    current_ability: float,
    available_questions: list[Question],
) -> Optional[Question]:
    """
    Select the question whose difficulty is closest to the student's current ability.

    Args:
        current_ability:     Student's current theta estimate.
        available_questions: Questions not yet answered in this session.

    Returns:
        The most informative question, or None if the list is empty.
    """
    if not available_questions:
        return None

    return min(
        available_questions,
        key=lambda q: abs(q.difficulty - current_ability),
    )
