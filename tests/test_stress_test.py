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


class TestRunStressTest:
    def test_missing_cards_and_vague_cards_have_distinct_ids(self):
        from unittest.mock import patch
        from engine.schemas import StressIssue, StressResult
        from engine.stress_test import run_stress_test

        sow_text = "We will make minor adjustments as needed."
        facts = SOWFacts(
            pages=["Home"],
            deliverables=["Website"],
            revision_rounds=None,  # Missing
            deadline=None,         # Missing
            excluded=["Hosting"],
            payment_terms="50/50",
            client_responsibilities=["Assets"],
        )
        mock_llm_result = StressResult(issues=[
            StressIssue(
                quote="minor adjustments",
                kind="vague",
                why_risky="Ambiguous limit",
                freelancer_reading="few tweaks",
                client_reading="endless changes",
                severity="high",
                suggested_rewrite="Up to 2 tweaks",
            )
        ])
        with patch("engine.stress_test.call_json", return_value=mock_llm_result):
            issues, ids = run_stress_test(sow_text, facts)

        # Check that missing issues (M1, M2) and in-text issue (A1) are present
        assert any(id.startswith("M") for id in ids)
        assert any(id.startswith("A") for id in ids)
        assert len(issues) == len(ids)

        missing_issues = [iss for iss in issues if iss.kind == "missing"]
        vague_issues = [iss for iss in issues if iss.kind != "missing"]

        assert len(missing_issues) == 2  # revision_rounds and deadline
        assert len(vague_issues) >= 1    # "minor adjustments"

