"""
engine/drafter.py
S7: Draft a polite reply and change-order block.
- LLM writes the reply text with numeric placeholders ({PRICE_1}, {HOURS_1})
- Code fills placeholders with actual numbers from decisions
- Number guard: every number in the draft must be in the allowed set
- Change-order block is built by code template, not LLM
- Gray area: clarifying question, never accusation
"""
from __future__ import annotations

import re
from typing import Optional

from .config import PROMPTS_DIR
from .llm import call_json
from .schemas import Decision
from pydantic import BaseModel


class DraftResult(BaseModel):
    reply_text: str
    clarifying_question: Optional[str] = None  # for gray_area items


# ── Number guard ──────────────────────────────────────────────────────────────

def _extract_numbers_from_text(text: str) -> set[str]:
    """Extract all numeric strings from text."""
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _build_allowed_numbers(decisions: list[Decision], rate: float) -> set[str]:
    """Build the set of numbers the LLM is allowed to use in the draft."""
    allowed = set()
    for d in decisions:
        if d.hours:
            allowed.add(str(d.hours))
            allowed.add(str(int(d.hours)) if d.hours == int(d.hours) else str(d.hours))
        if d.price:
            allowed.add(str(d.price))
            allowed.add(str(int(d.price)) if d.price == int(d.price) else str(d.price))
    if rate:
        allowed.add(str(rate))
        allowed.add(str(int(rate)) if rate == int(rate) else str(rate))
    # Add revision counts
    for d in decisions:
        if d.consumes_revision:
            allowed.add("1")
    return allowed


def _guard_numbers(draft: str, allowed: set[str]) -> bool:
    """Return True if all numbers in the draft are in the allowed set."""
    found = _extract_numbers_from_text(draft)
    return found.issubset(allowed)


# ── Change-order template (code-built, not LLM) ───────────────────────────────

def _build_change_order(decisions: list[Decision], order_num: int = 1) -> str:
    """Build the change-order Markdown block from code, not the LLM."""
    out_of_scope = [d for d in decisions if d.final_verdict == "out_of_scope"]
    if not out_of_scope:
        return ""

    lines = [f"**Change Order #{order_num}**"]
    for i, d in enumerate(out_of_scope, 1):
        lines.append(f"- Scope addition {i}: {d.request_text}")
        lines.append(f"  - Estimated hours: {d.hours}")
        lines.append(f"  - Cost: ${d.price:.2f}")
    total_hours = sum(d.hours for d in out_of_scope)
    total_price = sum(d.price for d in out_of_scope)
    lines.append(f"\n**Total estimated: {total_hours}h / ${total_price:.2f}**")
    lines.append("\nReply \"APPROVED\" to proceed.")
    return "\n".join(lines)


# ── Fallback plain template ───────────────────────────────────────────────────

def _fallback_reply(decisions: list[Decision], tone: str) -> str:
    """Plain template reply when the LLM output fails the number guard twice."""
    oos = [d for d in decisions if d.final_verdict == "out_of_scope"]
    gray = [d for d in decisions if d.final_verdict == "gray_area"]
    in_scope = [d for d in decisions if d.final_verdict == "in_scope"]

    parts = ["Hi,\n\nThank you for your message. Here's a quick summary:\n"]
    if in_scope:
        parts.append(
            "The following are within scope: "
            + ", ".join(d.request_text for d in in_scope) + ".\n"
        )
    if oos:
        parts.append(
            "The following items are outside the original agreement and would "
            "require a change order: "
            + ", ".join(d.request_text for d in oos) + ".\n"
        )
    if gray:
        parts.append(
            "The following need clarification before I can advise: "
            + ", ".join(d.request_text for d in gray) + ".\n"
        )
    parts.append("\nHappy to discuss. Let me know how you'd like to proceed.")
    return "\n".join(parts)


# ── Main drafter ──────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    return (PROMPTS_DIR / "draft_reply.txt").read_text(encoding="utf-8")


def draft_reply(
    decisions: list[Decision],
    rate: float,
    tone: str = "friendly",
    freelancer_name: Optional[str] = None,
    model: str | None = None,
) -> tuple[str, str]:
    """
    Draft a polite reply and a change-order block.

    Args:
        decisions:       All decisions from S5.
        rate:            Hourly rate (for number guard).
        tone:            "friendly" | "firm" | "formal"
        freelancer_name: Optional name to sign off with.
        model:           Override model.

    Returns:
        (reply_text, change_order_markdown)
    """
    system = _load_prompt()
    allowed = _build_allowed_numbers(decisions, rate)

    # Build decision summary for the LLM
    summary_lines = []
    for i, d in enumerate(decisions, 1):
        summary_lines.append(
            f"{i}. [{d.final_verdict.upper()}] {d.request_text} "
            f"— {{HOURS_{i}}}h / ${{PRICE_{i}}} "
            f"(confidence: {d.confidence})"
        )

    user = (
        f"Tone: {tone}\n"
        f"Freelancer name: {freelancer_name or 'not provided'}\n\n"
        f"Decisions:\n" + "\n".join(summary_lines)
    )

    last_draft = None
    for attempt in range(2):
        try:
            result: DraftResult = call_json(
                schema=DraftResult,
                system=system,
                user=user,
                step="S7_draft",
                model=model,
                max_tokens=600,
            )
            draft = result.reply_text

            # Fill numeric placeholders with actual values
            for i, d in enumerate(decisions, 1):
                draft = draft.replace(f"{{HOURS_{i}}}", str(d.hours))
                draft = draft.replace(f"{{PRICE_{i}}}", f"{d.price:.2f}")

            # Number guard
            if _guard_numbers(draft, allowed):
                last_draft = draft
                break
            # If guard fails, retry
        except Exception:
            pass

    if last_draft is None:
        last_draft = _fallback_reply(decisions, tone)

    change_order = _build_change_order(decisions)
    return last_draft, change_order
