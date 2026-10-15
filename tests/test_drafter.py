"""
tests/test_drafter.py
Unit tests for engine/drafter.py:
- Number guard extraction and validation
- Change-order block formatting
- Fallback plain template generation
All tests run deterministically with no LLM calls.
"""
import pytest
from engine.schemas import Decision
from engine.drafter import (
    _extract_numbers_from_text,
    _build_allowed_numbers,
    _guard_numbers,
    _build_change_order,
    _fallback_reply,
)


def _make_decision(
    text: str = "Add a contact form",
    verdict: str = "out_of_scope",
    hours: float = 4.0,
    price: float = 100.0,
    consumes_revision: bool = False,
) -> Decision:
    return Decision(
        request_text=text,
        final_verdict=verdict,
        llm_verdict=verdict,
        rule_ids=["R2"],
        overridden_by_rule=False,
        sow_quote=None,
        client_quote=text,
        quote_methods={"sow": "none", "client": "exact"},
        linked_ambiguity=None,
        consumes_revision=consumes_revision,
        confidence="high",
        hours=hours,
        price=price,
    )


class TestNumberGuard:
    def test_extract_numbers(self):
        text = "This project will take 4.5 hours and cost $150 or 2 rounds of review."
        nums = _extract_numbers_from_text(text)
        assert nums == {"4.5", "150", "2"}

    def test_build_allowed_numbers(self):
        d1 = _make_decision(hours=4.0, price=100.0, consumes_revision=True)
        d2 = _make_decision(hours=2.5, price=62.5, consumes_revision=False)
        allowed = _build_allowed_numbers([d1, d2], rate=25.0)

        # Hours
        assert "4.0" in allowed or "4" in allowed
        assert "2.5" in allowed
        # Prices
        assert "100.0" in allowed or "100" in allowed
        assert "62.5" in allowed
        # Rate
        assert "25.0" in allowed or "25" in allowed
        # Revision count
        assert "1" in allowed

    def test_guard_numbers_passes_when_all_allowed(self):
        allowed = {"4", "100", "25"}
        text = "This will take 4 hours at $25/hr for a total of $100."
        assert _guard_numbers(text, allowed) is True

    def test_guard_numbers_fails_when_hallucinated_number(self):
        allowed = {"4", "100", "25"}
        # 500 is hallucinated
        text = "This will take 4 hours at $25/hr for a total of $500."
        assert _guard_numbers(text, allowed) is False


class TestChangeOrder:
    def test_build_change_order_multiple_items(self):
        d1 = _make_decision("New blog page", "out_of_scope", hours=4.0, price=100.0)
        d2 = _make_decision("SEO audit", "out_of_scope", hours=3.0, price=75.0)
        co = _build_change_order([d1, d2], order_num=1)

        assert "**Change Order #1**" in co
        assert "New blog page" in co
        assert "Estimated hours: 4.0" in co
        assert "Cost: $100.00" in co
        assert "SEO audit" in co
        assert "Estimated hours: 3.0" in co
        assert "Cost: $75.00" in co
        assert "Total estimated: 7.0h / $175.00" in co
        assert 'Reply "APPROVED" to proceed.' in co

    def test_build_change_order_empty_when_no_out_of_scope(self):
        d1 = _make_decision("Fix typo", "in_scope", hours=0.5, price=12.5)
        d2 = _make_decision("Clarify palette", "gray_area", hours=1.0, price=25.0)
        co = _build_change_order([d1, d2], order_num=1)
        assert co == ""


class TestFallbackReply:
    def test_fallback_handles_all_verdicts(self):
        d1 = _make_decision("Add blog", "out_of_scope", hours=4.0, price=100.0)
        d2 = _make_decision("Fix typo", "in_scope", hours=0.5, price=12.5)
        d3 = _make_decision("Redo layout", "gray_area", hours=2.0, price=50.0)

        reply = _fallback_reply([d1, d2, d3], tone="friendly")
        assert "Fix typo" in reply
        assert "within scope" in reply
        assert "Add blog" in reply
        assert "outside the original agreement" in reply
        assert "Redo layout" in reply
        assert "need clarification" in reply
