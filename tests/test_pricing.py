"""
tests/test_pricing.py
Unit tests for engine/pricing.py — pure math, no LLM calls.
"""
import pytest
from engine.pricing import estimate_hours, price, summary


class TestEstimateHours:
    def test_new_page_medium(self):
        """new_page, M size = 4 * 1.0 = 4.0h"""
        assert estimate_hours("new_page", "M") == 4.0

    def test_new_page_small(self):
        """new_page, S size = 4 * 0.5 = 2.0h"""
        assert estimate_hours("new_page", "S") == 2.0

    def test_new_page_large(self):
        """new_page, L size = 4 * 2.0 = 8.0h"""
        assert estimate_hours("new_page", "L") == 8.0

    def test_new_feature_large(self):
        """new_feature, L size = 8 * 2.0 = 16.0h"""
        assert estimate_hours("new_feature", "L") == 16.0

    def test_timeline_change(self):
        """timeline_change always 0h"""
        assert estimate_hours("timeline_change", "M") == 0.0

    def test_unknown_type_falls_back_to_other(self):
        """Unknown type falls back to 'other' base hours (2)."""
        assert estimate_hours("unknown_type", "M") == 2.0


class TestPrice:
    def test_basic_price(self):
        assert price(4.0, 25.0) == 100.0

    def test_zero_hours(self):
        assert price(0.0, 25.0) == 0.0

    def test_fractional_hours(self):
        assert price(1.5, 30.0) == 45.0

    def test_rounding(self):
        # Should round to 2 decimal places
        result = price(3.0, 33.33)
        assert result == round(3.0 * 33.33, 2)


class TestSummary:
    def _make_log(self):
        return [
            {"verdict": "out_of_scope", "hours": 4.0, "price": 100.0},
            {"verdict": "in_scope",     "hours": 2.0, "price": 50.0},
            {"verdict": "out_of_scope", "hours": 8.0, "price": 200.0},
            {"verdict": "gray_area",    "hours": 0.0, "price": 0.0},
        ]

    def test_extras_count(self):
        s = summary(self._make_log(), rate=25.0, contract_price=1000.0)
        assert s["extras"] == 2

    def test_total_hours(self):
        s = summary(self._make_log(), rate=25.0, contract_price=1000.0)
        assert s["hours"] == 12.0

    def test_total_value(self):
        s = summary(self._make_log(), rate=25.0, contract_price=1000.0)
        assert s["value"] == 300.0

    def test_pct_over_scope(self):
        # contract_price=1000, rate=25 → baseline=40h. extras=12h → 30%
        s = summary(self._make_log(), rate=25.0, contract_price=1000.0)
        assert s["pct_over_scope"] == 30.0

    def test_empty_log(self):
        s = summary([], rate=25.0, contract_price=1000.0)
        assert s["extras"] == 0
        assert s["hours"] == 0.0
        assert s["value"] == 0.0

    def test_zero_rate_no_crash(self):
        s = summary(self._make_log(), rate=0.0, contract_price=1000.0)
        assert s["pct_over_scope"] is None
