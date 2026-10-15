"""
engine/pricing.py
S6: Estimate hours and price for out-of-scope requests.
All estimates are illustrative — labeled as such in the UI.
Config is loaded from config/hours.yaml.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from .config import CONFIG_DIR


@lru_cache(maxsize=1)
def _load_cfg() -> dict:
    p = CONFIG_DIR / "hours.yaml"
    with p.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def estimate_hours(req_type: str, size: str) -> float:
    """Return illustrative hour estimate for a request type and size."""
    cfg = _load_cfg()
    base = cfg["base_hours"].get(req_type, cfg["base_hours"]["other"])
    mult = cfg["size_multiplier"].get(size, 1.0)
    return round(base * mult, 1)


def price(hours: float, rate: float) -> float:
    """Convert hours to price at the given hourly rate."""
    return round(hours * rate, 2)


def summary(
    log: list[dict],
    rate: float,
    contract_price: float,
) -> dict:
    """
    Compute the summary bar figures for the top bar.

    Returns dict with:
        extras:         number of out-of-scope items
        hours:          total extra hours
        value:          total extra value at rate
        pct_over_scope: percentage of contract scope the extras represent
    """
    extra = [e for e in log if e.get("verdict") == "out_of_scope"]
    total_hours = sum(e.get("hours", 0.0) for e in extra)
    baseline = contract_price / rate if rate else 0.0
    return {
        "extras":         len(extra),
        "hours":          round(total_hours, 1),
        "value":          price(total_hours, rate),
        "pct_over_scope": round(100 * total_hours / baseline, 1) if baseline else None,
    }
