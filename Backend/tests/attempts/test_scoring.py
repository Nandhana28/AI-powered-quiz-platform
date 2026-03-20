import pytest
from services.scoring_service import calculate_xp


class TestCalculateXp:
    def test_easy_multiplier(self):
        assert calculate_xp(100, 'easy') == 100

    def test_medium_multiplier(self):
        assert calculate_xp(100, 'medium') == 150

    def test_hard_multiplier(self):
        assert calculate_xp(100, 'hard') == 200

    def test_zero_score(self):
        assert calculate_xp(0, 'easy') == 0

    def test_partial_score(self):
        assert calculate_xp(60, 'medium') == 90
