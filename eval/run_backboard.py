"""
eval/run_backboard.py
Cloud evaluation harness using Backboard.io (Partner Technology).
Compares local small open-weight models against larger models hosted on Backboard
using our synthetic gold set data.

Privacy Guarantee:
  Only synthetic gold set cases (data/gold/) are ever sent to Backboard.
  Real freelancer contracts in data/projects/ NEVER leave the laptop.

Usage:
  python -m eval.run_backboard --split test
  python -m eval.run_backboard --split dev --model meta-llama/llama-3.1-70b-instruct
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.config import GOLD_DIR, RESULTS_DIR, RAW_DIR
from eval.metrics import accuracy, false_accusation_rate, confusion_matrix, format_confusion_matrix_md


def get_api_key() -> str | None:
    """Retrieve Backboard API key from environment or .env file."""
    api_key = os.environ.get("BACKBOARD_API_KEY")
    if api_key:
        return api_key.strip()

    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BACKBOARD_API_KEY=") and not line.startswith("#"):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    return None


def print_setup_instructions() -> None:
    print("=" * 70)
    print("BACKBOARD.IO EVALUATION SETUP GUIDE (HACKTOBERFEST PARTNER)")
    print("=" * 70)
    print("Backboard API key not detected. To run this evaluation:\n")
    print("Step 1: Sign up for an account at: https://app.backboard.io")
    print("Step 2: Claim Hacktoberfest promo credits (~$5 free credit) at:")
    print("        https://hacktoberfest.com/my/promos")
    print("Step 3: Generate an API key from your Backboard dashboard.")
    print("Step 4: Create a '.env' file in the project root with:")
    print("        BACKBOARD_API_KEY=your_key_here")
    print("        or run in PowerShell:")
    print("        $env:BACKBOARD_API_KEY='your_key_here'")
    print("Step 5: Re-run this evaluation command:")
    print("        python -m eval.run_backboard --split test\n")
    print("NOTE: Backboard is strictly for synthetic gold set evaluation.")
    print("      No real user contracts or data ever leave your laptop.")
    print("=" * 70)


def load_gold_cases(split: str) -> list[dict]:
    cases_path = GOLD_DIR / "cases.json"
    with cases_path.open(encoding="utf-8") as fh:
        all_cases = json.load(fh)
    return [c for c in all_cases if c.get("split") == split]


def load_sow_text(sow_file: str) -> str:
    p = GOLD_DIR / "sows" / sow_file
    return p.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backboard AI eval harness")
    parser.add_argument("--split", choices=["dev", "test"], default="test", help="Dataset split")
    parser.add_argument("--model", default="meta-llama/llama-3.1-70b-instruct", help="Model name on Backboard")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print_setup_instructions()
        sys.exit(0)

    try:
        from backboard import BackboardClient
    except ImportError:
        print("ERROR: backboard-sdk is not installed. Run: pip install backboard-sdk")
        sys.exit(1)

    print(f"\n[Backboard Eval] Initializing BackboardClient for model: {args.model}")
    client = BackboardClient(api_key=api_key)

    cases = load_gold_cases(args.split)
    print(f"[Backboard Eval] Running on split '{args.split}' ({len(cases)} cases)...")

    predictions, gold_labels = [], []
    detailed_results = []

    # System instruction for baseline classification on Backboard
    system_prompt = (
        "You are an expert contract reviewer. Given a Statement of Work (SOW) "
        "and a client message, classify each request as exactly one of:\n"
        "- in_scope\n"
        "- out_of_scope\n"
        "- gray_area\n"
        "Return valid JSON with key 'verdicts': list of strings."
    )

    try:
        assistant = client.create_assistant(
            name=f"scope-eval-{args.split}",
            description="Synthetic evaluation assistant for Scope-Creep Catcher",
            system_prompt=system_prompt,
        )
        assistant_id = assistant.id
    except Exception as e:
        print(f"Failed to create assistant on Backboard: {e}")
        sys.exit(1)

    try:
        for idx, case in enumerate(cases, 1):
            sow_text = load_sow_text(case["sow_file"])
            msg = case["message"]
            user_content = f"SOW:\n{sow_text}\n\nClient message:\n{msg}"

            thread = client.create_thread(assistant_id=assistant_id)
            response = client.send_message(
                thread_id=thread.id,
                content=user_content,
                model=args.model,
            )

            # Process response and extract predictions
            reply_text = getattr(response, "content", str(response))
            for req in case.get("requests", []):
                gold = req.get("label", "in_scope")
                gold_labels.append(gold)
                # Parse or default
                pred = "gray_area"
                if "out_of_scope" in reply_text.lower():
                    pred = "out_of_scope"
                elif "in_scope" in reply_text.lower():
                    pred = "in_scope"
                predictions.append(pred)

                detailed_results.append({
                    "request": req.get("text"),
                    "gold": gold,
                    "predicted": pred,
                })

        acc = accuracy(predictions, gold_labels)
        far = false_accusation_rate(predictions, gold_labels)
        cm = confusion_matrix(predictions, gold_labels)

        print("\n" + "=" * 50)
        print(f"BACKBOARD EVALUATION RESULTS ({args.model})")
        print("=" * 50)
        print(f"Total requests:         {len(gold_labels)}")
        print(f"Accuracy:               {acc * 100:.1f}%")
        print(f"False Accusation Rate:  {far * 100:.1f}%\n")
        print("Confusion Matrix:")
        print(format_confusion_matrix_md(cm))

        out_path = RAW_DIR / f"backboard_{args.split}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump({
                "model": args.model,
                "split": args.split,
                "accuracy": acc,
                "false_accusation_rate": far,
                "confusion_matrix": cm,
                "details": detailed_results,
            }, fh, indent=2)
        print(f"\nSaved raw results to: {out_path}")

    finally:
        try:
            client.delete_assistant(assistant_id=assistant_id)
        except Exception:
            pass


if __name__ == "__main__":
    main()
