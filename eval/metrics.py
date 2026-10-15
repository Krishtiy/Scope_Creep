"""
eval/metrics.py
Metric computation for the evaluation harness.
Works on lists of (predicted_label, gold_label) pairs.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Literal

Label = Literal["in_scope", "out_of_scope", "gray_area", "unverified"]
LABELS = ["in_scope", "out_of_scope", "gray_area"]


def accuracy(predictions: list[str], gold: list[str]) -> float:
    """Overall accuracy."""
    if not gold:
        return 0.0
    return round(sum(p == g for p, g in zip(predictions, gold)) / len(gold), 4)


def false_accusation_rate(predictions: list[str], gold: list[str]) -> float:
    """
    False accusation rate: gold is in_scope or gray_area, predicted out_of_scope.
    This is worse than a miss (accusing an in-scope item of being OOS).
    """
    if not gold:
        return 0.0
    false_acc = sum(
        1 for p, g in zip(predictions, gold)
        if g in ("in_scope", "gray_area") and p == "out_of_scope"
    )
    denom = sum(1 for g in gold if g in ("in_scope", "gray_area"))
    return round(false_acc / denom, 4) if denom else 0.0


def confusion_matrix(predictions: list[str], gold: list[str]) -> dict[str, dict[str, int]]:
    """
    3×3 confusion matrix: {actual: {predicted: count}}.
    Rows = actual, columns = predicted.
    """
    matrix: dict[str, dict[str, int]] = {
        label: {l: 0 for l in LABELS + ["unverified"]}
        for label in LABELS + ["unverified"]
    }
    for p, g in zip(predictions, gold):
        actual = g if g in matrix else "unverified"
        pred   = p if p in matrix[actual] else "unverified"
        matrix[actual][pred] += 1
    return matrix


def per_difficulty(
    predictions: list[str],
    gold: list[str],
    difficulties: list[str],
) -> dict[str, float]:
    """Accuracy split by difficulty (obvious / subtle)."""
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for p, g, d in zip(predictions, gold, difficulties):
        groups[d].append((p, g))
    return {
        diff: round(sum(p == g for p, g in pairs) / len(pairs), 4)
        for diff, pairs in groups.items()
        if pairs
    }


def fabricated_citation_catch_rate(
    quote_methods: list[dict],
    injected_flags: list[bool],
) -> float:
    """
    Fraction of injected fabricated quotes that were correctly flagged.
    quote_methods: list of {"sow": method, "client": method} from decisions.
    injected_flags: True if this decision had a fabricated quote injected.
    """
    injected = [(qm, flag) for qm, flag in zip(quote_methods, injected_flags) if flag]
    if not injected:
        return 1.0
    caught = sum(
        1 for qm, _ in injected
        if qm.get("sow") in ("not_found", "number_mismatch", "too_short")
        or qm.get("client") in ("not_found", "number_mismatch", "too_short")
    )
    return round(caught / len(injected), 4)


def format_confusion_matrix_md(matrix: dict) -> str:
    """Format confusion matrix as a Markdown table."""
    cols = ["in_scope", "out_of_scope", "gray_area", "unverified"]
    header = "| Actual \\ Predicted | " + " | ".join(cols) + " |"
    sep    = "|" + "---|" * (len(cols) + 1)
    rows   = []
    for actual in cols:
        row_vals = [str(matrix.get(actual, {}).get(c, 0)) for c in cols]
        rows.append(f"| {actual} | " + " | ".join(row_vals) + " |")
    return "\n".join([header, sep] + rows)
