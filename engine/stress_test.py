"""
engine/stress_test.py
S2: SOW Stress Test — three merged sources of issues:
  1. Lexicon scan (code, fast, deterministic)
  2. LLM judgement (confirms/rejects candidates, may add new ones)
  3. Missing-item checks (code, no LLM, from null fields in SOWFacts)

Results are merged, deduplicated, quote-verified, ranked by severity, and
capped at 5 issues. Each issue gets an id (A1..A5) for cross-referencing
in the checker (rule R4).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import PROMPTS_DIR
from .lexicon import scan as lexicon_scan, LexiconHit
from .llm import call_json
from .schemas import SOWFacts, StressIssue, StressResult
from .verifier import verify_quote

# ── Missing-field static templates ────────────────────────────────────────────
_MISSING_TEMPLATES: list[dict] = [
    {
        "trigger": lambda f: not f.pages and not f.deliverables,
        "why_risky": "No list of pages or deliverables means the scope is open-ended. "
                     "Every new request can be framed as 'part of the project'.",
        "freelancer_reading": "We agreed to build the specific things I propose.",
        "client_reading": "You'll build whatever I need until it feels complete.",
        "severity": "high",
        "suggested_rewrite": (
            "Add a section: 'Deliverables: [list each item explicitly]. "
            "Anything not listed is out of scope.'"
        ),
    },
    {
        "trigger": lambda f: f.revision_rounds is None,
        "why_risky": "No revision limit means a client can request changes indefinitely.",
        "freelancer_reading": "We'll do a reasonable number of revision rounds.",
        "client_reading": "I can keep asking for changes until I'm happy.",
        "severity": "high",
        "suggested_rewrite": (
            "Add: 'This project includes X rounds of revisions. "
            "Additional rounds will be billed at [rate]/hour.'"
        ),
    },
    {
        "trigger": lambda f: not f.excluded,
        "why_risky": "No exclusions list means nothing is explicitly out of scope.",
        "freelancer_reading": "Related things I didn't list are obviously not included.",
        "client_reading": "If you didn't say no, it's included.",
        "severity": "medium",
        "suggested_rewrite": (
            "Add an 'Excluded' section: 'The following are NOT included: "
            "[list]. Any of these requires a separate agreement.'"
        ),
    },
    {
        "trigger": lambda f: f.deadline is None,
        "why_risky": "No deadline means the project timeline is undefined.",
        "freelancer_reading": "I'll deliver within a reasonable timeframe.",
        "client_reading": "It should be done very soon.",
        "severity": "medium",
        "suggested_rewrite": "Add: 'Final delivery by [specific date].'",
    },
    {
        "trigger": lambda f: f.payment_terms is None,
        "why_risky": "No payment schedule means you may finish before getting paid.",
        "freelancer_reading": "Payment is due on delivery.",
        "client_reading": "We'll figure out payment when the work is done.",
        "severity": "medium",
        "suggested_rewrite": (
            "Add: 'Payment: 50% upfront, 50% on final delivery by [date].'"
        ),
    },
    {
        "trigger": lambda f: not f.client_responsibilities,
        "why_risky": "No client responsibilities means you bear all project risk.",
        "freelancer_reading": "The client will provide what I need when I ask.",
        "client_reading": "You figure out what you need and do it.",
        "severity": "low",
        "suggested_rewrite": (
            "Add: 'Client responsibilities: provide [content/assets/approvals] "
            "by [dates]. Delays caused by late delivery will extend the timeline.'"
        ),
    },
]


def _missing_cards(facts: SOWFacts) -> list[StressIssue]:
    cards = []
    for tmpl in _MISSING_TEMPLATES:
        if tmpl["trigger"](facts):
            cards.append(
                StressIssue(
                    quote=None,
                    kind="missing",
                    why_risky=tmpl["why_risky"],
                    freelancer_reading=tmpl["freelancer_reading"],
                    client_reading=tmpl["client_reading"],
                    severity=tmpl["severity"],
                    suggested_rewrite=tmpl["suggested_rewrite"],
                )
            )
    return cards


def _severity_rank(s: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(s, 3)


def _load_prompt() -> str:
    p = PROMPTS_DIR / "stress_test.txt"
    return p.read_text(encoding="utf-8")


def run_stress_test(
    sow_text: str,
    facts: SOWFacts,
    model: str | None = None,
) -> tuple[list[StressIssue], list[str]]:
    """
    Run the three-source stress test on a SOW.

    Returns:
        (issues, ids)
        issues: up to 5 StressIssue objects, sorted high→medium→low
        ids:    ["A1", "A2", ...] matching index to issue
    """
    # 1. Lexicon scan
    lex_hits: list[LexiconHit] = lexicon_scan(sow_text)
    candidate_phrases = [h.quote for h in lex_hits]

    # 2. LLM judgement
    system = _load_prompt()
    candidate_note = (
        f"\n\nA scanner found these candidate phrases: {candidate_phrases}. "
        "Confirm which are truly risky, reject false positives, and add any the scanner missed."
        if candidate_phrases
        else ""
    )
    user = f"SOW text:\n\n{sow_text}{candidate_note}"

    llm_result: StressResult = call_json(
        schema=StressResult,
        system=system,
        user=user,
        step="S2_stress_test",
        model=model,
        max_tokens=800,
    )
    llm_issues = llm_result.issues

    # 3. Missing-item checks (deterministic)
    missing_issues = _missing_cards(facts)

    # Merge all issues
    all_issues = list(llm_issues) + missing_issues

    # Verify quotes; drop failures (missing-kind have no quote, skip)
    verified: list[StressIssue] = []
    for issue in all_issues:
        if issue.kind == "missing" or issue.quote is None:
            verified.append(issue)
        else:
            check = verify_quote(issue.quote, sow_text)
            if check.ok:
                verified.append(issue)
            # Silently drop issues with unverifiable quotes

    # Rank and cap at 5
    verified.sort(key=lambda i: _severity_rank(i.severity))
    top5 = verified[:5]

    ids = [f"A{i + 1}" for i in range(len(top5))]
    return top5, ids
