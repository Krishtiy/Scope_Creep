"""
eval/run_eval.py
Evaluation harness for the Scope-Creep Catcher pipeline.

Usage:
    python -m eval.run_eval --model gemma2:2b --mode pipeline --split test
    python -m eval.run_eval --model gemma2:2b --mode baseline --split test
    python -m eval.run_eval --model gemma2:2b --mode pipeline --split dev

Modes:
    pipeline  - Full S1→S5 pipeline with rule engine
    baseline  - Single-prompt baseline (no pipeline, no rules)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure project root is on the path when run as `python -m eval.run_eval`
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from engine.config import GOLD_DIR, RESULTS_DIR
from engine.sow import extract_sow
from engine.checker import split_requests, match_request
from engine.rules import decide
from engine.pricing import estimate_hours, price
from engine.verifier import verify_quote
from eval.baseline import run_baseline
from eval.metrics import (
    accuracy, false_accusation_rate, confusion_matrix,
    per_difficulty, format_confusion_matrix_md,
)


def load_gold_cases(split: str) -> list[dict]:
    cases_path = GOLD_DIR / "cases.json"
    with cases_path.open(encoding="utf-8") as fh:
        all_cases = json.load(fh)
    return [c for c in all_cases if c.get("split") == split]


def load_sow_text(sow_file: str) -> str:
    p = GOLD_DIR / "sows" / sow_file
    return p.read_text(encoding="utf-8")


_SOW_CACHE: dict[tuple[str, str], tuple[SOWFacts, list[str]]] = {}

def get_cached_sow(sow_file: str, sow_text: str, model: str) -> tuple[SOWFacts, list[str]]:
    key = (sow_file, model)
    if key not in _SOW_CACHE:
        _SOW_CACHE[key] = extract_sow(sow_text, model=model)
    return _SOW_CACHE[key]


def run_pipeline_on_case(case: dict, model: str) -> list[dict]:
    """Run the full pipeline on one gold case. Returns list of result dicts."""
    sow_text = load_sow_text(case["sow_file"])
    message  = case["message"]

    # S1: Extract SOW (cached per SOW file)
    facts, warnings = get_cached_sow(case["sow_file"], sow_text, model=model)

    # S3: Split request
    split = split_requests(message, model=model)

    results = []
    for req in split.requests:
        # S4: Match
        try:
            match = match_request(req, sow_text, facts, model=model)
        except Exception as e:
            results.append({"predicted": "unverified", "error": str(e)})
            continue

        # S5: Rules
        decision = decide(
            request=req, match=match, sow=facts,
            quota={"revisions_used": 0},
            issues=[], issue_ids=[],
            sow_text=sow_text, client_message=message,
        )

        # S6: Pricing
        hrs = estimate_hours(req.type, match.size)
        prc = price(hrs, 25.0)  # default rate for eval
        decision.hours = hrs
        decision.price = prc

        results.append({
            "request_text":  req.request_text,
            "predicted":     decision.final_verdict,
            "llm_verdict":   decision.llm_verdict,
            "rule_ids":      decision.rule_ids,
            "quote_methods": decision.quote_methods,
            "confidence":    decision.confidence,
            "hours":         hrs,
            "price":         prc,
        })
    return results


def run_baseline_on_case(case: dict, model: str) -> list[dict]:
    """Run the single-prompt baseline on one gold case."""
    sow_text = load_sow_text(case["sow_file"])
    message  = case["message"]

    try:
        result = run_baseline(sow_text, message, model=model)
    except Exception as e:
        return [{"predicted": "unverified", "error": str(e)}]

    return [
        {
            "request_text": r.text,
            "predicted":    r.verdict,
            "sow_quote":    r.sow_quote,
            "client_quote": r.client_quote,
        }
        for r in result.requests
    ]


def main():
    parser = argparse.ArgumentParser(description="Scope-Creep Catcher Evaluator")
    parser.add_argument("--model", default="gemma2:2b", help="Ollama model tag")
    parser.add_argument("--mode",  choices=["pipeline", "baseline"], default="pipeline")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Scope-Creep Catcher Eval")
    print(f"  Model: {args.model}  |  Mode: {args.mode}  |  Split: {args.split}")
    print(f"{'='*60}\n")

    split_filter = args.split if args.split != "all" else None
    if split_filter:
        cases = load_gold_cases(split_filter)
    else:
        cases_path = GOLD_DIR / "cases.json"
        with cases_path.open(encoding="utf-8") as fh:
            cases = json.load(fh)

    if not cases:
        print(f"No cases found for split='{args.split}'")
        return

    all_predicted:   list[str] = []
    all_gold:        list[str] = []
    all_difficulties: list[str] = []
    raw_results = []

    total_cases = sum(len(c.get("requests", [])) for c in cases)
    print(f"Running {args.mode} on {len(cases)} messages ({total_cases} labeled requests)\n")

    for case_i, case in enumerate(cases, 1):
        print(f"[{case_i}/{len(cases)}] SOW={case['sow']} | {case['message'][:60]}...")

        t0 = time.perf_counter()
        if args.mode == "pipeline":
            preds = run_pipeline_on_case(case, model=args.model)
        else:
            preds = run_baseline_on_case(case, model=args.model)
        elapsed = time.perf_counter() - t0

        gold_requests = case.get("requests", [])

        # Match predictions to gold requests (by index / text similarity)
        for i, gold_req in enumerate(gold_requests):
            gold_label = gold_req["label"]
            difficulty = gold_req.get("difficulty", "unknown")
            all_gold.append(gold_label)
            all_difficulties.append(difficulty)

            if i < len(preds):
                pred_label = preds[i].get("predicted", "unverified")
            else:
                pred_label = "unverified"

            all_predicted.append(pred_label)

            match_char = "✓" if pred_label == gold_label else "✗"
            print(
                f"   {match_char} [{gold_label:12s}] → [{pred_label:12s}] "
                f"({difficulty}) | {gold_req['text'][:50]}"
            )

        raw_results.append({
            "case": case_i,
            "sow": case["sow"],
            "message": case["message"],
            "elapsed_s": round(elapsed, 2),
            "predictions": preds,
            "gold": gold_requests,
        })
        print(f"   ({elapsed:.1f}s)\n")

    # ── Compute metrics ───────────────────────────────────────────────────────
    acc  = accuracy(all_predicted, all_gold)
    far  = false_accusation_rate(all_predicted, all_gold)
    cm   = confusion_matrix(all_predicted, all_gold)
    diff = per_difficulty(all_predicted, all_gold, all_difficulties)

    print(f"\n{'='*60}")
    print(f"  Results: {args.model} | {args.mode} | {args.split}")
    print(f"{'='*60}")
    print(f"  Overall accuracy:        {acc:.1%}")
    print(f"  False accusation rate:   {far:.1%}")
    print(f"  Per difficulty:          {diff}")
    print()
    print("  Confusion matrix:")
    print(format_confusion_matrix_md(cm))
    print(f"{'='*60}\n")

    # ── Save raw results ──────────────────────────────────────────────────────
    RESULTS_DIR.mkdir(exist_ok=True)
    raw_path = RESULTS_DIR / "raw" / f"eval_{args.model.replace(':', '-')}_{args.mode}_{args.split}.json"
    raw_path.parent.mkdir(exist_ok=True)

    summary = {
        "model":               args.model,
        "mode":                args.mode,
        "split":               args.split,
        "n_requests":          len(all_gold),
        "accuracy":            acc,
        "false_accusation_rate": far,
        "per_difficulty":      diff,
        "confusion_matrix":    cm,
        "raw":                 raw_results,
    }
    with raw_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(f"Raw results saved to: {raw_path}")


if __name__ == "__main__":
    main()
