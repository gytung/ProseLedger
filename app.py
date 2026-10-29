"""Local research-writing workspace and read-only evaluation browser."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pandas as pd
import streamlit as st

from ui.jobs import (
    ROOT,
    is_running,
    latest_job,
    new_job,
    pdf_sources,
    read_json,
    resume_job,
    run_progress,
)
from ui.rendering import BRANCHES, heading, live_summary, proposal_pdf, source_table

DATA = ROOT / "data"

st.set_page_config(page_title="ProseLedger", page_icon="✦", layout="wide")
st.markdown(
    """
<style>
.stApp { background:#ffffff; color:#393447; }
[data-testid="stSidebar"] { background:#F6F3FA; }
.block-container { max-width:1250px; padding-top:2rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:Georgia,"Times New Roman",serif !important; color:#554167; }
.eyebrow { color:#8B719F; font-size:.8rem; font-weight:700; letter-spacing:.12em; }
.intro { color:#6D6577; max-width:900px; line-height:1.6; }
div[data-testid="stMetric"] { background:#FAF8FD; border-radius:15px; padding:1rem; }
.stButton>button[kind="primary"] { background:#806298; border-color:#806298; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=15, show_spinner=False)
def provider_status() -> str:
    """Probe the official CLI without reading or rendering any credential files."""
    from proseledger.codex_client import CodexCLIModel

    try:
        binary = CodexCLIModel._find_executable(None)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        status = subprocess.run(
            [binary, "login", "status"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=flags,
        )
        text = (status.stdout + status.stderr).lower()
        return (
            "authenticated" if status.returncode == 0 and "logged in" in text else "sign_in_needed"
        )
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        return "unavailable"


def authentication_panel() -> str:
    status = provider_status()
    if status == "authenticated":
        st.success("The Codex CLI is signed in. Fresh generation is available.")
    elif status == "sign_in_needed":
        st.warning(
            "Run `codex login` in a terminal, complete sign-in, then check the connection below."
        )
    else:
        st.info(
            "Install the official Codex CLI and complete `codex login`. If the native executable is not on PATH, set PROSELEDGER_CODEX_PATH before starting this app. See README.md."
        )
    if st.button("Check model connection"):
        provider_status.clear()
        st.rerun()
    return status


@st.fragment(run_every="2s")
def job_panel():
    output = latest_job("live")
    if output is None:
        return
    job = read_json(output / "job.json", {})
    artifacts = output / "output"
    state = read_json(artifacts / "status.json", {})
    summary = read_json(artifacts / "summary.json", {})
    progress = run_progress(output, job)
    status = job.get("status", "starting")
    columns = st.columns(3)
    columns[0].metric("Completed model calls", progress["completed_calls"])
    columns[1].metric("Elapsed since first start", progress["elapsed_label"])
    columns[2].metric("Attempt", progress["attempt"])
    st.caption(
        "Counts include completed calls across resumptions. Reused responses are not counted again."
    )
    if status in ("starting", "running"):
        stage = state.get("stage", "preparing").replace("_", " ")
        st.info(f"Generating a new proposal — {stage}.")
    elif status == "failed":
        st.error("The run stopped before completion. Completed calls remain available for resume.")
        if state.get("message"):
            st.caption(str(state["message"])[:450])
        if st.button("Resume this run", type="primary"):
            try:
                resume_job(output)
                st.rerun()
            except (OSError, ValueError) as error:
                st.error(str(error))
    elif status == "completed" and summary.get("status") == "completed":
        st.success("Generation completed. The following values belong to this run.")
        st.metric("Initial draft problem score", summary["initial_score"])
        live_summary(summary, artifacts)
        rows = []
        for method, branch in summary.get("branches", {}).items():
            for record in branch["rounds"]:
                rows.append(
                    {
                        "Method": BRANCHES[method],
                        "Round": record["round"],
                        "Candidate": record["candidate_score"],
                        "Retained": record["retained_score"],
                        "Accepted": record["accepted"],
                        "Route": record["route"],
                        "Historical card used": record["memory_used"],
                    }
                )
        with st.expander("Inspect all revision decisions"):
            st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button(
            "Download run summary",
            json.dumps(summary, indent=2),
            file_name="run_summary.json",
            mime="application/json",
        )
    else:
        st.warning(
            "A complete result summary is not available. Inspect this run before reporting any scores."
        )
    st.caption(
        f"Run: {output.name}. Keep its output directory to resume or inspect the full audit trail."
    )


def render_create():
    heading(
        "NEW GENERATION",
        "Create a research proposal",
        "Supply literature and a topic. Compare targeted rewriting, planning, and conditional experience reuse from one initial draft.",
    )
    st.caption(
        "This makes real hosted-model calls through the signed-in Codex CLI. Model: gpt-6.1-sol. No local training or GPU is required. Account access and usage allowance are required."
    )
    provider = authentication_panel()
    default_topic = (DATA / "topic.txt").read_text(encoding="utf-8").strip()
    topic = st.text_area("Research topic", default_topic, height=100)
    mode = st.radio(
        "Evidence input", ["Included source excerpts", "Upload 2–10 PDFs"], horizontal=True
    )
    files = []
    if mode.startswith("Upload"):
        files = st.file_uploader(
            "Text-readable English PDFs", type=["pdf"], accept_multiple_files=True
        )
        st.caption(
            "Up to 20,000 extracted characters per PDF. Scanned documents require OCR first."
        )
    else:
        with st.expander("View the included sources"):
            source_table(read_json(DATA / "sources.json", []))
    consent = st.checkbox(
        "Start fresh model calls; I understand the text and scores can differ from archived results."
    )
    if st.button(
        "Generate a proposal",
        type="primary",
        disabled=not consent or provider != "authenticated" or is_running("live"),
    ):
        try:
            if len(topic.strip()) < 12:
                raise ValueError("Please enter a research topic of at least 12 characters.")
            if mode.startswith("Upload") and not 2 <= len(files) <= 10:
                raise ValueError("Please upload between two and ten PDFs.")
            sources = (
                pdf_sources(files)
                if mode.startswith("Upload")
                else read_json(DATA / "sources.json", [])
            )
            new_job(topic.strip(), sources)
            st.rerun()
        except (ValueError, OSError) as error:
            st.error(str(error))
    st.divider()
    job_panel()
    st.caption(
        "Keep the computer awake. Closing the browser does not stop the background job. Generated traces remain local under runs/ and are excluded from Git."
    )


def render_evaluation():
    heading(
        "ARCHIVED EVALUATION",
        "Six proposals. All outcomes.",
        "These are preserved model-generated drafts and recorded scores, not a new model run. This page does not make model calls.",
    )
    evidence = read_json(ROOT / "docs" / "evidence.json", {})
    cases = evidence.get("cases", [])
    if not cases:
        st.warning(
            "The evaluation bundle is missing. Restore docs/evidence.json from the source archive."
        )
        return
    rows = []
    for case in cases:
        row = {"Case": case["number"], "Topic": case["theme"], "Initial": case["initial"]["score"]}
        row.update({label: case["branches"][method]["score"] for method, label in BRANCHES.items()})
        t, m = row["Targeted"], row["Memory"]
        row["Memory vs Targeted"] = "Win" if m < t else "Loss" if m > t else "Tie"
        rows.append(row)
    st.dataframe(rows, hide_index=True, width="stretch")
    frame = pd.DataFrame(rows)
    means = frame[["Initial", *BRANCHES.values()]].mean()
    columns = st.columns(4)
    for column, (name, value) in zip(columns, means.items()):
        column.metric(f"Mean {name}", f"{value:.4f}")
    outcomes = frame["Memory vs Targeted"].value_counts()
    st.write(
        f"**Memory vs Targeted: {outcomes.get('Win', 0)} wins / {outcomes.get('Tie', 0)} ties / {outcomes.get('Loss', 0)} losses.**"
    )
    st.caption(
        "Lower is better: 30% rule score + 70% model rubric. This is not authorship accuracy. Planning adds calls; total token budgets are not identical. This batch does not establish a Memory advantage."
    )
    selection = st.selectbox(
        "Inspect a proposal",
        range(len(cases)),
        format_func=lambda i: f"{cases[i]['number']:02d} · {cases[i]['theme']}",
    )
    case = cases[selection]
    tabs = st.tabs(["Retained manuscripts", "Revision decisions", "Supplied sources"])
    with tabs[0]:
        branch = st.selectbox(
            "Manuscript", ["Initial", *BRANCHES], format_func=lambda key: BRANCHES.get(key, key)
        )
        record = case["initial"] if branch == "Initial" else case["branches"][branch]
        document = record["text"]
        st.download_button(
            "Download manuscript",
            document,
            file_name=f"case_{case['number']:02d}_{branch.lower()}.md",
        )
        with st.container(height=600, border=True):
            st.markdown(document)
    with tabs[1]:
        decisions = []
        for method, label in BRANCHES.items():
            for record in case["branches"][method]["rounds"]:
                decisions.append(
                    {
                        "Method": label,
                        "Round": record["round"],
                        "Candidate": record["candidate_score"],
                        "Retained": record["retained_score"],
                        "Accepted": record["accepted"],
                        "Check passed": record["guard_passed"],
                        "Route": record["route"],
                        "Cards": ", ".join(record["historical_card_ids"]),
                    }
                )
        st.dataframe(decisions, hide_index=True, width="stretch")
        st.caption(
            "Card retrieval, execution, acceptance and benefit are distinct events. A non-increasing retained-score curve follows the selection rule."
        )
    with tabs[2]:
        source_table(case["sources"])
    st.info(
        "For the full offline demonstration, open docs/index.html. That viewer and this page use the same archived evidence. They do not reconstruct raw model responses."
    )


def render_memory():
    heading(
        "FROZEN EXPERIENCE",
        "Inspect the editing catalogue",
        "Development-time operation cards record examples, applicability conditions and preservation requirements. The catalogue stays fixed during a comparison.",
    )
    catalog = read_json(DATA / "catalogs.json", {})["memory"]
    st.write(
        f"**{len(catalog['cards'])} active cards.** Planner-only receives no historical cards. Both planning branches retain their own earlier outcomes within the current run."
    )
    for card in catalog["cards"]:
        with st.expander(card["id"].replace("_", " ").title()):
            st.write(card["operation"])
            st.markdown("**Applicability conditions**")
            st.dataframe(card.get("conditions", []), hide_index=True, width="stretch")
            st.markdown("**Preservation requirements**")
            for item in card.get("preserve", []):
                st.write("• " + item)
            st.caption(
                "Examples are historical observations, not a guarantee that the operation helps a new proposal."
            )
            for index, example in enumerate(card.get("examples", []), 1):
                payload = example.get("payload", {})
                st.markdown(f"**Example {index}**")
                columns = st.columns(2)
                columns[0].write(payload.get("before", ""))
                columns[1].write(payload.get("after", ""))
    st.caption(
        "Current-run records do not automatically become new cards. Model weights are unchanged."
    )


with st.sidebar:
    st.markdown("## ProseLedger")
    st.caption("RESEARCH WRITING · REVISION MEMORY")
    page = st.radio("Workspace", ["Create proposal", "Saved evaluation", "Memory catalogue"])
    st.divider()
    st.caption(
        "New runs and archived results are kept separate. See THIRD_PARTY_NOTICES.md for upstream attribution and licensing."
    )

if page == "Create proposal":
    render_create()
elif page == "Saved evaluation":
    render_evaluation()
else:
    render_memory()
