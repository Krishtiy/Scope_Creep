"""
eval/baseline.py
Single-prompt baseline: one call to the LLM with the SOW + client message,
asking it to classify and quote directly — no pipeline, no rules.
Used to compare against the full pipeline.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from engine.llm import call_json
from engine.schemas import Verdict


class BaselineRequest(BaseModel):
    text: str
    verdict: Verdict
    sow_quote: Optional[str] = None
    client_quote: str
    reasoning: str


class BaselineResult(BaseModel):
    requests: list[BaselineRequest] = Field(default_factory=list)


_SYSTEM = """You are a scope review assistant. Given a Statement of Work and a client message, 
identify each distinct request in the message and classify it as:
- in_scope: the SOW clearly covers it
- out_of_scope: the SOW clearly excludes or does not include it  
- gray_area: the SOW is vague or silent on this

For each request:
- text: the exact request words from the client message
- verdict: in_scope, out_of_scope, or gray_area
- sow_quote: verbatim relevant clause from the SOW, or null
- client_quote: exact words from the client message
- reasoning: one sentence explanation

Use only the SOW text. Do not use outside knowledge."""


def run_baseline(
    sow_text: str,
    client_message: str,
    model: str | None = None,
) -> BaselineResult:
    """Run the single-prompt baseline (no pipeline, no rules)."""
    user = f"SOW:\n{sow_text}\n\nClient message:\n{client_message}"
    return call_json(
        schema=BaselineResult,
        system=_SYSTEM,
        user=user,
        step="baseline",
        model=model,
        max_tokens=800,
    )
