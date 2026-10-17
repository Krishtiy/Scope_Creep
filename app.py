"""
app.py — Scope-Creep Catcher Streamlit UI (S9)
Three tabs: Stress Test | Check Request | Log
Top bar: running summary of extra work flagged.

Disclaimer: This is a text-analysis aid. It does not give legal advice.
Hour and cost figures are illustrative estimates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Ensure engine is importable when run from project root
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.config import MODEL
from engine.sow import extract_sow
from engine.stress_test import run_stress_test
from engine.checker import split_requests, match_request
from engine.rules import decide
from engine.pricing import estimate_hours, price, summary as pricing_summary
import importlib
from engine.drafter import draft_reply
from engine import state as project_state
importlib.reload(project_state)
from engine.schemas import SOWFacts, StressIssue

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scope-Creep Catcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────────────
if "project" not in st.session_state:
    st.session_state.project = None
if "sow_facts" not in st.session_state:
    st.session_state.sow_facts = None
if "stress_issues" not in st.session_state:
    st.session_state.stress_issues = []
if "stress_ids" not in st.session_state:
    st.session_state.stress_ids = []
if "decisions" not in st.session_state:
    st.session_state.decisions = []
if "last_message" not in st.session_state:
    st.session_state.last_message = ""
if "draft_reply" not in st.session_state:
    st.session_state.draft_reply = ""
if "change_order" not in st.session_state:
    st.session_state.change_order = ""
if "draft_version" not in st.session_state:
    st.session_state.draft_version = 0
if "current_page" not in st.session_state:
    st.session_state.current_page = "⚙️ Current Project"

# ── Helpers ───────────────────────────────────────────────────────────────────
VERDICT_COLORS = {
    "in_scope":    "🟢",
    "out_of_scope": "🔴",
    "gray_area":   "🟡",
    "unverified":  "⚠️",
}
SEVERITY_COLORS = {
    "high":   "🔴",
    "medium": "🟡",
    "low":    "🔵",
}


def get_project() -> dict | None:
    return st.session_state.project


def save_state():
    if st.session_state.project:
        project_state.save_project(st.session_state.project)


def load_project_into_session(proj: dict):
    """Hydrate Streamlit session state from a loaded project dict with zero LLM calls."""
    st.session_state.project = proj

    # Hydrate SOW Facts
    if proj.get("sow"):
        try:
            st.session_state.sow_facts = SOWFacts.model_validate(proj["sow"])
        except Exception:
            st.session_state.sow_facts = None
    else:
        st.session_state.sow_facts = None

    # Hydrate Stress Test Results
    if proj.get("stress"):
        try:
            st.session_state.stress_issues = [
                StressIssue.model_validate(item["issue"]) for item in proj["stress"]
            ]
            st.session_state.stress_ids = [item["id"] for item in proj["stress"]]
        except Exception:
            st.session_state.stress_issues = []
            st.session_state.stress_ids = []
    else:
        st.session_state.stress_issues = []
        st.session_state.stress_ids = []

    st.session_state.decisions = []
    st.session_state.last_message = ""
    st.session_state.draft_reply = ""
    st.session_state.change_order = ""
    st.session_state.draft_version = 0

    if proj.get("project_id"):
        project_state.set_last_opened(proj["project_id"])
        st.query_params["project"] = proj["project_id"]


# ── Project auto-load on browser refresh (URL query params) ───────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    target_id = st.query_params.get("project")
    if target_id:
        try:
            loaded_proj = project_state.load_project(target_id)
            if loaded_proj:
                load_project_into_session(loaded_proj)
        except Exception:
            pass


def render_all_projects_view():
    st.header("📁 All Saved Projects")
    st.caption("Manage, open, or delete your client projects stored locally on this machine.")

    saved_projects = project_state.list_projects()

    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.write(f"**Total Projects:** {len(saved_projects)}")
    with col_hdr2:
        if st.button("➕ Create New Project", type="primary", use_container_width=True):
            st.session_state.project = None
            st.session_state.sow_facts = None
            st.session_state.stress_issues = []
            st.session_state.stress_ids = []
            st.session_state.decisions = []
            st.session_state.last_message = ""
            st.session_state.draft_reply = ""
            st.session_state.change_order = ""
            if "project" in st.query_params:
                del st.query_params["project"]
            if "view" in st.query_params:
                del st.query_params["view"]
            st.rerun()

    st.divider()

    if not saved_projects:
        st.info("No saved projects found. Click '➕ Create New Project' to get started!")
        return

    curr_proj = st.session_state.project
    active_pid = curr_proj.get("project_id") if curr_proj else None

    for p in saved_projects:
        pid = p["project_id"]
        is_active = (pid == active_pid)
        updated_str = p.get("updated_at", "")[:16].replace("T", " ") if p.get("updated_at") else "Unknown"

        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                title_badge = " *(Active)*" if is_active else ""
                st.markdown(f"### 📁 **{p['name']}**{title_badge}")
                st.caption(f"**ID:** `{pid}` | **Last modified:** {updated_str}")

                # Status badges
                badge_sow = "🟢 SOW Extracted" if p.get("has_sow") else "⚪ No SOW"
                badge_stress = "🔍 Stress Tested" if p.get("has_stress") else "⚪ No Stress Test"
                badge_log = f"📊 {p.get('log_count', 0)} log entries"
                st.markdown(f"`{badge_sow}` &nbsp;&nbsp; `{badge_stress}` &nbsp;&nbsp; `{badge_log}`")

            with cols[1]:
                if is_active:
                    st.button("✅ Active", key=f"active_btn_{pid}", disabled=True, use_container_width=True)
                else:
                    if st.button("📂 Open", key=f"open_btn_{pid}", type="primary", use_container_width=True):
                        try:
                            full_proj = project_state.load_project(pid)
                            if full_proj:
                                load_project_into_session(full_proj)
                                if "view" in st.query_params:
                                    del st.query_params["view"]
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to open project: {e}")

            with cols[2]:
                with st.popover("🗑️ Delete", use_container_width=True):
                    st.markdown(f"**Delete '{p['name']}'?**")
                    st.caption("This will permanently delete this project file and all logs.")
                    if st.button("Yes, Delete", key=f"del_confirm_{pid}", type="secondary", use_container_width=True):
                        project_state.delete_project(pid)
                        if is_active:
                            st.session_state.project = None
                            st.session_state.sow_facts = None
                            st.session_state.stress_issues = []
                            st.session_state.stress_ids = []
                            if "project" in st.query_params:
                                del st.query_params["project"]
                        st.success(f"Deleted '{p['name']}'.")
                        st.rerun()


# ── Sidebar setup ─────────────────────────────────────────────────────────────
with st.sidebar:
    is_projects_view = (st.query_params.get("view") == "projects")

    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button(
            "⚙️ Workspace",
            type="primary" if not is_projects_view else "secondary",
            use_container_width=True,
        ):
            if "view" in st.query_params:
                del st.query_params["view"]
            st.rerun()
    with col_nav2:
        if st.button(
            "📁 All Projects",
            type="primary" if is_projects_view else "secondary",
            use_container_width=True,
        ):
            st.query_params["view"] = "projects"
            st.rerun()

    st.divider()

    if is_projects_view:
        st.title("📁 All Projects")
        st.caption("View and manage your saved projects.")
        if st.button("➕ Create New Project", type="primary", use_container_width=True):
            st.session_state.project = None
            st.session_state.sow_facts = None
            st.session_state.stress_issues = []
            st.session_state.stress_ids = []
            st.session_state.decisions = []
            st.session_state.last_message = ""
            st.session_state.draft_reply = ""
            st.session_state.change_order = ""
            if "project" in st.query_params:
                del st.query_params["project"]
            if "view" in st.query_params:
                del st.query_params["view"]
            st.rerun()
    else:
        st.title("⚙️ Project Setup")

        curr_proj = st.session_state.project
        if curr_proj:
            col_info, col_btn = st.columns([3, 2])
            with col_info:
                st.caption(f"Active: **{curr_proj['name']}**")
            with col_btn:
                if st.button("➕ New", key="new_proj_sidebar_top", use_container_width=True, help="Clear workspace and start a clean new project"):
                    st.session_state.project = None
                    st.session_state.sow_facts = None
                    st.session_state.stress_issues = []
                    st.session_state.stress_ids = []
                    st.session_state.decisions = []
                    st.session_state.last_message = ""
                    st.session_state.draft_reply = ""
                    st.session_state.change_order = ""
                    if "project" in st.query_params:
                        del st.query_params["project"]
                    st.rerun()
        else:
            st.caption("_New unsaved project_")

        k_suffix = curr_proj["project_id"] if curr_proj else "new"

        project_name = st.text_input(
            "Project name",
            value=curr_proj.get("name", "my-project") if curr_proj else "my-project",
            key=f"project_name_{k_suffix}",
        )
        sow_text = st.text_area(
            "Paste SOW text here",
            value=curr_proj.get("sow_text", "") if curr_proj else "",
            height=250,
            placeholder="Paste your Statement of Work...",
            key=f"sow_text_{k_suffix}",
        )

        col1, col2 = st.columns(2)
        with col1:
            default_rate = float(curr_proj.get("hourly_rate", 50.0)) if curr_proj else 50.0
            hourly_rate = st.number_input(
                "Hourly rate",
                min_value=1.0,
                value=default_rate,
                step=5.0,
                key=f"hourly_rate_{k_suffix}",
            )
            currencies = ["USD", "EUR", "GBP", "INR", "AUD"]
            curr_default = curr_proj.get("currency", "USD") if curr_proj else "USD"
            curr_idx = currencies.index(curr_default) if curr_default in currencies else 0
            currency = st.selectbox(
                "Currency",
                currencies,
                index=curr_idx,
                key=f"currency_{k_suffix}",
            )
        with col2:
            default_price = float(curr_proj.get("contract_price", 1000.0)) if curr_proj else 1000.0
            contract_price = st.number_input(
                "Contract price",
                min_value=0.0,
                value=default_price,
                step=100.0,
                key=f"contract_price_{k_suffix}",
            )
            niche = st.selectbox(
                "Niche profile",
                ["None", "web_dev", "copywriting"],
                key=f"niche_{k_suffix}",
            )

        niche_val = None if niche == "None" else niche

        # Auto-save modifications to project settings if already created
        if curr_proj:
            changed = False
            if curr_proj.get("name") != project_name:
                curr_proj["name"] = project_name
                changed = True
            if curr_proj.get("hourly_rate") != hourly_rate:
                curr_proj["hourly_rate"] = hourly_rate
                changed = True
            if curr_proj.get("currency") != currency:
                curr_proj["currency"] = currency
                changed = True
            if curr_proj.get("contract_price") != contract_price:
                curr_proj["contract_price"] = contract_price
                changed = True
            if curr_proj.get("sow_text") != sow_text:
                curr_proj["sow_text"] = sow_text
                changed = True
            if changed:
                save_state()

        extract_btn_label = "🔄 Re-extract SOW" if (curr_proj and curr_proj.get("sow")) else "🚀 Extract SOW"
        if st.button(extract_btn_label, type="primary", use_container_width=True):
            if not sow_text.strip():
                st.error("Please paste your SOW text first.")
            else:
                with st.spinner("Extracting SOW facts…"):
                    try:
                        if not curr_proj:
                            target_proj = project_state.new_project(
                                name=project_name,
                                currency=currency,
                                hourly_rate=hourly_rate,
                                contract_price=contract_price,
                                sow_text=sow_text,
                            )
                        else:
                            target_proj = curr_proj
                            target_proj["name"] = project_name
                            target_proj["currency"] = currency
                            target_proj["hourly_rate"] = hourly_rate
                            target_proj["contract_price"] = contract_price
                            target_proj["sow_text"] = sow_text

                        facts, warnings = extract_sow(sow_text)
                        project_state.set_sow(target_proj, facts)
                        project_state.save_project(target_proj)
                        load_project_into_session(target_proj)
                        st.success("SOW extracted ✓")
                        if warnings:
                            for w in warnings:
                                st.warning(w)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")

        # Show extracted facts
        if st.session_state.sow_facts:
            facts: SOWFacts = st.session_state.sow_facts
            st.divider()
            st.subheader("Extracted facts")
            st.json({
                "pages":           facts.pages,
                "revision_rounds": facts.revision_rounds,
                "deliverables":    facts.deliverables,
                "excluded":        facts.excluded,
                "deadline":        facts.deadline,
                "payment_terms":   facts.payment_terms,
            })

        # Switch to All Projects shortcut
        st.divider()
        if st.button("📁 Switch / Manage Projects", use_container_width=True):
            st.query_params["view"] = "projects"
            st.rerun()

        # Delete current project
        if curr_proj:
            with st.expander("🗑️ Delete this project", expanded=False):
                st.caption(f"Permanently delete **{curr_proj['name']}** from disk.")
                if st.button("Confirm Delete", type="secondary", key=f"del_sidebar_{k_suffix}", use_container_width=True):
                    project_state.delete_project(curr_proj["project_id"])
                    st.session_state.project = None
                    st.session_state.sow_facts = None
                    st.session_state.stress_issues = []
                    st.session_state.stress_ids = []
                    st.session_state.decisions = []
                    st.session_state.last_message = ""
                    st.session_state.draft_reply = ""
                    st.session_state.change_order = ""
                    if "project" in st.query_params:
                        del st.query_params["project"]
                    st.success("Project deleted.")
                    st.rerun()

        st.divider()
        st.caption(
            "⚠️ **Not legal advice.** Hour and cost figures are illustrative estimates. "
            "Always review before sending."
        )

# If All Projects menu is selected, render project management view and stop
if is_projects_view:
    render_all_projects_view()
    st.stop()

# ── Top bar: summary ──────────────────────────────────────────────────────────
proj = get_project()
if proj:
    s = pricing_summary(proj.get("log", []), hourly_rate, contract_price)
    quota = proj.get("quota", {})
    sow_f = st.session_state.sow_facts

    rev_used = quota.get("revisions_used", 0)
    rev_total = sow_f.revision_rounds if sow_f and sow_f.revision_rounds else "∞"

    bar_cols = st.columns(5)
    bar_cols[0].metric("Extra requests", s["extras"])
    bar_cols[1].metric("Est. extra hours", f"{s['hours']}h")
    bar_cols[2].metric("Est. extra value", f"{currency} {s['value']:.0f}")
    bar_cols[3].metric(
        "% over contract",
        f"{s['pct_over_scope']}%" if s["pct_over_scope"] is not None else "N/A"
    )
    bar_cols[4].metric("Revisions used", f"{rev_used}/{rev_total}")
    st.caption("_Extra work flagged (illustrative estimate)_")
    st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍 Stress Test", "📋 Check Request", "📊 Log"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Stress Test
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("SOW Stress Test")
    st.markdown(
        "Finds vague wording, missing clauses, and risky terms in your SOW "
        "**before** you sign the contract."
    )

    if not st.session_state.sow_facts:
        st.info("Extract the SOW first using the sidebar ↖")
    else:
        if st.button("🔍 Run Stress Test", type="primary"):
            with st.spinner("Analysing SOW for risks…"):
                try:
                    issues, ids = run_stress_test(
                        sow_text=proj["sow_text"],
                        facts=st.session_state.sow_facts,
                    )
                    st.session_state.stress_issues = issues
                    st.session_state.stress_ids    = ids
                    project_state.set_stress(proj, issues, ids)
                    save_state()
                except Exception as e:
                    st.error(f"Stress test failed: {e}")

        if st.session_state.stress_issues:
            issues: list[StressIssue] = st.session_state.stress_issues
            ids = st.session_state.stress_ids

            missing_items = [(ids[i], issue) for i, issue in enumerate(issues) if issue.kind == "missing"]
            vague_items = [(ids[i], issue) for i, issue in enumerate(issues) if issue.kind != "missing"]

            total_count = len(issues)
            if total_count == 0:
                st.success("✅ No significant issues found. Your SOW looks tight!")
            else:
                st.warning(
                    f"Found **{total_count} issue(s)** to review: "
                    f"**{len(missing_items)} missing standard clause(s)** and "
                    f"**{len(vague_items)} vague phrasing issue(s)**."
                )

            # ── Section 1: Missing Standard Clauses ──
            st.markdown("### ⚠️ Missing Standard Clauses")
            st.caption(
                "Standard protections absent from the SOW (e.g. revision limits, "
                "fixed deadlines, payment terms, or client responsibilities)."
            )
            if not missing_items:
                st.success("✅ All standard clauses (revisions, deadline, payment terms, deliverables, exclusions) are present.")
            else:
                for card_id, issue in missing_items:
                    sev_icon = SEVERITY_COLORS.get(issue.severity, "⚪")
                    with st.expander(
                        f"{sev_icon} **{card_id}** — Missing Clause: {issue.why_risky}",
                        expanded=True,
                    ):
                        st.markdown(f"**Issue:** {issue.why_risky}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**You assume:** _{issue.freelancer_reading}_")
                        with col_b:
                            st.markdown(f"**Client assumes:** _{issue.client_reading}_")

                        st.markdown("**Suggested clause to add:**")
                        st.code(issue.suggested_rewrite, language=None)
                        st.button(
                            "📋 Copy clause",
                            key=f"copy_rewrite_{card_id}",
                            help="Copy this suggested clause to clipboard",
                        )

            st.markdown("---")

            # ── Section 2: Vague & Ambiguous Phrasing ──
            st.markdown("### 🔍 Vague & Ambiguous Phrasing in SOW")
            st.caption("Wording inside the SOW text that is open to multiple interpretations.")
            if not vague_items:
                st.success("✅ No ambiguous phrases detected in the text.")
            else:
                for idx, (card_id, issue) in enumerate(vague_items):
                    sev_icon = SEVERITY_COLORS.get(issue.severity, "⚪")
                    kind_label = "Undefined term" if issue.kind == "undefined_term" else "Vague wording"
                    quote_preview = (
                        issue.quote[:50] + "…"
                        if issue.quote and len(issue.quote) > 50
                        else (issue.quote or "N/A")
                    )
                    with st.expander(
                        f"{sev_icon} **{card_id}** — {kind_label}: \"{quote_preview}\"",
                        expanded=(idx == 0),
                    ):
                        if issue.quote:
                            st.markdown(f"**Exact Quote:** `{issue.quote}` ✅ _verified in text_")
                        st.markdown(f"**Why risky:** {issue.why_risky}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**You read it as:** _{issue.freelancer_reading}_")
                        with col_b:
                            st.markdown(f"**Client reads it as:** _{issue.client_reading}_")

                        st.markdown("**Suggested rewrite:**")
                        st.code(issue.suggested_rewrite, language=None)
                        st.button(
                            "📋 Copy rewrite",
                            key=f"copy_rewrite_{card_id}",
                            help="Copy this rewrite to clipboard",
                        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Check Request
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Check Client Request")
    st.markdown("Paste a client message to check which requests are in or out of scope.")

    if not st.session_state.sow_facts:
        st.info("Extract the SOW first using the sidebar ↖")
    else:
        client_msg = st.text_area(
            "Client message",
            placeholder="e.g. 'Can you add a blog page? Also, can you update the footer?'",
            height=120,
            key="client_msg_input",
        )

        if st.button("🔎 Check Request", type="primary"):
            if not client_msg.strip():
                st.error("Please enter a client message.")
            else:
                with st.spinner("Splitting and checking requests…"):
                    try:
                        split = split_requests(client_msg)
                        decisions = []
                        for req in split.requests:
                            match = match_request(
                                req,
                                proj["sow_text"],
                                st.session_state.sow_facts,
                                niche=niche_val,
                            )
                            decision = decide(
                                request=req, match=match,
                                sow=st.session_state.sow_facts,
                                quota=proj.get("quota", {"revisions_used": 0}),
                                issues=st.session_state.stress_issues,
                                issue_ids=st.session_state.stress_ids,
                                sow_text=proj["sow_text"],
                                client_message=client_msg,
                            )
                            hrs = estimate_hours(req.type, match.size)
                            prc = price(hrs, hourly_rate)
                            decision.hours = hrs
                            decision.price = prc
                            decisions.append(decision)

                        st.session_state.decisions    = decisions
                        st.session_state.last_message = client_msg
                        st.session_state.draft_reply  = ""
                        st.session_state.change_order = ""
                        st.session_state.draft_version = st.session_state.get("draft_version", 0) + 1
                    except Exception as e:
                        st.error(f"Check failed: {e}")

        # Show decisions
        # Show decisions
        if st.session_state.decisions:
            st.divider()
            st.subheader("Results")

            VERDICT_INFO = {
                "in_scope": {
                    "title": "🟢 INCLUDED IN CONTRACT",
                    "description": "Covered by your agreed scope. This request is included in your contract without additional billing.",
                },
                "out_of_scope": {
                    "title": "🔴 EXTRA WORK (BILLABLE)",
                    "description": "Not covered by your agreement. This request falls outside the contract and requires additional billing.",
                },
                "gray_area": {
                    "title": "🟡 UNCLEAR / NEEDS CLARIFICATION",
                    "description": "Your contract does not explicitly define this request (or revision terms are open-ended). We recommend clarifying with the client before proceeding.",
                },
                "unverified": {
                    "title": "⚠️ UNVERIFIED REQUEST",
                    "description": "The cited text could not be verified against the contract or client message. Please review manually.",
                },
            }

            CONFIDENCE_INFO = {
                "high": ("🟢 High Confidence", "Direct, unambiguous matching found in contract terms."),
                "medium": ("🟡 Medium Confidence", "Reasonable match based on overall contract context."),
                "low": ("🟠 Low Confidence", "Contract language is broad or silent on this topic."),
            }

            for i, d in enumerate(st.session_state.decisions):
                v_info = VERDICT_INFO.get(
                    d.final_verdict,
                    {
                        "title": f"⚪ {d.final_verdict.replace('_', ' ').upper()}",
                        "description": "Review request against contract terms.",
                    },
                )

                with st.expander(
                    f"{v_info['title']} — \"{d.request_text[:65]}\"",
                    expanded=True,
                ):
                    if d.final_verdict == "in_scope":
                        st.success(f"**Included:** {v_info['description']}")
                    elif d.final_verdict == "out_of_scope":
                        st.error(f"**Extra Work:** {v_info['description']}")
                    elif d.final_verdict == "gray_area":
                        st.warning(f"**Clarification Needed:** {v_info['description']}")
                    else:
                        st.info(f"**Manual Review:** {v_info['description']}")

                    if d.final_verdict == "out_of_scope":
                        st.markdown(
                            f"💰 **Estimated Billing:** **{d.hours} hrs** / "
                            f"**{currency} {d.price:.2f}** *(at {currency} {hourly_rate:.2f}/hr)*"
                        )

                    conf_label, conf_desc = CONFIDENCE_INFO.get(
                        d.confidence, (d.confidence.title(), "")
                    )
                    st.caption(f"🤖 **AI Analysis Confidence:** **{conf_label}** — _{conf_desc}_")

                    col_msg, col_sow = st.columns(2)
                    with col_msg:
                        st.markdown("**🗣️ Client message:**")
                        st.info(f"\"{d.client_quote}\"")
                    with col_sow:
                        st.markdown("**📜 Relevant contract clause:**")
                        if d.sow_quote:
                            st.info(f"\"{d.sow_quote}\"")
                        else:
                            st.caption("_No specific clause found in contract_")

                    if d.linked_ambiguity:
                        st.caption(
                            f"🔗 **Linked Risk:** Connects to issue **{d.linked_ambiguity}** "
                            "identified during your SOW Stress Test."
                        )

                    # Action buttons
                    btn_cols = st.columns([1, 1, 2])
                    with btn_cols[0]:
                        if st.button("📝 Save to log", key=f"add_log_{i}"):
                            project_state.add_log_entry(
                                proj, d, st.session_state.last_message
                            )
                            save_state()
                            st.success("Saved to log ✓")
                    with btn_cols[1]:
                        if d.consumes_revision and d.final_verdict == "in_scope":
                            if st.button("📊 Count as revision", key=f"count_rev_{i}"):
                                project_state.increment_revision(proj)
                                save_state()
                                st.success(
                                    f"Revision counted. Total used: "
                                    f"{proj['quota']['revisions_used']}"
                                )

            # Draft reply
            st.divider()
            st.subheader("Draft Reply")
            tone = st.selectbox("Tone", ["friendly", "formal"], key="tone_select")

            if st.button("✍️ Draft Reply", type="primary"):
                with st.spinner("Drafting reply…"):
                    try:
                        reply, co = draft_reply(
                            decisions=st.session_state.decisions,
                            rate=hourly_rate,
                            tone=tone,
                            freelancer_name=None,
                        )
                        st.session_state.draft_reply  = reply
                        st.session_state.change_order = co
                        st.session_state.draft_version = st.session_state.get("draft_version", 0) + 1
                    except Exception as e:
                        st.error(f"Drafting failed: {e}")

            if st.session_state.draft_reply:
                draft_ver = st.session_state.get("draft_version", 0)
                st.text_area(
                    "Reply",
                    value=st.session_state.draft_reply,
                    height=200,
                    key=f"reply_area_{draft_ver}",
                )
                if st.session_state.change_order:
                    st.markdown("---")
                    st.subheader("Change Order")
                    st.markdown(st.session_state.change_order)
                    st.download_button(
                        "⬇️ Download change order",
                        data=st.session_state.change_order,
                        file_name="change_order.md",
                        mime="text/markdown",
                    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Log
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Project Log")

    if not proj:
        st.info("Start a project using the sidebar ↖")
    else:
        log = proj.get("log", [])
        if not log:
            st.info("No items logged yet. Check a request and click 'Add to log'.")
        else:
            for i, entry in enumerate(log):
                icon = VERDICT_COLORS.get(entry["verdict"], "⚪")
                cols = st.columns([3, 1, 1, 1, 1, 2])
                cols[0].markdown(f"{icon} {entry['request'][:60]}")
                cols[1].markdown(f"`{entry['verdict']}`")
                cols[2].markdown(f"{entry['hours']}h")
                cols[3].markdown(f"{currency} {entry['price']:.2f}")
                cols[4].markdown(entry["date"])

                new_status = cols[5].selectbox(
                    "Status",
                    ["pending", "approved", "declined"],
                    index=["pending", "approved", "declined"].index(entry.get("status", "pending")),
                    key=f"status_{i}",
                )
                if new_status != entry.get("status"):
                    project_state.update_log_status(proj, i, new_status)
                    save_state()

            st.divider()
            md_export = project_state.export_log_markdown(proj)
            st.download_button(
                "⬇️ Export log as Markdown",
                data=md_export,
                file_name=f"{proj.get('name', 'project')}_log.md",
                mime="text/markdown",
            )

    st.divider()
    st.caption(
        "**Disclaimer:** Scope-Creep Catcher is a text-analysis aid. It flags vague wording "
        "and compares client requests to a document. It does not give legal advice. "
        "Hour and cost figures are illustrative estimates. Consult a qualified professional "
        "for legal questions. Nothing is uploaded — all data stays on your machine."
    )
