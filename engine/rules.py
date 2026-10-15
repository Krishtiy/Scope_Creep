"""
engine/rules.py
S5: Deterministic rule engine that enforces verdicts on top of the LLM's proposals.
Rules always win over the LLM (R8). The LLM never has the final word on a verdict.

Rule table:
  R0: Quote fails verification → unverified
  R1: Matched exclusion in SOW excluded list → out_of_scope
  R2: new_page not in SOW pages list → out_of_scope (or gray_area if no pages)
  R3: Revision quota — null=gray_area, exceeded=out_of_scope, else in_scope
  R4: Substantial revision with vague definition → gray_area
  R5: new_feature/new_deliverable not matching deliverables → out_of_scope
  R6: timeline_change → gray_area
  R7: LLM confidence=low, no hard rule → gray_area
  R8: Hard rule overrides LLM verdict
"""
from __future__ import annotations

from typing import Optional

from rapidfuzz import fuzz

from .schemas import (
    SOWFacts,
    SplitRequest,
    MatchResult,
    Decision,
    StressIssue,
    Verdict,
)
from .verifier import verify_quote, QuoteCheck
from .lexicon import matches_lexicon


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return text.lower().strip()


def _page_listed(request_text: str, pages: list[str], threshold: float = 85.0) -> bool:
    """Return True if the request mentions a page already in the SOW pages list."""
    nr = _norm(request_text)
    return any(
        fuzz.partial_ratio(_norm(p), nr) >= threshold
        for p in pages
    )


def _deliverable_listed(
    request_text: str, deliverables: list[str], threshold: float = 80.0
) -> bool:
    nr = _norm(request_text)
    return any(
        fuzz.partial_ratio(_norm(d), nr) >= threshold
        for d in deliverables
    )


def _vague_revision_clause(facts: SOWFacts, issues: list[StressIssue]) -> bool:
    """True if revision definition is missing or flagged as vague by lexicon."""
    if facts.revision_definition is None:
        return True
    if matches_lexicon(facts.revision_definition):
        return True
    return False


def _linked_issue(
    request: SplitRequest,
    verdict: str,
    issues: list[StressIssue],
    issue_ids: list[str],
) -> Optional[str]:
    """Return the id of a linked ambiguity issue, if any."""
    if verdict != "gray_area" or not issues:
        return None
    # Link to the first vague/missing revision-related issue
    for i, issue in enumerate(issues):
        if issue.kind in ("vague", "missing") and (
            "revision" in (issue.quote or "").lower()
            or "revision" in issue.why_risky.lower()
        ):
            return issue_ids[i] if i < len(issue_ids) else None
    return None


def _build_decision(
    request: SplitRequest,
    match: MatchResult,
    final_verdict: str,
    rule_ids: list[str],
    overridden: bool,
    sow_check: QuoteCheck,
    client_check: QuoteCheck,
    linked_ambiguity: Optional[str],
    hours: float = 0.0,
    price: float = 0.0,
) -> Decision:
    return Decision(
        request_text=request.request_text,
        final_verdict=final_verdict,  # type: ignore[arg-type]
        llm_verdict=match.verdict,
        rule_ids=rule_ids,
        overridden_by_rule=overridden,
        sow_quote=match.sow_quote,
        client_quote=match.client_quote,
        quote_methods={
            "sow":    sow_check.method if match.sow_quote else "none",
            "client": client_check.method,
        },
        linked_ambiguity=linked_ambiguity,
        consumes_revision=match.consumes_revision,
        confidence=match.confidence,
        hours=hours,
        price=price,
    )


# ── Main rule engine ──────────────────────────────────────────────────────────

def decide(
    request: SplitRequest,
    match: MatchResult,
    sow: SOWFacts,
    quota: dict,                    # {"revisions_used": int}
    issues: list[StressIssue],
    issue_ids: list[str],
    sow_text: str,
    client_message: str,
) -> Decision:
    """
    Apply rules to arrive at a final, code-enforced verdict.

    Args:
        request:        The atomic request from S3.
        match:          The LLM's proposed verdict from S4.
        sow:            Extracted SOW facts from S1.
        quota:          Current revision usage {"revisions_used": int}.
        issues:         Stress-test issues (for R4 linkage).
        issue_ids:      Corresponding ids ["A1", ...].
        sow_text:       Raw SOW text (for quote verification).
        client_message: Raw client message (for quote verification).

    Returns:
        Decision with the final, rule-enforced verdict.
    """
    rule_ids: list[str] = []

    # Verify quotes
    sow_check: QuoteCheck
    if match.sow_quote:
        sow_check = verify_quote(match.sow_quote, sow_text)
    else:
        # No SOW quote provided — treat as ok (absence is fine, not unverified)
        from dataclasses import dataclass
        sow_check = QuoteCheck(ok=True, method="none", start=None, end=None, score=0.0)

    client_check = verify_quote(match.client_quote, client_message)

    # R0: Quote fails verification
    if (match.sow_quote and not sow_check.ok) or not client_check.ok:
        return _build_decision(
            request, match, "unverified", ["R0"], False,
            sow_check, client_check, None,
        )

    # Determine hard rule
    hard: Optional[tuple[str, str]] = None  # (verdict, rule_id)

    # R1: Explicit exclusion
    if match.matched_exclusion and _norm(match.matched_exclusion) in {
        _norm(x) for x in sow.excluded
    }:
        hard = ("out_of_scope", "R1")

    # R2: New page not listed
    elif request.type == "new_page":
        if sow.pages:
            if not _page_listed(request.request_text, sow.pages):
                hard = ("out_of_scope", "R2")
            # else: page IS listed → let LLM verdict stand
        else:
            hard = ("gray_area", "R2")   # no pages list → unclear

    # R3: Revision quota
    elif request.type == "revision":
        if sow.revision_rounds is None:
            hard = ("gray_area", "R3")
        elif quota.get("revisions_used", 0) >= sow.revision_rounds:
            hard = ("out_of_scope", "R3")
        else:
            # Within quota — check for vague clause (R4)
            if (
                request.magnitude == "substantial"
                and _vague_revision_clause(sow, issues)
            ):
                hard = ("gray_area", "R4")
            # else: in_scope; let LLM verdict flow through

    # R5: New feature/deliverable not in scope
    elif request.type in ("new_feature", "new_deliverable"):
        if sow.deliverables:
            if not _deliverable_listed(request.request_text, sow.deliverables):
                hard = ("out_of_scope", "R5")
        else:
            # No deliverable list → vague clause → gray_area
            hard = ("gray_area", "R5")

    # R6: Timeline change
    elif request.type == "timeline_change":
        hard = ("gray_area", "R6")

    # Apply hard rule or fallback to LLM with R7 soft rule
    if hard:
        final_verdict, rid = hard
        rule_ids.append(rid)
        overridden = hard[0] != match.verdict
    else:
        # R7: Low confidence, no hard rule → gray_area
        if match.confidence == "low":
            final_verdict = "gray_area"
            rule_ids.append("R7")
            overridden = match.verdict != "gray_area"
        else:
            final_verdict = match.verdict
            overridden = False

    linked = _linked_issue(request, final_verdict, issues, issue_ids)

    return _build_decision(
        request, match, final_verdict, rule_ids, overridden,
        sow_check, client_check, linked,
    )
