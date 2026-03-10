"""
Unit tests for the IRT (Item Response Theory) module.

These tests are pure math — no database or network required.
"""

import math
import pytest
from app.utils.irt import probability_correct, update_ability, fisher_information


class TestProbabilityCorrect:
    def test_equal_ability_difficulty_gives_0_5(self):
        """When theta == b, probability should be exactly 0.5."""
        assert probability_correct(0.5, 0.5) == pytest.approx(0.5)

    def test_higher_ability_gives_probability_above_0_5(self):
        """Student more able than difficulty → P > 0.5."""
        p = probability_correct(0.8, 0.3)
        assert p > 0.5

    def test_lower_ability_gives_probability_below_0_5(self):
        """Student less able than difficulty → P < 0.5."""
        p = probability_correct(0.2, 0.9)
        assert p < 0.5

    def test_probability_range(self):
        """Probability must always be in (0, 1)."""
        for theta in [0.1, 0.5, 1.0]:
            for b in [0.1, 0.5, 1.0]:
                p = probability_correct(theta, b)
                assert 0.0 < p < 1.0

    def test_symmetry(self):
        """P(theta, b) + P(b, theta) should equal 1.0 (logistic symmetry)."""
        p1 = probability_correct(0.7, 0.3)
        p2 = probability_correct(0.3, 0.7)
        assert p1 + p2 == pytest.approx(1.0)


class TestUpdateAbility:
    def test_correct_answer_increases_ability(self):
        """A correct answer should raise ability estimate."""
        new_theta = update_ability(0.5, 0.5, is_correct=True)
        assert new_theta > 0.5

    def test_incorrect_answer_decreases_ability(self):
        """An incorrect answer should lower ability estimate."""
        new_theta = update_ability(0.5, 0.5, is_correct=False)
        assert new_theta < 0.5

    def test_correct_on_easy_question_small_increase(self):
        """Correct on easy question (theta >> b) → small ability increase."""
        easy_increase = update_ability(0.9, 0.2, is_correct=True) - 0.9
        hard_increase = update_ability(0.5, 0.5, is_correct=True) - 0.5
        assert easy_increase < hard_increase

    def test_ability_clamped_at_minimum(self):
        """Ability should not drop below ABILITY_MIN (0.1)."""
        new_theta = update_ability(0.1, 0.9, is_correct=False, learning_rate=1.0)
        assert new_theta >= 0.1

    def test_ability_clamped_at_maximum(self):
        """Ability should not exceed ABILITY_MAX (1.0)."""
        new_theta = update_ability(1.0, 0.1, is_correct=True, learning_rate=1.0)
        assert new_theta <= 1.0


class TestFisherInformation:
    def test_max_information_at_equal_ability_difficulty(self):
        """Information is maximized when theta == b."""
        info_at_match = fisher_information(0.5, 0.5)
        info_off_match = fisher_information(0.9, 0.5)
        assert info_at_match > info_off_match

    def test_information_max_is_0_25(self):
        """Maximum Fisher information for 1PL is P*(1-P) = 0.5*0.5 = 0.25."""
        info = fisher_information(0.5, 0.5)
        assert info == pytest.approx(0.25)

    def test_information_is_positive(self):
        """Fisher information is always positive."""
        for theta in [0.1, 0.5, 1.0]:
            for b in [0.1, 0.5, 1.0]:
                assert fisher_information(theta, b) > 0
