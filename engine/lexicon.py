"""
engine/lexicon.py
Vague-phrase scanner: regex patterns from config/lexicon.yaml.
Returns candidate spans for the stress test (S2) and for rule R4.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import yaml

from .config import CONFIG_DIR


@dataclass(frozen=True)
class LexiconHit:
    tag: str
    severity: str       # "low" | "medium" | "high"
    quote: str          # matched text
    start: int
    end: int


@lru_cache(maxsize=1)
def _load_patterns() -> list[dict]:
    cfg_path = CONFIG_DIR / "lexicon.yaml"
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("patterns", [])


def scan(text: str) -> list[LexiconHit]:
    """
    Scan `text` for vague phrases defined in config/lexicon.yaml.

    Returns a list of LexiconHit sorted by position (start).
    Overlapping hits are deduplicated: the first (higher severity or earlier)
    match wins.
    """
    patterns = _load_patterns()
    hits: list[LexiconHit] = []

    for pat in patterns:
        regex    = pat["re"]
        severity = pat.get("severity", "medium")
        tag      = pat.get("tag", "untagged")

        try:
            compiled = re.compile(regex, re.IGNORECASE)
        except re.error:
            continue  # skip malformed patterns gracefully

        for m in compiled.finditer(text):
            hits.append(
                LexiconHit(
                    tag=tag,
                    severity=severity,
                    quote=m.group(0),
                    start=m.start(),
                    end=m.end(),
                )
            )

    # Deduplicate by overlapping spans (keep first / highest severity)
    hits.sort(key=lambda h: (h.start, _sev_order(h.severity)))
    deduped: list[LexiconHit] = []
    last_end = -1
    for hit in hits:
        if hit.start >= last_end:
            deduped.append(hit)
            last_end = hit.end

    return deduped


def _sev_order(sev: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(sev, 3)


def matches_lexicon(text: str) -> bool:
    """Return True if any lexicon pattern matches the text (for rule R4)."""
    return len(scan(text)) > 0
