"""
engine/config.py
Central configuration: model names, paths, defaults.
Edit this file to switch models or tune parameters.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
PROMPTS_DIR   = ROOT / "prompts"
SKILLS_DIR    = ROOT / "skills"
CONFIG_DIR    = ROOT / "config"
DATA_DIR      = ROOT / "data"
RESULTS_DIR   = ROOT / "results"
RAW_DIR       = RESULTS_DIR / "raw"
PROJECTS_DIR  = DATA_DIR / "projects"
GOLD_DIR      = DATA_DIR / "gold"

# Ensure directories exist
for _d in [RAW_DIR, PROJECTS_DIR, GOLD_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Model settings ────────────────────────────────────────────────────────────
# Primary model: gemma2:2b (installed, fast on local hardware)
# Future comparison model: qwen2.5:7b (noted in IMPLEMENTATION_PLAN.md)
MODEL    : str = "gemma2:2b"
NUM_CTX  : int = 8192      # context window for SOW processing
SEED     : int = 42        # deterministic outputs across runs
MAX_TOKENS_DEFAULT : int = 700

# ── Metrics logger ────────────────────────────────────────────────────────────
METRICS_FILE = RAW_DIR / "metrics.jsonl"


@dataclass
class _MetricsRecord:
    step: str
    model: str
    seconds: float
    prompt_tokens: Optional[int]
    output_tokens: Optional[int]
    timestamp: float = field(default_factory=time.time)


class MetricsLogger:
    """Appends one JSON line per LLM call to results/raw/metrics.jsonl."""

    def record(
        self,
        step: str,
        model: str,
        seconds: float,
        prompt_tokens: Optional[int],
        output_tokens: Optional[int],
    ) -> None:
        rec = _MetricsRecord(
            step=step,
            model=model,
            seconds=round(seconds, 3),
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )
        with METRICS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(rec)) + "\n")


# Singleton shared across the whole app
METRICS = MetricsLogger()
