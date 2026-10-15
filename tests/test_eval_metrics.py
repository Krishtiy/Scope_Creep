"""
tests/test_eval_metrics.py
Unit tests for eval/metrics.py:
- accuracy calculation
- false_accusation_rate calculation
- confusion_matrix generation
- per_difficulty breakdown
- fabricated_citation_catch_rate
"""
import pytest
from eval.metrics import (
    accuracy,
    false_accusation_rate,
    confusion_matrix,
    per_difficulty,
    fabricated_citation_catch_rate,
    format_confusion_matrix_md,
)


class TestMetrics:
    def test_accuracy_perfect(self):
        preds = ["in_scope", "out_of_scope", "gray_area"]
        gold = ["in_scope", "out_of_scope", "gray_area"]
        assert accuracy(preds, gold) == 1.0

    def test_accuracy_partial(self):
        preds = ["in_scope", "in_scope"]
        gold = ["in_scope", "out_of_scope"]
        assert accuracy(preds, gold) == 0.5

    def test_accuracy_empty(self):
        assert accuracy([], []) == 0.0

    def test_false_accusation_rate(self):
        # False accusation = gold is in_scope or gray_area, but predicted out_of_scope
        preds = ["out_of_scope", "in_scope", "out_of_scope", "gray_area", "out_of_scope"]
        gold  = ["in_scope",     "in_scope", "gray_area",    "gray_area", "out_of_scope"]
        # Total eligible = 4 (gold in_scope or gray_area). Accusations = 2.
        assert false_accusation_rate(preds, gold) == 0.5

    def test_confusion_matrix(self):
        preds = ["in_scope", "out_of_scope", "gray_area"]
        gold  = ["in_scope", "in_scope",     "out_of_scope"]
        cm = confusion_matrix(preds, gold)
        # Rows = actual, columns = predicted
        assert cm["in_scope"]["in_scope"] == 1
        assert cm["in_scope"]["out_of_scope"] == 1
        assert cm["out_of_scope"]["gray_area"] == 1

        md = format_confusion_matrix_md(cm)
        assert "| Actual \\ Predicted |" in md
        assert "| in_scope |" in md

    def test_per_difficulty(self):
        preds = ["in_scope", "out_of_scope", "gray_area"]
        gold  = ["in_scope", "in_scope",     "gray_area"]
        diffs = ["obvious",  "obvious",      "subtle"]

        res = per_difficulty(preds, gold, diffs)
        assert res["obvious"] == 0.5
        assert res["subtle"] == 1.0

    def test_fabricated_citation_catch_rate(self):
        quote_methods = [
            {"sow": "not_found", "client": "exact"},
            {"sow": "exact", "client": "exact"},
            {"sow": "number_mismatch", "client": "fuzzy"},
        ]
        injected = [True, False, True]
        rate = fabricated_citation_catch_rate(quote_methods, injected)
        assert rate == 1.0
