"""
engine/schemas.py
All Pydantic v2 schemas used by the pipeline.
These are passed directly to Ollama's `format` parameter via model_json_schema().
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

# ── Type aliases ─────────────────────────────────────────────────────────────
Verdict  = Literal["in_scope", "out_of_scope", "gray_area"]
ReqType  = Literal["new_page", "revision", "new_feature", "new_deliverable",
                   "timeline_change", "other"]
Severity = Literal["low", "medium", "high"]
Conf     = Literal["low", "medium", "high"]


# ── S1: SOW Extraction ────────────────────────────────────────────────────────
class SOWFacts(BaseModel):
    """Output of S1 extraction. None/empty means the SOW does not state it."""

    project: Optional[str] = None
    pages: list[str] = Field(default_factory=list)
    revision_rounds: Optional[int] = None
    revision_definition: Optional[str] = None
    deliverables: list[str] = Field(default_factory=list)
    excluded: list[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    payment_terms: Optional[str] = None
    client_responsibilities: list[str] = Field(default_factory=list)

    # Evidence quotes — verified by code after extraction
    pages_quote: Optional[str] = None
    revision_quote: Optional[str] = None
    excluded_quote: Optional[str] = None


# ── S2: Stress Test ───────────────────────────────────────────────────────────
class StressIssue(BaseModel):
    """A single ambiguity or risk card from the SOW stress test."""

    quote: Optional[str] = None          # exact SOW text; None only for 'missing' kind
    kind: Literal["vague", "undefined_term", "missing"]
    why_risky: str
    freelancer_reading: str
    client_reading: str
    severity: Severity
    suggested_rewrite: str


class StressResult(BaseModel):
    """Up to 5 stress-test issues, ranked by severity."""

    issues: list[StressIssue] = Field(default_factory=list, max_length=5)


# ── S3: Split Request ─────────────────────────────────────────────────────────
class SplitRequest(BaseModel):
    """One atomic request parsed out of a client message."""

    request_text: str                    # exact client words
    type: ReqType
    magnitude: Literal["tweak", "substantial", "unclear"]


class SplitResult(BaseModel):
    requests: list[SplitRequest] = Field(default_factory=list)


# ── S4: Match & Propose ───────────────────────────────────────────────────────
class MatchResult(BaseModel):
    """LLM's proposed verdict for a single request, before rule enforcement."""

    verdict: Verdict
    sow_quote: Optional[str] = None
    client_quote: str
    matched_exclusion: Optional[str] = None
    consumes_revision: bool = False
    size: Literal["S", "M", "L"] = "M"
    confidence: Conf = "medium"
    reasoning: str


# ── S5: Decision (code-enforced) ──────────────────────────────────────────────
class Decision(BaseModel):
    """Final decision after rule enforcement and quote verification."""

    request_text: str
    final_verdict: Literal["in_scope", "out_of_scope", "gray_area", "unverified"]
    llm_verdict: Verdict
    rule_ids: list[str] = Field(default_factory=list)
    overridden_by_rule: bool = False
    sow_quote: Optional[str] = None
    client_quote: str
    quote_methods: dict = Field(default_factory=dict)   # {"sow": "exact|fuzzy|none", "client": "exact|fuzzy"}
    linked_ambiguity: Optional[str] = None              # e.g. "A2"
    consumes_revision: bool = False
    confidence: Conf = "medium"
    hours: float = 0.0
    price: float = 0.0
