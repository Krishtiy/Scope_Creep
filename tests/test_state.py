"""
tests/test_state.py
Unit tests for engine/state.py:
- Project creation, persistence, reload
- Revision counter increment
- Log appending, status updates, markdown export
"""
import pytest
from pathlib import Path
from engine.state import (
    new_project,
    save_project,
    load_project,
    increment_revision,
    add_log_entry,
    update_log_status,
    export_log_markdown,
)
from engine.schemas import Decision


def _dummy_decision(verdict: str = "out_of_scope", hours: float = 4.0, price: float = 100.0) -> Decision:
    return Decision(
        request_text="Add dark mode toggle",
        final_verdict=verdict,
        llm_verdict=verdict,
        rule_ids=["R5"],
        overridden_by_rule=False,
        sow_quote=None,
        client_quote="Add dark mode toggle",
        quote_methods={"sow": "none", "client": "exact"},
        linked_ambiguity=None,
        consumes_revision=False,
        confidence="high",
        hours=hours,
        price=price,
    )


class TestProjectLifecycle:
    def test_new_and_save_and_load_project(self, tmp_path, monkeypatch):
        # Override PROJECTS_DIR to tmp_path
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        state = new_project(
            name="Test Bakery",
            currency="USD",
            hourly_rate=30.0,
            contract_price=1200.0,
            sow_text="Home, About, Contact",
        )
        assert state["name"] == "Test Bakery"
        assert state["hourly_rate"] == 30.0
        assert state["quota"]["revisions_used"] == 0
        assert len(state["log"]) == 0

        save_project(state)
        loaded = load_project(state["project_id"])
        assert loaded is not None
        assert loaded["project_id"] == state["project_id"]
        assert loaded["name"] == "Test Bakery"

    def test_increment_revision(self):
        state = new_project("Test", "USD", 25.0, 500.0, "SOW")
        assert state["quota"]["revisions_used"] == 0
        cnt1 = increment_revision(state)
        assert cnt1 == 1
        assert state["quota"]["revisions_used"] == 1
        cnt2 = increment_revision(state)
        assert cnt2 == 2
        assert state["quota"]["revisions_used"] == 2

    def test_add_log_and_update_status(self):
        state = new_project("Test", "USD", 25.0, 500.0, "SOW")
        d = _dummy_decision()
        entry = add_log_entry(state, d, message_text="Can you add dark mode?")

        assert len(state["log"]) == 1
        assert state["log"][0]["request"] == "Add dark mode toggle"
        assert state["log"][0]["verdict"] == "out_of_scope"
        assert state["log"][0]["status"] == "pending"

        update_log_status(state, 0, "approved")
        assert state["log"][0]["status"] == "approved"

    def test_export_log_markdown(self):
        state = new_project("Test", "USD", 25.0, 500.0, "SOW")
        empty_md = export_log_markdown(state)
        assert "No items logged yet" in empty_md

        d = _dummy_decision()
        add_log_entry(state, d, "Client says add dark mode")
        md = export_log_markdown(state)
        assert "| Date | Request | Verdict | Hours | Price | Status |" in md
        assert "Add dark mode toggle" in md
        assert "out_of_scope" in md
        assert "4.0h" in md
        assert "$100.00" in md
