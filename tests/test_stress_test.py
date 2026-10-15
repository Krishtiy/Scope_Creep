"""
tests/test_stress_test.py
Unit tests for deterministic parts of engine/stress_test.py:
- _missing_cards generation from null SOWFacts fields
- Severity ranking
All tests run with no LLM calls.
"""
import pytest
from engine.schemas import SOWFacts
from engine.stress_test import _missing_cards, _severity_rank


class TestMissingCards:
    def test_missing_pages_and_deliverables_generates_high_card(self):
        facts = SOWFacts(
            pages=[],
            deliverables=[],
            revision_rounds=2,
            excluded=["Hosting"],
            deadline="Nov 1",
            payment_terms="50/50",
            client_responsibilities=["Assets"],
        )
        cards = _missing_cards(facts)
        kinds = [c.kind for c in cards]
        assert all(k == "missing" for k in kinds)
        why = " ".join(c.why_risky for c in cards)
        assert "No list of pages or deliverables" in why

    def test_missing_revision_rounds_generates_high_card(self):
        facts = SOWFacts(
            pages=["Home", "About"],
            deliverables=["Website"],
            revision_rounds=None,
            excluded=["SEO"],
            deadline="Nov 1",
            payment_terms="Net 30",
            client_responsibilities=["Copy"],
        )
        cards = _missing_cards(facts)
        assert len(cards) == 1
        assert cards[0].severity == "high"
        assert "No revision limit" in cards[0].why_risky

    def test_completely_empty_sowfacts_generates_all_templates(self):
        facts = SOWFacts()
        cards = _missing_cards(facts)
        # Should generate multiple cards for missing items
        assert len(cards) >= 5

    def test_complete_sowfacts_generates_zero_missing_cards(self):
        facts = SOWFacts(
            pages=["Home"],
            deliverables=["Design"],
            revision_rounds=2,
            excluded=["Hosting"],
            deadline="2026-12-01",
            payment_terms="50/50",
            client_responsibilities=["Feedback within 48h"],
        )
        cards = _missing_cards(facts)
        assert len(cards) == 0


class TestSeverityRanking:
    def test_ranking_order(self):
        assert _severity_rank("high") < _severity_rank("medium")
        assert _severity_rank("medium") < _severity_rank("low")
        assert _severity_rank("low") < _severity_rank("unknown")
