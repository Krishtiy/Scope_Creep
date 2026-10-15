"""
engine/sow.py
S1: Extract structured facts from a raw SOW text using the LLM.
Post-extraction: verify every *_quote field with code; set to None on failure.
"""
from __future__ import annotations

from pathlib import Path

from .config import PROMPTS_DIR
from .llm import call_json
from .schemas import SOWFacts
from .verifier import verify_quote


def _load_prompt() -> str:
    p = PROMPTS_DIR / "extract_sow.txt"
    return p.read_text(encoding="utf-8")


def extract_sow(sow_text: str, model: str | None = None) -> tuple[SOWFacts, list[str]]:
    """
    Extract SOW facts from raw text.

    Returns:
        (sow_facts, warnings)
        warnings: list of human-readable strings for quotes that failed verification.
    """
    system = _load_prompt()
    user   = f"SOW text:\n\n{sow_text}"

    facts: SOWFacts = call_json(
        schema=SOWFacts,
        system=system,
        user=user,
        step="S1_extract_sow",
        model=model,
        max_tokens=600,
    )

    warnings: list[str] = []

    # Verify every *_quote field
    quote_fields = {
        "pages_quote":    facts.pages_quote,
        "revision_quote": facts.revision_quote,
        "excluded_quote": facts.excluded_quote,
    }
    for field_name, quote in quote_fields.items():
        if quote is None:
            continue
        check = verify_quote(quote, sow_text)
        if not check.ok:
            warnings.append(
                f"Could not verify extraction for '{field_name}' "
                f"(method={check.method}, score={check.score:.1f}). "
                "Please review this field manually."
            )
            # Null out the unverifiable quote
            setattr(facts, field_name, None)

    return facts, warnings
