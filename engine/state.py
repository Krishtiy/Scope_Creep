"""
engine/state.py
S8: Project state management — load, save, and update the project JSON file.
Manages the quota counter and the decision log.
Data lives in data/projects/<project_id>.json and is git-ignored.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import PROJECTS_DIR
from .schemas import SOWFacts, StressIssue, Decision

WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
}


class ProjectLoadError(Exception):
    """Raised when a project file cannot be loaded or is corrupted."""
    pass


def slugify(name: str) -> str:
    """
    Convert a project name into a safe filesystem slug:
    - Lowercase
    - Unicode accents normalized to ASCII
    - Non-alphanumeric characters replaced with hyphens
    - Consecutive hyphens collapsed
    - Leading/trailing hyphens stripped
    - Max 63 characters
    - Fallback to 'project' if empty
    - Windows reserved names appended with '-project'
    """
    if not name:
        return "project"
    # Normalize unicode to ASCII
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Replace non-alphanumeric with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    if not text:
        text = "project"
    # Clamp length
    text = text[:63].rstrip("-")
    if not text:
        text = "project"
    # Check Windows reserved names
    if text in WINDOWS_RESERVED:
        text = f"{text}-project"
    return text


def project_path(project_id: str) -> Path:
    """
    Return the Path for a project JSON file.
    Rejects path traversal attempts.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("Invalid project_id: must be a non-empty string.")

    # Strictly forbid path traversal
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        raise ValueError(f"Path traversal detected in project_id: {project_id!r}")

    p = (PROJECTS_DIR / f"{project_id}.json").resolve()
    base_dir = PROJECTS_DIR.resolve()

    # Must reside strictly within PROJECTS_DIR
    if p.parent != base_dir:
        raise ValueError(f"Invalid project path resolution: {project_id!r}")

    return p


_project_path = project_path


def new_project(
    name: str,
    currency: str,
    hourly_rate: float,
    contract_price: float,
    sow_text: str,
) -> dict:
    """Create a new project state dict (not saved yet)."""
    slug = slugify(name)
    suffix = uuid.uuid4().hex[:6]
    project_id = f"{slug}-{suffix}"
    return {
        "project_id":     project_id,
        "name":           name,
        "currency":       currency,
        "hourly_rate":    hourly_rate,
        "contract_price": contract_price,
        "sow_text":       sow_text,
        "sow":            None,       # SOWFacts dict, filled after extraction
        "stress":         [],         # list of {id, issue: issue_dict, status: "open"}
        "quota":          {"revisions_used": 0},
        "log":            [],         # list of log entries
        "created_at":     datetime.now().isoformat(),
        "updated_at":     datetime.now().isoformat(),
    }


def save_project(state: dict) -> None:
    """
    Persist the project state to disk atomically.
    Uses tempfile + os.replace and creates a .bak backup.
    """
    state["updated_at"] = datetime.now().isoformat()
    p = project_path(state["project_id"])
    p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write to temp file in same directory
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=p.parent, prefix="proj_", suffix=".tmp")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())

        # 2. If target exists, backup to .bak
        bak_path = p.with_suffix(".json.bak")
        if p.exists():
            try:
                shutil.copy2(p, bak_path)
            except Exception:
                pass

        # 3. Atomic rename/replace
        os.replace(tmp_path, p)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def load_project(project_id: str) -> Optional[dict]:
    """
    Load a project from disk.
    Returns None if not found.
    Raises ProjectLoadError if file is corrupted.
    """
    p = project_path(project_id)
    bak_path = p.with_suffix(".json.bak")

    target_file = None
    if p.exists():
        target_file = p
    elif bak_path.exists():
        target_file = bak_path
    else:
        return None

    try:
        with target_file.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        # If main file failed and backup exists, try backup
        if target_file == p and bak_path.exists():
            try:
                with bak_path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                raise ProjectLoadError(f"Corrupted project file and backup for '{project_id}': {e}") from e
        else:
            raise ProjectLoadError(f"Corrupted project file for '{project_id}': {e}") from e

    # Backward compatibility / schema defaults
    if not isinstance(data, dict):
        raise ProjectLoadError(f"Invalid project format for '{project_id}': root must be a dict.")

    data.setdefault("project_id", project_id)
    data.setdefault("name", data.get("project_id", project_id))
    data.setdefault("currency", "USD")
    data.setdefault("hourly_rate", 50.0)
    data.setdefault("contract_price", 1000.0)
    data.setdefault("sow_text", "")
    data.setdefault("sow", None)
    data.setdefault("stress", [])
    data.setdefault("quota", {"revisions_used": 0})
    data.setdefault("log", [])
    data.setdefault("created_at", datetime.now().isoformat())
    data.setdefault("updated_at", datetime.now().isoformat())

    return data


def list_projects() -> list[dict]:
    """Return summary metadata for all saved projects, sorted by updated_at descending."""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for p in PROJECTS_DIR.glob("*.json"):
        if p.name.startswith("."):
            continue
        try:
            with p.open(encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                continue
            projects.append({
                "project_id":  data.get("project_id", p.stem),
                "name":        data.get("name", p.stem),
                "created_at":  data.get("created_at"),
                "updated_at":  data.get("updated_at", ""),
                "has_sow":     bool(data.get("sow")),
                "has_stress":  bool(data.get("stress")),
                "log_count":   len(data.get("log", [])),
            })
        except Exception:
            pass
    return sorted(projects, key=lambda x: x.get("updated_at") or "", reverse=True)


def get_last_opened() -> Optional[str]:
    """Return the project_id of the last opened project, or None."""
    try:
        last_file = PROJECTS_DIR / ".last_opened"
        if last_file.exists():
            pid = last_file.read_text(encoding="utf-8").strip()
            if pid:
                p = PROJECTS_DIR / f"{pid}.json"
                if p.exists():
                    return pid
    except Exception:
        pass
    return None


def set_last_opened(project_id: str) -> None:
    """Record the project_id as the last opened project."""
    try:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        last_file = PROJECTS_DIR / ".last_opened"
        last_file.write_text(project_id.strip(), encoding="utf-8")
    except Exception:
        pass


def delete_project(project_id: str) -> bool:
    """
    Permanently delete a project and its backup from disk.
    Also clears .last_opened if this was the last opened project.
    Returns True if the project file existed and was deleted, False otherwise.
    """
    p = project_path(project_id)
    bak_path = p.with_suffix(".json.bak")
    deleted = False

    if p.exists():
        p.unlink()
        deleted = True
    if bak_path.exists():
        try:
            bak_path.unlink()
        except OSError:
            pass

    try:
        last_file = PROJECTS_DIR / ".last_opened"
        if last_file.exists():
            current_last = last_file.read_text(encoding="utf-8").strip()
            if current_last == project_id:
                last_file.unlink()
    except Exception:
        pass

    return deleted


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
