"""
eval/make_report.py
Generate results/RESULTS.md from raw eval output files.
Run after completing all eval runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.config import RESULTS_DIR
from eval.metrics import format_confusion_matrix_md


def load_all_results() -> list[dict]:
    raw_dir = RESULTS_DIR / "raw"
    results = []
    for f in raw_dir.glob("eval_*.json"):
        try:
            with f.open(encoding="utf-8") as fh:
                results.append(json.load(fh))
        except Exception:
            pass
    for f in raw_dir.glob("backboard_*.json"):
        try:
            with f.open(encoding="utf-8") as fh:
                d = json.load(fh)
                d["mode"] = "backboard"
                d["n_requests"] = len(d.get("details", []))
                results.append(d)
        except Exception:
            pass
    return results


def make_summary_table(results: list[dict]) -> str:
    if not results:
        return "_No eval results found. Run `python -m eval.run_eval` first._\n"

    header = "| Model | Mode | Split | N | Accuracy | False Accusation Rate |\n"
    sep    = "|-------|------|-------|---|----------|----------------------|\n"
    rows   = []
    for r in sorted(results, key=lambda x: (x["model"], x["mode"], x["split"])):
        rows.append(
            f"| {r['model']} | {r['mode']} | {r['split']} | {r['n_requests']} | "
            f"{r['accuracy']:.1%} | {r['false_accusation_rate']:.1%} |"
        )
    return header + sep + "\n".join(rows) + "\n"


def main():
    results = load_all_results()

    lines = [
        "# Scope-Creep Catcher — Evaluation Results",
        "",
        "> **Note:** Gold set is self-written (synthetic). n is small (~23 requests).",
        "> Accuracy has roughly ±13 percentage points of uncertainty.",
        "> Do not overinterpret small differences between models or modes.",
        "",
        "## Summary Table",
        "",
        make_summary_table(results),
        "",
    ]

    for r in results:
        lines += [
            f"## {r['model']} | {r['mode']} | {r['split']}",
            "",
            f"- **Accuracy:** {r['accuracy']:.1%}",
            f"- **False accusation rate:** {r['false_accusation_rate']:.1%}",
            f"- **Per difficulty:** {r.get('per_difficulty', {})}",
            "",
            "### Confusion Matrix",
            "",
            format_confusion_matrix_md(r.get("confusion_matrix", {})),
            "",
        ]

    lines += [
        "---",
        "",
        "## Limitations",
        "",
        "- Gold set is self-written, not independently labelled.",
        "- n ≈ 23 requests total (dev + test combined).",
        "- Hour estimates are illustrative — not real project quotes.",
        "- The quote verifier catches fabricated citations but not wrong reasoning.",
        "- This is not legal advice.",
        "",
    ]

    out_path = RESULTS_DIR / "RESULTS.md"
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
