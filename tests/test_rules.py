"""
tests/test_rules.py
Unit tests for engine/rules.py — deterministic rule engine.
Uses mock MatchResult/SplitRequest objects. No LLM calls.
"""
import pytest
from engine.schemas import SOWFacts, SplitRequest, MatchResult
from engine.rules import decide


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_sow(**kwargs) -> SOWFacts:
    defaults = {
        "pages": ["Home", "About", "Contact"],
        "revision_rounds": 2,
        "revision_definition": "One consolidated batch of changes",
        "deliverables": ["5-page website"],
        "excluded": ["e-commerce", "admin dashboard"],
        "deadline": "December 1, 2026",
        "payment_terms": "50% upfront, 50% on delivery",
    }
    defaults.update(kwargs)
    return SOWFacts(**defaults)


def make_request(**kwargs) -> SplitRequest:
    defaults = {
        "request_text": "add a blog page",
        "type": "new_page",
        "magnitude": "substantial",
    }
    defaults.update(kwargs)
    return SplitRequest(**defaults)


def make_match(**kwargs) -> MatchResult:
    defaults = {
        "verdict": "out_of_scope",
        "sow_quote": None,
        "client_quote": "add a blog page",
        "matched_exclusion": None,
        "consumes_revision": False,
        "size": "M",
        "confidence": "high",
        "reasoning": "Blog page not in listed pages",
    }
    defaults.update(kwargs)
    return MatchResult(**defaults)


# ── R0: Unverifiable quote ────────────────────────────────────────────────────

class TestR0Unverified:
    def test_fabricated_sow_quote_is_unverified(self):
        """A fake SOW quote should produce 'unverified' verdict."""
        sow = make_sow()
        req = make_request()
        match = make_match(
            verdict="in_scope",
            sow_quote="unlimited revisions are included",  # not in SOW text
            client_quote="add a blog page",
        )
        sow_text = "The project includes 5 pages: Home, About, Contact. Two revision rounds."
        client_msg = "add a blog page"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "unverified"
        assert "R0" in result.rule_ids

    def test_fabricated_client_quote_is_unverified(self):
        """A client quote not in the message should produce 'unverified'."""
        sow = make_sow()
        req = make_request()
        match = make_match(
            verdict="out_of_scope",
            sow_quote=None,
            client_quote="completely different text not in message",
        )
        sow_text = "The project includes 5 pages."
        client_msg = "add a blog page"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "unverified"
        assert "R0" in result.rule_ids


# ── R1: Explicit exclusion ────────────────────────────────────────────────────

class TestR1Exclusion:
    def test_excluded_item_is_out_of_scope(self):
        sow = make_sow(excluded=["e-commerce", "admin dashboard"])
        req = make_request(request_text="add an e-commerce shop", type="new_feature")
        match = make_match(
            verdict="gray_area",   # LLM got it wrong
            client_quote="add an e-commerce shop",
            matched_exclusion="e-commerce",
        )
        sow_text = "Excluded: e-commerce, admin dashboard."
        client_msg = "add an e-commerce shop"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "out_of_scope"
        assert "R1" in result.rule_ids
        assert result.overridden_by_rule is True   # LLM said gray_area, rule overrides


# ── R2: New page not listed ───────────────────────────────────────────────────

class TestR2Pages:
    def test_unlisted_page_is_out_of_scope(self):
        sow = make_sow(pages=["Home", "About", "Contact"])
        req = make_request(request_text="add a Blog page", type="new_page")
        match = make_match(client_quote="add a Blog page")
        sow_text = "Pages: Home, About, Contact."
        client_msg = "add a Blog page"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "out_of_scope"
        assert "R2" in result.rule_ids

    def test_no_pages_list_gives_gray_area(self):
        """If SOW has no pages list, a new_page request is gray_area."""
        sow = make_sow(pages=[])   # empty pages
        req = make_request(request_text="add a blog page", type="new_page")
        match = make_match(client_quote="add a blog page")
        sow_text = "Website project."
        client_msg = "add a blog page"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "gray_area"


# ── R3: Revision quota ────────────────────────────────────────────────────────

class TestR3RevisionQuota:
    def test_null_revision_rounds_is_gray_area(self):
        sow = make_sow(revision_rounds=None)
        req = make_request(type="revision", magnitude="substantial", request_text="redo the layout")
        match = make_match(verdict="in_scope", client_quote="redo the layout")
        sow_text = "Revisions are available."
        client_msg = "redo the layout"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "gray_area"
        assert "R3" in result.rule_ids

    def test_quota_exceeded_is_out_of_scope(self):
        sow = make_sow(revision_rounds=2)
        req = make_request(type="revision", magnitude="tweak", request_text="change the footer colour")
        match = make_match(verdict="in_scope", client_quote="change the footer colour")
        sow_text = "Two revision rounds are included."
        client_msg = "change the footer colour"

        result = decide(req, match, sow, {"revisions_used": 2}, [], [], sow_text, client_msg)
        assert result.final_verdict == "out_of_scope"
        assert "R3" in result.rule_ids

    def test_within_quota_uses_llm_verdict(self):
        sow = make_sow(revision_rounds=2)
        req = make_request(type="revision", magnitude="tweak", request_text="change the footer colour")
        match = make_match(verdict="in_scope", client_quote="change the footer colour", confidence="high")
        sow_text = "Two revision rounds are included."
        client_msg = "change the footer colour"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "in_scope"


# ── R5: New deliverable not listed ────────────────────────────────────────────

class TestR5Deliverables:
    def test_unlisted_deliverable_is_out_of_scope(self):
        sow = make_sow(deliverables=["5-page website"])
        req = make_request(type="new_feature", request_text="add a mobile app")
        match = make_match(client_quote="add a mobile app")
        sow_text = "Deliverables: 5-page website."
        client_msg = "add a mobile app"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "out_of_scope"
        assert "R5" in result.rule_ids


# ── R6: Timeline change ───────────────────────────────────────────────────────

class TestR6Timeline:
    def test_timeline_change_is_gray_area(self):
        sow = make_sow()
        req = make_request(type="timeline_change", request_text="move deadline to January")
        match = make_match(verdict="in_scope", client_quote="move deadline to January")
        sow_text = "Timeline: December 1, 2026."
        client_msg = "move deadline to January"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "gray_area"
        assert "R6" in result.rule_ids


# ── R7: Low confidence ────────────────────────────────────────────────────────

class TestR7LowConfidence:
    def test_low_confidence_without_hard_rule_is_gray_area(self):
        sow = make_sow()
        req = make_request(type="other", request_text="make it look better overall")
        match = make_match(
            verdict="in_scope",
            confidence="low",   # LLM unsure
            client_quote="make it look better overall",
        )
        sow_text = "The project includes 5 pages."
        client_msg = "make it look better overall"

        result = decide(req, match, sow, {"revisions_used": 0}, [], [], sow_text, client_msg)
        assert result.final_verdict == "gray_area"
        assert "R7" in result.rule_ids
