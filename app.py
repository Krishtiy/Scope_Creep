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
from engine.drafter import draft_reply
from engine import state as project_state
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


# ── Sidebar setup ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Project Setup")

    project_name = st.text_input("Project name", value="my-project", key="project_name_input")
    sow_text     = st.text_area(
        "Paste SOW text here",
        height=250,
        placeholder="Paste your Statement of Work...",
        key="sow_text_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        hourly_rate     = st.number_input("Hourly rate", min_value=1.0, value=50.0, step=5.0)
        currency        = st.selectbox("Currency", ["USD", "EUR", "GBP", "INR", "AUD"])
    with col2:
        contract_price  = st.number_input("Contract price", min_value=0.0, value=1000.0, step=100.0)
        niche           = st.selectbox("Niche profile", ["None", "web_dev", "copywriting"])

    niche_val = None if niche == "None" else niche

    if st.button("🚀 Extract SOW", type="primary", use_container_width=True):
        if not sow_text.strip():
            st.error("Please paste your SOW text first.")
        else:
            with st.spinner("Extracting SOW facts…"):
                try:
                    proj = project_state.new_project(
                        name=project_name,
                        currency=currency,
                        hourly_rate=hourly_rate,
                        contract_price=contract_price,
                        sow_text=sow_text,
                    )
                    facts, warnings = extract_sow(sow_text)
                    project_state.set_sow(proj, facts)
                    st.session_state.project   = proj
                    st.session_state.sow_facts = facts
                    save_state()
                    st.success("SOW extracted ✓")
                    if warnings:
                        for w in warnings:
                            st.warning(w)
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

    st.divider()
    st.caption(
        "⚠️ **Not legal advice.** Hour and cost figures are illustrative estimates. "
        "Always review before sending."
    )

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

            if len(issues) == 0:
                st.success("✅ No significant issues found. Your SOW looks tight!")
            else:
                st.warning(f"Found {len(issues)} issue(s) to review:")

            for i, issue in enumerate(issues):
                sev_icon = SEVERITY_COLORS.get(issue.severity, "⚪")
                kind_label = {"vague": "Vague", "undefined_term": "Undefined term",
                              "missing": "Missing clause"}.get(issue.kind, issue.kind)

                with st.expander(
                    f"{sev_icon} **{ids[i]}** — {kind_label} "
                    f"({'Missing' if issue.kind == 'missing' else issue.quote[:50] + '…' if issue.quote and len(issue.quote) > 50 else issue.quote or 'N/A'})",
                    expanded=(i == 0),
                ):
                    if issue.kind != "missing" and issue.quote:
                        st.markdown(f"**Quote:** `{issue.quote}` ✅ _verified_")
                    elif issue.kind == "missing":
                        st.markdown(f"**Missing clause** (no quote — this is about something absent)")

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
                        key=f"copy_rewrite_{i}",
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
                    except Exception as e:
                        st.error(f"Check failed: {e}")

        # Show decisions
        if st.session_state.decisions:
            st.divider()
            st.subheader("Results")

            for i, d in enumerate(st.session_state.decisions):
                icon = VERDICT_COLORS.get(d.final_verdict, "⚪")
                with st.expander(
                    f"{icon} {d.request_text[:70]} — **{d.final_verdict.replace('_', ' ').upper()}**",
                    expanded=True,
                ):
                    cols = st.columns([2, 1, 1])
                    with cols[0]:
                        st.markdown(f"**Verdict:** {icon} `{d.final_verdict}`")
                        if d.overridden_by_rule:
                            st.caption(
                                f"⚡ Rule(s) `{', '.join(d.rule_ids)}` overrode LLM "
                                f"verdict (`{d.llm_verdict}`)"
                            )
                        else:
                            st.caption(f"Rules applied: `{', '.join(d.rule_ids) or 'none'}`")
                    with cols[1]:
                        st.metric("Conf.", d.confidence)
                    with cols[2]:
                        if d.final_verdict == "out_of_scope":
                            st.metric("Est. hours", f"{d.hours}h")
                            st.metric("Est. cost", f"{currency} {d.price:.2f}")

                    if d.sow_quote:
                        q_method = d.quote_methods.get("sow", "")
                        badge = "✅ exact" if q_method == "exact" else "🔶 fuzzy" if q_method == "fuzzy" else "⚠️ unverified"
                        st.markdown(f"**SOW clause:** `{d.sow_quote}` {badge}")
                    else:
                        st.caption("_No SOW clause cited_")

                    cq_method = d.quote_methods.get("client", "")
                    cbadge = "✅ verified" if cq_method in ("exact", "fuzzy") else "⚠️ unverified"
                    st.markdown(f"**Client quote:** `{d.client_quote}` {cbadge}")

                    if d.final_verdict == "unverified":
                        st.error("⚠️ Cannot draft a change order for this item — quote could not be verified. Please review manually.")

                    if d.linked_ambiguity:
                        st.caption(f"🔗 Linked to stress-test issue {d.linked_ambiguity}")

                    # Action buttons
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if st.button(f"📝 Add to log", key=f"add_log_{i}"):
                            entry = project_state.add_log_entry(
                                proj, d, st.session_state.last_message
                            )
                            if d.consumes_revision and d.final_verdict == "in_scope":
                                st.info(
                                    "This is a revision. Click 'Count as revision' to use a revision round."
                                )
                            save_state()
                            st.success("Added to log ✓")
                    with btn_cols[1]:
                        if d.consumes_revision and d.final_verdict == "in_scope":
                            if st.button(f"📊 Count as revision", key=f"count_rev_{i}"):
                                project_state.increment_revision(proj)
                                save_state()
                                st.success(
                                    f"Revision counted. Used: "
                                    f"{proj['quota']['revisions_used']}"
                                )

            # Draft reply
            st.divider()
            st.subheader("Draft Reply")
            tone = st.selectbox("Tone", ["friendly", "firm", "formal"], key="tone_select")
            freelancer_name = st.text_input("Your name (optional)", key="freelancer_name")

            if st.button("✍️ Draft Reply", type="primary"):
                with st.spinner("Drafting reply…"):
                    try:
                        reply, co = draft_reply(
                            decisions=st.session_state.decisions,
                            rate=hourly_rate,
                            tone=tone,
                            freelancer_name=freelancer_name or None,
                        )
                        st.session_state.draft_reply  = reply
                        st.session_state.change_order = co
                    except Exception as e:
                        st.error(f"Drafting failed: {e}")

            if st.session_state.draft_reply:
                st.text_area("Reply", value=st.session_state.draft_reply, height=200, key="reply_area")
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
