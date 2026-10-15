"""
engine/checker.py
S3: Split a client message into atomic requests (LLM).
S4: For each request, match against the SOW and propose a verdict (LLM + skills profile).
"""
from __future__ import annotations

from pathlib import Path

from .config import PROMPTS_DIR, SKILLS_DIR
from .llm import call_json
from .schemas import SOWFacts, SplitRequest, SplitResult, MatchResult


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _load_skills_profile(niche: str | None) -> str:
    """Load a skills profile if available (web_dev or copywriting)."""
    if not niche:
        return ""
    p = SKILLS_DIR / f"{niche}.md"
    if p.exists():
        return f"\n\nNiche skills profile:\n{p.read_text(encoding='utf-8')}"
    return ""


def split_requests(
    client_message: str,
    model: str | None = None,
) -> SplitResult:
    """
    S3: Split a client message into atomic requests.

    Args:
        client_message: The raw text from the client.
        model: Override the default model.

    Returns:
        SplitResult containing one SplitRequest per atomic request.
    """
    system = _load_prompt("split_requests.txt")
    return call_json(
        schema=SplitResult,
        system=system,
        user=f"Client message:\n\n{client_message}",
        step="S3_split",
        model=model,
        max_tokens=500,
    )


def match_request(
    request: SplitRequest,
    sow_text: str,
    facts: SOWFacts,
    niche: str | None = None,
    model: str | None = None,
) -> MatchResult:
    """
    S4: Propose a verdict for a single request against the SOW.

    Args:
        request:  A single atomic request from split_requests().
        sow_text: Full raw SOW text.
        facts:    Structured SOWFacts (from S1).
        niche:    Skills profile to inject ("web_dev" | "copywriting" | None).
        model:    Override the default model.

    Returns:
        MatchResult with the LLM's proposed verdict (not yet rule-enforced).
    """
    system = _load_prompt("match_request.txt") + _load_skills_profile(niche)

    sow_summary = (
        f"Pages: {facts.pages or 'not stated'}\n"
        f"Revision rounds: {facts.revision_rounds or 'not stated'}\n"
        f"Deliverables: {facts.deliverables or 'not stated'}\n"
        f"Excluded: {facts.excluded or 'none stated'}\n"
    )

    user = (
        f"SOW facts:\n{sow_summary}\n\n"
        f"Full SOW text:\n{sow_text}\n\n"
        f"Client request:\n{request.request_text}\n"
        f"Request type: {request.type}, magnitude: {request.magnitude}"
    )

    return call_json(
        schema=MatchResult,
        system=system,
        user=user,
        step="S4_match",
        model=model,
        max_tokens=500,
    )
