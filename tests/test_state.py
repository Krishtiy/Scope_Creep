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


class TestSlugify:
    def test_basic_slug(self):
        from engine.state import slugify
        assert slugify("Apex Fitness") == "apex-fitness"
        assert slugify("My Cool Project 123") == "my-cool-project-123"

    def test_accents_and_unicode(self):
        from engine.state import slugify
        assert slugify("Café au Lait") == "cafe-au-lait"
        assert slugify("Crème Brûlée & Co.") == "creme-brulee-co"

    def test_special_chars_and_collapse(self):
        from engine.state import slugify
        assert slugify("Web & Brand Refresh! @#$") == "web-brand-refresh"
        assert slugify("---multiple---hyphens---") == "multiple-hyphens"

    def test_empty_and_fallback(self):
        from engine.state import slugify
        assert slugify("") == "project"
        assert slugify("   ") == "project"
        assert slugify("---") == "project"
        assert slugify("!@#$%^&*()") == "project"

    def test_max_length_clamped(self):
        from engine.state import slugify
        long_name = "a" * 100
        slug = slugify(long_name)
        assert len(slug) <= 63
        assert slug == "a" * 63

    def test_windows_reserved_names(self):
        from engine.state import slugify
        assert slugify("CON") == "con-project"
        assert slugify("prn") == "prn-project"
        assert slugify("aux") == "aux-project"
        assert slugify("NUL") == "nul-project"
        assert slugify("com1") == "com1-project"


class TestPathSecurity:
    def test_valid_project_path(self, tmp_path, monkeypatch):
        from engine.state import project_path
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)
        p = project_path("my-safe-project-123")
        assert p.parent == tmp_path.resolve()
        assert p.name == "my-safe-project-123.json"

    def test_reject_empty_or_non_string(self):
        from engine.state import project_path
        with pytest.raises(ValueError, match="non-empty string"):
            project_path("")
        with pytest.raises(ValueError, match="non-empty string"):
            project_path(None)  # type: ignore

    def test_reject_path_traversal(self, tmp_path, monkeypatch):
        from engine.state import project_path
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        traversal_attempts = [
            "../secret",
            "../../etc/passwd",
            "..\\windows\\system32",
            "sub/dir/proj",
            "sub\\dir\\proj",
            "....//attack",
        ]
        for bad_id in traversal_attempts:
            with pytest.raises(ValueError):
                project_path(bad_id)


class TestAtomicSaveAndBackup:
    def test_atomic_save_and_backup_created(self, tmp_path, monkeypatch):
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        state = new_project("Bakery", "USD", 40.0, 800.0, "SOW 1")
        pid = state["project_id"]
        save_project(state)

        json_file = tmp_path / f"{pid}.json"
        bak_file = tmp_path / f"{pid}.json.bak"
        assert json_file.exists()
        assert not bak_file.exists()  # first save, no previous file to backup

        # Second save (modify state)
        state["contract_price"] = 1200.0
        save_project(state)

        assert json_file.exists()
        assert bak_file.exists()  # backup created!
        
        # Verify content
        import json
        with bak_file.open(encoding="utf-8") as fh:
            bak_data = json.load(fh)
        assert bak_data["contract_price"] == 800.0

        with json_file.open(encoding="utf-8") as fh:
            new_data = json.load(fh)
        assert new_data["contract_price"] == 1200.0


class TestProjectCorruptAndFallback:
    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)
        assert load_project("does-not-exist") is None

    def test_corrupt_file_without_backup_raises_error(self, tmp_path, monkeypatch):
        from engine.state import ProjectLoadError
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        corrupt_file = tmp_path / "corrupt-proj.json"
        corrupt_file.write_text("{ this is bad json", encoding="utf-8")

        with pytest.raises(ProjectLoadError, match="Corrupted project file"):
            load_project("corrupt-proj")

    def test_corrupt_file_recovers_from_backup(self, tmp_path, monkeypatch):
        import json
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        state = new_project("Fallback Bakery", "USD", 50.0, 1000.0, "SOW")
        pid = state["project_id"]
        save_project(state)
        # Second save creates .bak
        state["hourly_rate"] = 60.0
        save_project(state)

        json_file = tmp_path / f"{pid}.json"
        # Intentionally corrupt main file
        json_file.write_text("CORRUPTED_ZERO_BYTE_SIMULATION", encoding="utf-8")

        loaded = load_project(pid)
        assert loaded is not None
        assert loaded["name"] == "Fallback Bakery"
        assert loaded["hourly_rate"] == 50.0  # restored from backup!


class TestListProjects:
    def test_list_projects_metadata_and_order(self, tmp_path, monkeypatch):
        from engine.state import list_projects, set_sow
        from engine.schemas import SOWFacts
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        p1 = new_project("Alpha", "USD", 50.0, 500.0, "SOW Alpha")
        p1["updated_at"] = "2026-10-01T10:00:00"
        save_project(p1)

        p2 = new_project("Beta", "USD", 60.0, 600.0, "SOW Beta")
        p2["updated_at"] = "2026-10-02T10:00:00"
        facts = SOWFacts(pages=["Home"])
        set_sow(p2, facts)
        save_project(p2)

        projects = list_projects()
        assert len(projects) == 2
        # Beta updated later, should be first
        assert projects[0]["name"] == "Beta"
        assert projects[0]["has_sow"] is True
        assert projects[1]["name"] == "Alpha"
        assert projects[1]["has_sow"] is False


class TestLastOpened:
    def test_get_and_set_last_opened(self, tmp_path, monkeypatch):
        from engine.state import get_last_opened, set_last_opened
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        # Initially None
        assert get_last_opened() is None

        # Setting when file doesn't exist returns None
        set_last_opened("ghost-project")
        assert get_last_opened() is None

        # Create real project and set
        state = new_project("Real Project", "USD", 50.0, 1000.0, "SOW")
        pid = state["project_id"]
        save_project(state)

        set_last_opened(pid)
        assert get_last_opened() == pid


class TestDeleteProject:
    def test_delete_existing_project_and_backup(self, tmp_path, monkeypatch):
        from engine.state import delete_project, get_last_opened, set_last_opened
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)

        state = new_project("Delete Me", "USD", 50.0, 1000.0, "SOW")
        pid = state["project_id"]
        save_project(state)
        # 2nd save to create backup
        state["contract_price"] = 1200.0
        save_project(state)

        json_file = tmp_path / f"{pid}.json"
        bak_file = tmp_path / f"{pid}.json.bak"
        assert json_file.exists()
        assert bak_file.exists()

        set_last_opened(pid)
        assert get_last_opened() == pid

        # Delete
        success = delete_project(pid)
        assert success is True
        assert not json_file.exists()
        assert not bak_file.exists()
        assert get_last_opened() is None

    def test_delete_nonexistent_project(self, tmp_path, monkeypatch):
        from engine.state import delete_project
        monkeypatch.setattr("engine.state.PROJECTS_DIR", tmp_path)
        assert delete_project("does-not-exist") is False
