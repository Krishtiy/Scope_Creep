"""
engine/state.py
S8: Project state management — load, save, and update the project JSON file.
Manages the quota counter and the decision log.
Data lives in data/projects/<project_id>.json and is git-ignored.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import PROJECTS_DIR
from .schemas import SOWFacts, StressIssue, Decision


def _project_path(project_id: str) -> Path:
    return PROJECTS_DIR / f"{project_id}.json"


def new_project(
    name: str,
    currency: str,
    hourly_rate: float,
    contract_price: float,
    sow_text: str,
) -> dict:
    """Create a new project state dict (not saved yet)."""
    return {
        "project_id":     name.lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:6],
        "name":           name,
        "currency":       currency,
        "hourly_rate":    hourly_rate,
        "contract_price": contract_price,
        "sow_text":       sow_text,
        "sow":            None,       # SOWFacts dict, filled after extraction
        "stress":         [],         # list of {id, issue_dict, status: "open"}
        "quota":          {"revisions_used": 0},
        "log":            [],         # list of log entries
        "created_at":     datetime.now().isoformat(),
        "updated_at":     datetime.now().isoformat(),
    }


def save_project(state: dict) -> None:
    """Persist the project state to disk."""
    state["updated_at"] = datetime.now().isoformat()
    p = _project_path(state["project_id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


def load_project(project_id: str) -> Optional[dict]:
    """Load a project from disk. Returns None if not found."""
    p = _project_path(project_id)
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def list_projects() -> list[dict]:
    """Return summary dicts for all saved projects."""
    projects = []
    for p in PROJECTS_DIR.glob("*.json"):
        try:
            with p.open(encoding="utf-8") as fh:
                data = json.load(fh)
            projects.append({
                "project_id":     data.get("project_id"),
                "name":           data.get("name", p.stem),
                "created_at":     data.get("created_at"),
                "updated_at":     data.get("updated_at"),
            })
        except (json.JSONDecodeError, KeyError):
            pass
    return sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True)


def set_sow(state: dict, facts: SOWFacts) -> None:
    """Store extracted SOW facts in project state."""
    state["sow"] = facts.model_dump()


def set_stress(state: dict, issues: list[StressIssue], ids: list[str]) -> None:
    """Store stress-test results in project state."""
    state["stress"] = [
        {"id": ids[i], "issue": issues[i].model_dump(), "status": "open"}
        for i in range(len(issues))
    ]


def add_log_entry(
    state: dict,
    decision: Decision,
    message_text: str,
) -> dict:
    """
    Append a decision to the project log.

    Returns the log entry dict.
    """
    entry = {
        "date":          datetime.now().strftime("%Y-%m-%d"),
        "request":       decision.request_text,
        "verdict":       decision.final_verdict,
        "llm_verdict":   decision.llm_verdict,
        "rule_ids":      decision.rule_ids,
        "hours":         decision.hours,
        "price":         decision.price,
        "sow_quote":     decision.sow_quote,
        "client_quote":  decision.client_quote,
        "quote_methods": decision.quote_methods,
        "confidence":    decision.confidence,
        "status":        "pending",    # pending | approved | declined
        "client_message_excerpt": message_text[:200],
    }
    state["log"].append(entry)
    return entry


def increment_revision(state: dict) -> int:
    """
    Increment the revision counter.
    The LLM proposes consumes_revision; only the user action calls this.

    Returns the new revisions_used count.
    """
    state["quota"]["revisions_used"] = state["quota"].get("revisions_used", 0) + 1
    return state["quota"]["revisions_used"]


def update_log_status(state: dict, index: int, status: str) -> None:
    """Update the status of a log entry (pending | approved | declined)."""
    if 0 <= index < len(state["log"]):
        state["log"][index]["status"] = status


def export_log_markdown(state: dict) -> str:
    """Export the project log as a Markdown table."""
    log = state.get("log", [])
    if not log:
        return "_No items logged yet._"

    header = "| Date | Request | Verdict | Hours | Price | Status |\n"
    sep    = "|------|---------|---------|-------|-------|--------|\n"
    rows   = []
    currency = state.get("currency", "USD")
    symbol   = "$" if currency == "USD" else currency

    for e in log:
        rows.append(
            f"| {e['date']} | {e['request'][:60]} | {e['verdict']} | "
            f"{e['hours']}h | {symbol}{e['price']:.2f} | {e['status']} |"
        )

    return header + sep + "\n".join(rows)
