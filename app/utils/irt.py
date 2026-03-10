"""
1PL (Rasch) Item Response Theory implementation.

The Rasch model defines the probability of a correct response as:

    P(correct | theta, b) = 1 / (1 + exp(-(theta - b)))

where:
    theta  = student ability estimate (0.1 to 1.0)
    b      = item difficulty parameter (0.1 to 1.0)

Ability is updated via a gradient ascent step on the log-likelihood:

    dL/dtheta = response - P(correct | theta, b)

This is equivalent to a single Newton-Raphson step and is mathematically
equivalent to the score equation of the Rasch model.
"""

import math
from app.config import settings


def probability_correct(theta: float, b: float) -> float:
    """
    Probability of a correct response given ability theta and item difficulty b.

    Uses the 1PL (Rasch) logistic model.
    """
    return 1.0 / (1.0 + math.exp(-(theta - b)))


def update_ability(theta: float, b: float, is_correct: bool, learning_rate: float = 0.3) -> float:
    """
    Update ability estimate using gradient ascent on the Rasch log-likelihood.

    The gradient (score function) is:
        dL/dtheta = response - P(correct | theta, b)

    When correct:   gradient > 0  → theta increases
    When incorrect: gradient < 0  → theta decreases
    The magnitude is largest when the item is well-targeted (P ≈ 0.5).

    Args:
        theta:         Current ability estimate.
        b:             Item difficulty (IRT b-parameter).
        is_correct:    Whether the student answered correctly.
        learning_rate: Step size for the gradient update.

    Returns:
        Updated ability clamped to [ABILITY_MIN, ABILITY_MAX].
    """
    p = probability_correct(theta, b)
    response = 1.0 if is_correct else 0.0
    gradient = response - p
    new_theta = theta + learning_rate * gradient
    return max(settings.ABILITY_MIN, min(settings.ABILITY_MAX, new_theta))


def fisher_information(theta: float, b: float) -> float:
    """
    Fisher information for the 1PL model at ability theta for item difficulty b.

    I(theta) = P(correct) * (1 - P(correct))

    Maximized when theta == b (P = 0.5). Used to verify that b-matching
    selects the most informative item.
    """
    p = probability_correct(theta, b)
    return p * (1.0 - p)
