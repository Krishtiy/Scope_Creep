"""
engine/sow.py
S1: Extract structured facts from a raw SOW text using the LLM.
Post-extraction:
  1. Regex fallback: fills obvious fields that gemma2:2b commonly omits.
  2. Verify every *_quote field with code; set to None on failure.
"""
from __future__ import annotations

import re
from pathlib import Path

from .config import PROMPTS_DIR
from .llm import call_json
from .schemas import SOWFacts
from .verifier import verify_quote


def _load_prompt() -> str:
    p = PROMPTS_DIR / "extract_sow.txt"
    return p.read_text(encoding="utf-8")


# ── Regex fallback helpers ────────────────────────────────────────────────────

def _regex_pages(sow_text: str) -> list[str]:
    """
    Try to extract page names from patterns like:
      '4 pages: Home, Menu, About Us, Contact'
      'following pages: Home, About, Contact'
      'Those pages are: who we are, what we do...'
    """
    # Clean out adjective compound phrases like "one-page guide" so they don't trigger false positives
    cleaned_text = re.sub(
        r'(?:one|single|\d+)[- ]page\s+(?:guide|document|summary|pdf|report|sheet|manual)',
        '',
        sow_text,
        flags=re.IGNORECASE,
    )

    # Match 'X pages: ...' or 'pages: ...' or 'those pages are: ...'
    pattern = re.compile(
        r'(?:following\s+\d+\s+pages?|pages?\s+included?|those\s+pages\s+are|pages?)[\s:]+([A-Za-z ,/&]+?)(?:\.|$)',
        re.IGNORECASE | re.MULTILINE,
    )
    for m in pattern.finditer(cleaned_text):
        raw = m.group(1)
        # Split on comma, filter short/empty tokens
        items = [p.strip() for p in raw.split(",") if len(p.strip()) > 1]
        # Ignore document types
        items = [p for p in items if not re.search(r'\b(?:guide|manual|document|summary|pdf)\b', p, re.IGNORECASE)]
        if items:
            return items

    # Fallback: look for 'Home, Menu, About ...' style enum after a colon
    colon_pattern = re.compile(
        r':\s*([A-Z][a-zA-Z ]+(?:,\s*[A-Z][a-zA-Z ]+){2,})',
        re.MULTILINE,
    )
    for m in colon_pattern.finditer(cleaned_text):
        items = [p.strip() for p in m.group(1).split(",") if len(p.strip()) > 1]
        if items:
            return items

    return []


def _regex_revision_rounds(sow_text: str) -> int | None:
    """
    Try to extract revision round count from patterns like:
      'up to 2 rounds', '2 revisions', 'two of those built in'
    """
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    pattern = re.compile(
        r'(?:up\s+to\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
        r'\s+(?:rounds?\s+of\s+)?(?:minor\s+)?(?:revis(?:ion|ions)|changes|edits|tweaks|feedback)',
        re.IGNORECASE,
    )
    m = pattern.search(sow_text)
    if m:
        val = m.group(1).lower()
        return word_to_num.get(val, int(val) if val.isdigit() else None)

    # Check for "two of those built in" or "X built in"
    built_in_pattern = re.compile(
        r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:of\s+those\s+)?(?:built\s+in|included)',
        re.IGNORECASE,
    )
    m_bi = built_in_pattern.search(sow_text)
    if m_bi:
        val = m_bi.group(1).lower()
        return word_to_num.get(val, int(val) if val.isdigit() else None)

    if re.search(r'\bone\s+shot\b', sow_text, re.IGNORECASE):
        return 1
    return None


def _regex_excluded(sow_text: str) -> list[str]:
    """
    Try to extract excluded items from a bullet list following
    'NOT included', 'Excluded:', or similar headings.
    """
    pattern = re.compile(
        r'(?:not\s+included|excluded?|following\s+are\s+not\s+included)[^\n]*\n'
        r'((?:\s*[-*•]\s*.+\n?)+)',
        re.IGNORECASE,
    )
    m = pattern.search(sow_text)
    if m:
        block = m.group(1)
        items = re.findall(r'[-*•]\s*(.+)', block)
        return [i.strip() for i in items if i.strip()]

    # Match "X, Y, or Z will be quoted separately"
    qs_m = re.search(r'(?:[.\n]|^)\s*([^.\n]+?)\s+will\s+be\s+quoted\s+separately', sow_text, re.IGNORECASE)
    if qs_m:
        raw = qs_m.group(1).strip()
        items = [p.strip() for p in re.split(r',|\bor\b', raw) if len(p.strip()) > 2]
        if items:
            return items

    return []


def _regex_deliverables(sow_text: str) -> list[str]:
    """
    Try to extract deliverables from a bulleted list or conversational phrasing.
    """
    # 1. Look for 'Deliverables:' bullet list
    pattern = re.compile(
        r'(?:deliverables?|scope of work)[^\n]*\n'
        r'((?:\s*[-*•]\s*.+\n?)+)',
        re.IGNORECASE,
    )
    m = pattern.search(sow_text)
    if m:
        items = re.findall(r'[-*•]\s*(.+)', m.group(1))
        found = [i.strip() for i in items if i.strip()]
        if found:
            return found

    # 2. Look for scope limitation: "limited to a four-page brochure website"
    scope_pattern = re.compile(
        r'(?:scope(?:\s+of\s+this\s+contract)?\s+is\s+limited\s+to\s+a\s+|building\s+(?:out\s+)?your\s+)([a-zA-Z0-9_\- ]+?\s+(?:website|site|app|application|package))',
        re.IGNORECASE,
    )
    m2 = scope_pattern.search(sow_text)
    if m2:
        item = m2.group(1).strip()
        if len(item) > 3:
            return [item]

    # 3. Look for conversational phrasing: "building out your portfolio site"
    conv_pattern = re.compile(
        r'(?:building(?:\s+out)?|creating|designing|developing)\s+(?:your\s+|a\s+|the\s+)([a-zA-Z0-9_\- ]+?)(?:\s*—|\s*[-–]|,|\.|\n)',
        re.IGNORECASE,
    )
    m3 = conv_pattern.search(sow_text)
    if m3:
        item = m3.group(1).strip()
        if len(item) > 3:
            return [item]

    return []


def _regex_client_responsibilities(sow_text: str) -> list[str]:
    """
    Try to extract client responsibilities from headings or bullet points.
    """
    pattern = re.compile(
        r'(?:client\s+responsibilities?|client\s+provides?|client\s+will\s+provide)[^\n:]*[:\n]'
        r'((?:\s*[-*•]\s*.+\n?)+|[^\n]+)',
        re.IGNORECASE,
    )
    m = pattern.search(sow_text)
    if m:
        raw = m.group(1).strip()
        bullets = re.findall(r'[-*•]\s*(.+)', raw)
        if bullets:
            return [b.strip() for b in bullets if b.strip()]
        if len(raw) > 3:
            return [raw]
    return []


def _regex_pages_quote(sow_text: str, pages: list[str]) -> str | None:
    """Find the sentence in the SOW that lists the pages."""
    if not pages:
        return None
    # Search for a line containing most page names
    for line in sow_text.splitlines():
        matches = sum(1 for p in pages if p.lower() in line.lower())
        if matches >= max(1, len(pages) // 2):
            return line.strip()
    return None


def _regex_revision_quote(sow_text: str) -> str | None:
    """Find the sentence in the SOW that mentions revision rounds or limits."""
    pattern = re.compile(
        r'(?:revis(?:ion|ions)|one\s+shot|rounds?\s+of\s+changes|edits|tweaks|built\s+in)',
        re.IGNORECASE,
    )
    for line in sow_text.splitlines():
        if pattern.search(line):
            return line.strip()
    return None


def _regex_excluded_quote(sow_text: str) -> str | None:
    """Find the block or sentence of excluded items."""
    pattern = re.compile(
        r'(?:not\s+included|excluded?)[^\n]*\n(?:\s*[-*•]\s*.+\n?)+',
        re.IGNORECASE,
    )
    m = pattern.search(sow_text)
    if m:
        return m.group(0).strip()
    for line in sow_text.splitlines():
        if re.search(r'(?:quoted\s+separately|outside\s+(?:the\s+)?scope|separate\s+conversation|not\s+(?:part\s+of|included))', line, re.IGNORECASE):
            return line.strip()
    return None


def _apply_regex_fallback(facts: SOWFacts, sow_text: str) -> SOWFacts:
    """
    Fill any fields that the LLM left empty using simple regex extraction.
    Only fills fields that are None/empty — never overwrites LLM values.
    """
    if not facts.pages:
        pages = _regex_pages(sow_text)
        if pages:
            facts.pages = pages

    if not facts.deliverables:
        deliverables = _regex_deliverables(sow_text)
        if deliverables:
            facts.deliverables = deliverables
        elif facts.pages:
            m_site = re.search(r'([a-zA-Z0-9_\- ]+?\s+(?:website|site|app|application|package))', sow_text, re.IGNORECASE)
            if m_site and len(m_site.group(1).strip()) < 40:
                facts.deliverables = [m_site.group(1).strip()]
            elif facts.project:
                facts.deliverables = [facts.project]
        elif facts.project:
            facts.deliverables = [facts.project]

    if facts.revision_rounds is None:
        rounds = _regex_revision_rounds(sow_text)
        if rounds is not None:
            facts.revision_rounds = rounds

    if not facts.excluded:
        excluded = _regex_excluded(sow_text)
        if excluded:
            facts.excluded = excluded

    if not facts.client_responsibilities:
        client_resp = _regex_client_responsibilities(sow_text)
        if client_resp:
            facts.client_responsibilities = client_resp
    else:
        # Filter out hallucinated items if the LLM echoed prompt examples
        facts.client_responsibilities = [
            r for r in facts.client_responsibilities
            if any(w in sow_text.lower() for w in re.findall(r'[a-zA-Z]{4,}', r.lower()))
        ]

    if facts.pages_quote is None:
        facts.pages_quote = _regex_pages_quote(sow_text, facts.pages)

    if facts.revision_quote is None:
        facts.revision_quote = _regex_revision_quote(sow_text)

    if facts.excluded_quote is None:
        facts.excluded_quote = _regex_excluded_quote(sow_text)

    return facts


# ── Main extraction entry point ───────────────────────────────────────────────

def extract_sow(sow_text: str, model: str | None = None) -> tuple[SOWFacts, list[str]]:
    """
    Extract SOW facts from raw text.

    Returns:
        (sow_facts, warnings)
        warnings: list of human-readable strings for quotes that failed verification.
    """
    print(f"[SOW] Starting extraction | text_length={len(sow_text)} chars", flush=True)
    system = _load_prompt()
    user   = f"SOW text:\n\n{sow_text}"

    facts: SOWFacts = call_json(
        schema=SOWFacts,
        system=system,
        user=user,
        step="S1_extract_sow",
        model=model,
        max_tokens=1500,          # raised from 600 — schema has 12 fields
    )
    print(f"[SOW] LLM returned | pages={facts.pages} | revision_rounds={facts.revision_rounds} | excluded_count={len(facts.excluded)}", flush=True)

    # ── Regex fallback: fill fields the LLM left empty ────────────────────────
    print(f"[SOW] Running regex fallback...", flush=True)
    facts = _apply_regex_fallback(facts, sow_text)
    print(f"[SOW] After fallback | pages={facts.pages} | revision_rounds={facts.revision_rounds} | excluded_count={len(facts.excluded)}", flush=True)

    warnings: list[str] = []

    # ── Verify every *_quote field ────────────────────────────────────────────
    quote_fields = {
        "pages_quote":    facts.pages_quote,
        "revision_quote": facts.revision_quote,
        "excluded_quote": facts.excluded_quote,
    }
    for field_name, quote in quote_fields.items():
        if quote is None:
            print(f"[SOW] {field_name}: skipped (null)", flush=True)
            continue
        print(f"[SOW] Verifying {field_name}...", flush=True)
        check = verify_quote(quote, sow_text)
        print(f"[SOW] {field_name}: method={check.method} ok={check.ok} score={check.score:.1f}", flush=True)
        if not check.ok:
            warnings.append(
                f"Could not verify extraction for '{field_name}' "
                f"(method={check.method}, score={check.score:.1f}). "
                "Please review this field manually."
            )
            # Null out the unverifiable quote
            setattr(facts, field_name, None)

    print(f"[SOW] Extraction complete | warnings={len(warnings)}", flush=True)
    return facts, warnings
