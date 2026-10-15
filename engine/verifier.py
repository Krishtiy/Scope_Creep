"""
engine/verifier.py
Quote verification: checks that an LLM-produced quote actually appears in the
source text (SOW or client message).

Design:
  1. Exact match after Unicode normalization and smart-quote replacement.
  2. Fuzzy fallback (rapidfuzz partial_ratio_alignment) at >=95% similarity.
  3. Numbers must match exactly (word-numbers mapped to digits) to prevent
     "2 revision rounds" being accepted as a quote for "3 revision rounds".
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz

# ── Normalisation maps ────────────────────────────────────────────────────────
_CHAR_MAP: dict[str, str] = {
    "\u201c": '"', "\u201d": '"',   # " "  → "
    "\u2018": "'", "\u2019": "'",   # ' '  → '
    "\u2026": "...",                 # …    → ...
    "\u00a0": " ",                   # NBSP → space
    "\u2013": "-",                   # en dash
    "\u2014": "-",                   # em dash
}

_WORD_NUM: dict[str, str] = {
    w: str(i)
    for i, w in enumerate(
        "zero one two three four five six seven eight nine "
        "ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen twenty".split()
    )
}

_FUZZY_THRESHOLD = 95.0
_MIN_QUOTE_LEN   = 4       # quotes shorter than this are rejected outright


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """
    Normalize text for comparison and return a character-index mapping back
    to the original positions.

    Returns:
        (normalized_string, index_map)
        index_map[i] = position in original `text` for normalized char at i.
    """
    out: list[str]  = []
    idx: list[int]  = []
    prev_space = False

    for orig_i, ch in enumerate(text):
        expanded = unicodedata.normalize("NFKC", _CHAR_MAP.get(ch, ch))
        for c in expanded:
            if c.isspace():
                if prev_space:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = False
            out.append(c.lower())
            idx.append(orig_i)

    return "".join(out), idx


def _extract_numbers(text: str) -> list[str]:
    """
    Extract all numeric tokens from text, converting word-numbers to digits.
    E.g. "two revision rounds" → ["2"]
    """
    tokens = re.findall(r"[a-z]+|\d+(?:[.,]\d+)?", text.lower())
    result = []
    for tok in tokens:
        if tok in _WORD_NUM:
            result.append(_WORD_NUM[tok])
        elif tok and tok[0].isdigit():
            result.append(tok)
    return result


@dataclass
class QuoteCheck:
    """Result of a single quote verification."""
    ok: bool
    method: str          # "exact" | "fuzzy" | "not_found" | "number_mismatch" | "too_short"
    start: int | None    # character start in original source
    end: int | None      # character end (exclusive) in original source
    score: float         # 100.0 for exact, fuzzy score otherwise, 0.0 on failure


def verify_quote(
    quote: str,
    source: str,
    threshold: float = _FUZZY_THRESHOLD,
) -> QuoteCheck:
    """
    Verify that `quote` appears in `source`.

    Steps:
      1. Exact match after normalization.
      2. Fuzzy partial-ratio with number guard.

    Args:
        quote:     The string the LLM claimed to quote.
        source:    The original document (SOW text or client message).
        threshold: Minimum fuzzy score (0–100) to accept a fuzzy match.

    Returns:
        QuoteCheck with ok=True if the quote is verified.
    """
    nq, _    = _normalize_with_map(quote)
    nq       = nq.strip()
    ns, imap = _normalize_with_map(source)

    # Reject trivially short quotes
    if len(nq) < _MIN_QUOTE_LEN:
        return QuoteCheck(ok=False, method="too_short", start=None, end=None, score=0.0)

    # 1) Exact match (after normalization)
    pos = ns.find(nq)
    if pos >= 0:
        end_pos = pos + len(nq) - 1
        return QuoteCheck(
            ok=True,
            method="exact",
            start=imap[pos],
            end=imap[end_pos] + 1,
            score=100.0,
        )

    # 2) Fuzzy fallback
    alignment = fuzz.partial_ratio_alignment(nq, ns)
    if alignment and alignment.score >= threshold:
        window = ns[alignment.dest_start : alignment.dest_end]
        if _extract_numbers(nq) == _extract_numbers(window):
            start_orig = imap[alignment.dest_start] if alignment.dest_start < len(imap) else None
            end_orig   = imap[alignment.dest_end - 1] + 1 if alignment.dest_end > 0 and alignment.dest_end - 1 < len(imap) else None
            return QuoteCheck(
                ok=True,
                method="fuzzy",
                start=start_orig,
                end=end_orig,
                score=alignment.score,
            )
        # Numbers don't match — reject
        return QuoteCheck(
            ok=False,
            method="number_mismatch",
            start=None,
            end=None,
            score=alignment.score,
        )

    return QuoteCheck(
        ok=False,
        method="not_found",
        start=None,
        end=None,
        score=alignment.score if alignment else 0.0,
    )
