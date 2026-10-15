"""
tests/test_lexicon.py
Unit tests for engine/lexicon.py — regex-based vague phrase scanner.
No LLM calls.
"""
import pytest
from engine.lexicon import scan, matches_lexicon, LexiconHit


class TestScan:
    def test_detects_minor_revisions(self):
        """'minor revisions' should be flagged as high severity."""
        text = "The project includes minor revisions as requested."
        hits = scan(text)
        assert len(hits) >= 1
        tags = [h.tag for h in hits]
        severities = [h.severity for h in hits]
        assert "high" in severities

    def test_detects_a_few(self):
        text = "Delivered in a few weeks."
        hits = scan(text)
        assert any(h.severity == "high" for h in hits)

    def test_detects_unlimited(self):
        text = "Unlimited revisions are included."
        hits = scan(text)
        assert any(h.tag == "no_limit" for h in hits)

    def test_detects_etc(self):
        text = "Includes lead management, reporting, etc."
        hits = scan(text)
        assert len(hits) >= 1

    def test_clean_sow_returns_few_hits(self):
        """A tight, specific SOW should return 0-1 hits."""
        text = (
            "The project includes 5 pages: Home, Menu, About, Gallery, Contact. "
            "Two rounds of revisions are included. Additional work billed at $50/hour. "
            "Excluded: e-commerce, admin dashboard, CMS integration. "
            "Delivery by December 1, 2026."
        )
        hits = scan(text)
        # A tight SOW should have at most 1 hit (or zero)
        assert len(hits) <= 1

    def test_no_duplicate_overlapping_spans(self):
        """Overlapping patterns should not produce duplicate hits."""
        text = "minor revisions as needed"
        hits = scan(text)
        # Check no two hits overlap
        for i in range(len(hits) - 1):
            assert hits[i].end <= hits[i + 1].start, "Overlapping hits found"

    def test_case_insensitive(self):
        """Pattern matching should be case-insensitive."""
        text = "MINOR REVISIONS will be included."
        hits = scan(text)
        assert len(hits) >= 1

    def test_hit_quote_in_source(self):
        """Every hit's quote must actually appear in the source text."""
        text = "unlimited support is included as needed."
        hits = scan(text)
        for hit in hits:
            assert hit.quote.lower() in text.lower()


class TestMatchesLexicon:
    def test_vague_text_returns_true(self):
        assert matches_lexicon("minor revisions included") is True

    def test_tight_text_returns_false(self):
        assert matches_lexicon("Two revision rounds, each submitted in one email.") is False

    def test_empty_text(self):
        assert matches_lexicon("") is False
