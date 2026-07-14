"""SAP EPM Design Agent — Streamlit UI entry point.

UI only: widgets, layout, session state reads/writes, and calls to core/.
No business logic, no Anthropic SDK imports, no python-docx imports.
"""

import html
import logging
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core import fsd_generator as fsd_gen
from core import interactive_generator as interactive_gen
from core import tsd_generator as tsd_gen
from core.brd_parser import BRDParseError, build_combined_input, parse_brd, parse_supporting_docs
from core.brd_summariser import BRDSummariserError, generate_structured_summary
from core.document_builder import parse_batch_sections
from core.llm_client import LLMError, get_last_usage
from core.question_engine import generate_questions
from core.section_regenerator import regenerate_section
from skills import load_domain_skills, load_sap_skill
from utils.file_handler import (
    FileValidationError,
    validate_and_read_brd,
    validate_and_read_supporting_docs,
    validate_discussion_notes,
    validate_template,
)
from utils.session_state import (
    DEFAULT_METADATA,
    KEY_ANSWERS,
    KEY_BRD_DICT,
    KEY_DETECTED_DOMAINS,
    KEY_DISCUSSION_NOTES,
    KEY_FSD_BATCH_STATUS,
    KEY_FSD_BYTES,
    KEY_FSD_CORRECTION_HISTORY,
    KEY_FSD_CURRENT_DRAFT,
    KEY_FSD_CURRENT_SECTION_INDEX,
    KEY_FSD_DRAFT_FEEDBACK,
    KEY_FSD_DRAFT_PREV,
    KEY_FSD_FULL_TEXT,
    KEY_FSD_GENERATED_AT,
    KEY_FSD_LOCKED_SECTIONS,
    KEY_FSD_PENDING_ANSWERS,
    KEY_FSD_PENDING_QUESTIONS,
    KEY_FSD_REVISION_COUNT,
    KEY_FSD_SECTION_CONTENT,
    KEY_FSD_SECTION_STRUCTURE,
    KEY_FSD_TEMPLATE,
    KEY_METADATA,
    KEY_QUESTIONS,
    KEY_RECOMMENDED_TECHNOLOGIES,
    KEY_SESSION_INPUT_TOKENS,
    KEY_SESSION_OUTPUT_TOKENS,
    KEY_STEP_INPUT_TOKENS,
    KEY_STEP_OUTPUT_TOKENS,
    KEY_STRUCTURED_SUMMARY,
    KEY_SUPPORTING_DOCS,
    KEY_TECHNOLOGY,
    KEY_TECHNOLOGIES,
    KEY_TECHNOLOGY_AUTO,
    KEY_TSD_BATCH_STATUS,
    KEY_TSD_BYTES,
    KEY_TSD_CORRECTION_HISTORY,
    KEY_TSD_CURRENT_DRAFT,
    KEY_TSD_CURRENT_SECTION_INDEX,
    KEY_TSD_DRAFT_FEEDBACK,
    KEY_TSD_DRAFT_PREV,
    KEY_TSD_GENERATED_AT,
    KEY_TSD_LOCKED_SECTIONS,
    KEY_TSD_PENDING_ANSWERS,
    KEY_TSD_PENDING_QUESTIONS,
    KEY_TSD_REVISION_COUNT,
    KEY_TSD_SECTION_CONTENT,
    KEY_TSD_SECTION_STRUCTURE,
    KEY_TSD_TEMPLATE,
    KEY_WORKFLOW_STEP,
    SAP_TECHNOLOGIES,
    SAP_TECHNOLOGY_DESCRIPTIONS,
    STEP_ADDITIONAL_INPUT,
    STEP_ANALYSE,
    STEP_FSD_DOWNLOAD,
    STEP_GENERATE_FSD,
    STEP_GENERATE_TSD,
    STEP_QUESTIONS,
    STEP_SELECT_TECHNOLOGY,
    STEP_TSD_DOWNLOAD,
    STEP_TSD_INPUT,
    STEP_UPLOAD,
    active_step_sequence,
    advance_to,
    compute_cost_usd,
    display_step_number,
    get,
    init_session_state,
    record_llm_usage,
    reset_all,
    set_value,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

APP_TITLE = os.getenv("APP_TITLE", "SAP EPM Design Agent")

# CLAUDE.md §3.7: the interactive per-section loop is the default. Setting this to
# false in .env falls back to the legacy batched generation path — the two must
# never run concurrently for the same document.
INTERACTIVE_GENERATION = os.getenv("INTERACTIVE_GENERATION", "true").strip().lower() != "false"


# ---------------------------------------------------------------------------
# CHANGE 6 — Custom dark-navy theme. Edit only this function to restyle.
# ---------------------------------------------------------------------------

def _apply_custom_styles() -> None:
    """Inject the SAP EPM dark-navy/white theme and shared component CSS."""
    st.markdown(
        """
        <style>
        :root {
            --epm-primary: #1F497D;
            --epm-bg: #0F1923;
            --epm-card-bg: #1A2535;
            --epm-success: #2ECC71;
            --epm-active: #3498DB;
            --epm-text: #ECEFF1;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp { background-color: var(--epm-bg); color: var(--epm-text); }
        section[data-testid="stSidebar"] { display: none; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--epm-text); }

        button[kind="primary"], .stDownloadButton button {
            background-color: var(--epm-primary) !important;
            border-color: var(--epm-primary) !important;
        }

        [data-testid="stHeader"] { background-color: var(--epm-bg); }
        [data-testid="stExpander"] {
            background-color: var(--epm-card-bg);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
        }
        [data-testid="stExpander"] summary { background-color: var(--epm-card-bg); color: var(--epm-text); }
        [data-testid="stExpander"] summary p { color: var(--epm-text) !important; }
        [data-testid="stExpanderDetails"] { background-color: var(--epm-card-bg); }
        [data-testid="stFileUploaderDropzone"] {
            background-color: rgba(255,255,255,0.04);
            border: 1px dashed rgba(255,255,255,0.2);
        }
        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small,
        [data-testid="stWidgetLabel"] p {
            color: rgba(236, 239, 241, 0.75) !important;
        }

        /* Step navigator (CHANGE 1) */
        .epm-nav-panel {
            background-color: var(--epm-card-bg);
            border-radius: 10px;
            padding: 1rem 0.9rem;
            position: sticky;
            top: 1rem;
        }
        .epm-nav-phase {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--epm-active);
            margin: 0.9rem 0 0.4rem 0;
        }
        .epm-nav-step {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.35rem 0.4rem;
            border-radius: 6px;
            margin-bottom: 0.15rem;
            font-size: 0.82rem;
            line-height: 1.25;
        }
        .epm-nav-icon { flex-shrink: 0; }
        .epm-nav-label { font-weight: 600; }
        .epm-nav-desc { display: block; font-size: 0.72rem; opacity: 0.75; font-weight: 400; }
        .epm-nav-done { color: var(--epm-success); }
        .epm-nav-current {
            background-color: rgba(52, 152, 219, 0.18);
            color: var(--epm-active);
            border: 1px solid rgba(52, 152, 219, 0.4);
        }
        .epm-nav-pending { color: #6b7785; }

        /* Compact summary / info cards (CHANGE 3) */
        .epm-card {
            background-color: var(--epm-card-bg);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 1.1rem 1.3rem;
            margin: 0.6rem 0 1rem 0;
        }
        .epm-card-title { font-size: 0.95rem; font-weight: 700; margin-bottom: 0.6rem; }
        .epm-card-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.25rem 0;
            font-size: 0.85rem;
            border-bottom: 1px dashed rgba(255,255,255,0.08);
        }
        .epm-card-row:last-child { border-bottom: none; }
        .epm-card-row .epm-label { opacity: 0.7; white-space: nowrap; }
        .epm-card-row .epm-value { font-weight: 600; text-align: right; }

        /* Section generation tiles (CHANGE 4) */
        .epm-tile-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 0.5rem;
            margin: 0.6rem 0 1rem 0;
        }
        .epm-tile { border-radius: 8px; padding: 0.5rem 0.6rem; font-size: 0.72rem; line-height: 1.2; min-height: 3rem; }
        .epm-tile-num { font-weight: 700; display: block; font-size: 0.78rem; }
        .epm-tile-pending { background-color: rgba(255,255,255,0.05); color: #8b96a3; border: 1px solid rgba(255,255,255,0.06); }
        .epm-tile-done { background-color: rgba(46, 204, 113, 0.16); color: var(--epm-success); border: 1px solid rgba(46, 204, 113, 0.5); }
        .epm-tile-active {
            background-color: rgba(52, 152, 219, 0.22);
            color: var(--epm-active);
            border: 1px solid var(--epm-active);
            animation: epm-pulse 1.4s ease-in-out infinite;
        }
        .epm-tile-failed { background-color: rgba(231, 76, 60, 0.16); color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.5); }

        @keyframes epm-pulse {
            0% { box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.5); }
            70% { box-shadow: 0 0 0 8px rgba(52, 152, 219, 0); }
            100% { box-shadow: 0 0 0 0 rgba(52, 152, 219, 0); }
        }

        /* Download card (CHANGE 5) */
        .epm-download-card {
            background: linear-gradient(145deg, var(--epm-card-bg), rgba(31,73,125,0.35));
            border: 1px solid rgba(52, 152, 219, 0.35);
            border-radius: 12px;
            padding: 1.3rem 1.5rem 0.6rem 1.5rem;
            margin: 0.8rem 0 0.4rem 0;
        }
        .epm-download-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.6rem; }
        .epm-download-meta { font-size: 0.85rem; opacity: 0.9; margin: 0.15rem 0; }

        /* Persistent token/cost footer (CHANGE 2) */
        .epm-footer {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            background-color: #0B131C;
            border-top: 1px solid rgba(255,255,255,0.08);
            color: var(--epm-text);
            font-size: 0.78rem;
            padding: 0.55rem 1.2rem;
            z-index: 999;
            text-align: center;
        }
        .epm-footer b { color: var(--epm-active); }
        .block-container { padding-bottom: 4.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# CHANGE 1 — Left-hand step navigator
# ---------------------------------------------------------------------------

def _step_label(step_const: int) -> str:
    """Return "Step N" using the contiguous display number for step_const — never the
    raw STEP_* constant value, which has a gap where STEP_QUESTIONS is skipped in
    interactive mode. Fixes the "Step 4 -> Step 6" numbering bug."""
    return f"Step {display_step_number(step_const, INTERACTIVE_GENERATION)}"


def _build_nav_steps() -> list:
    """Return the left-hand phase/step list, filtered to whichever steps are active for
    the current generation mode via active_step_sequence() — the single source of truth
    also used by _step_label(), so the nav panel and the in-page step headers can never
    drift out of sync on which steps are shown or what number each one gets."""
    gen_desc = (
        "Interactive section-by-section generate / review / lock loop"
        if INTERACTIVE_GENERATION
        else "Batched generation of 14 sections (legacy fast mode)"
    )
    metadata_by_step = {
        STEP_UPLOAD: ("Phase 1 — FSD Generation", "Upload BRD", "Upload the mandatory requirements document"),
        STEP_ADDITIONAL_INPUT: (None, "Supporting Docs & Metadata", "Optional files, notes, and project details"),
        STEP_SELECT_TECHNOLOGY: (None, "Select Technology", "Choose target SAP technology and templates"),
        STEP_ANALYSE: (None, "Analyse Input", "Pre-summarise input, detect domain(s)"),
        STEP_QUESTIONS: (None, "Clarification Questions", "Answer or skip agent questions"),
        STEP_GENERATE_FSD: (None, "Generate FSD", gen_desc),
        STEP_FSD_DOWNLOAD: (None, "FSD Download / Regenerate", "Download FSD or redo a section"),
        STEP_TSD_INPUT: ("Phase 2 — TSD Generation", "TSD Input", "Confirm FSD source and TSD template"),
        STEP_GENERATE_TSD: (None, "Generate TSD", gen_desc),
        STEP_TSD_DOWNLOAD: (None, "TSD Download / Regenerate", "Download TSD or redo a section"),
    }
    return [(step, *metadata_by_step[step]) for step in active_step_sequence(INTERACTIVE_GENERATION)]


def _render_step_navigator(current_step: int) -> None:
    """Render the persistent left-hand workflow step navigator (updates from session state)."""
    parts = ['<div class="epm-nav-panel">']
    for step_num, phase_header, label, desc in _build_nav_steps():
        if phase_header:
            parts.append(f'<div class="epm-nav-phase">{html.escape(phase_header)}</div>')
        if current_step > step_num:
            icon, css_class = "✅", "epm-nav-done"
        elif current_step == step_num:
            icon, css_class = "▶", "epm-nav-current"
        else:
            icon, css_class = "○", "epm-nav-pending"
        display_num = display_step_number(step_num, INTERACTIVE_GENERATION)
        parts.append(
            f'<div class="epm-nav-step {css_class}">'
            f'<span class="epm-nav-icon">{icon}</span>'
            f'<span><span class="epm-nav-label">{display_num}. {html.escape(label)}</span>'
            f'<span class="epm-nav-desc">{html.escape(desc)}</span></span>'
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

    if current_step > STEP_UPLOAD:
        st.write("")
        if st.button("Reset", key="sidebar_reset", use_container_width=True):
            reset_all()
            st.rerun()


def _section_status_label(entry: dict | None, is_current: bool) -> tuple:
    """Return (icon, css_class, status_text) for one section's nav row.

    Rendered ONLY from a locked_sections entry and the active section pointer —
    never inferred from document byte content (CLAUDE.md §3.8a).
    """
    if entry is not None:
        rev = entry.get("revision_count", 0)
        status = f"locked (rev {rev})" if rev else "locked"
        if entry.get("force_locked"):
            status += " ⚠️ manual review"
        return "✅", "epm-nav-done", status
    if is_current:
        return "▶", "epm-nav-current", "current"
    return "○", "epm-nav-pending", "pending"


def _render_section_status_nav(section_structure: list, locked_sections: dict, current_index: int) -> None:
    """Render locked/current/pending status for every FSD or TSD section (FR-10)."""
    parts = ['<div class="epm-nav-panel" style="margin-top:0.75rem;">', '<div class="epm-nav-phase">Sections</div>']
    for i, section in enumerate(section_structure):
        entry = locked_sections.get(section["number"])
        icon, css_class, status = _section_status_label(entry, i == current_index)
        parts.append(
            f'<div class="epm-nav-step {css_class}">'
            f'<span class="epm-nav-icon">{icon}</span>'
            f'<span><span class="epm-nav-label">{html.escape(section["number"])}. {html.escape(section["title"])}</span>'
            f'<span class="epm-nav-desc">{html.escape(status)}</span></span>'
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CHANGE 2 — Token usage tracking + persistent footer
# ---------------------------------------------------------------------------

def _track_usage() -> None:
    """Pull the most recent LLM call's token usage from llm_client and record it in session state."""
    usage = get_last_usage()
    record_llm_usage(usage["input_tokens"], usage["output_tokens"])


def _render_cost_footer() -> None:
    """Render the fixed bottom footer showing per-step and session-total token usage and cost."""
    step_in = get(KEY_STEP_INPUT_TOKENS) or 0
    step_out = get(KEY_STEP_OUTPUT_TOKENS) or 0
    session_in = get(KEY_SESSION_INPUT_TOKENS) or 0
    session_out = get(KEY_SESSION_OUTPUT_TOKENS) or 0
    step_cost = compute_cost_usd(step_in, step_out)
    session_cost = compute_cost_usd(session_in, session_out)
    st.markdown(
        f'<div class="epm-footer">'
        f"Step tokens: <b>{step_in:,}</b> in / <b>{step_out:,}</b> out &nbsp;|&nbsp; "
        f"Step cost: <b>${step_cost:.4f}</b> &nbsp;|&nbsp; "
        f"Session total: <b>{session_in + session_out:,}</b> tokens &nbsp;|&nbsp; "
        f"Session cost: <b>${session_cost:.4f}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# CHANGE 3 — Input summary card
# ---------------------------------------------------------------------------

def _render_input_summary_card() -> None:
    """Render a compact read-only summary of all Phase 1 inputs before analysis begins."""
    brd = get(KEY_BRD_DICT) or {}
    supporting = get(KEY_SUPPORTING_DOCS) or []
    notes = get(KEY_DISCUSSION_NOTES) or ""
    metadata = get(KEY_METADATA) or {}

    if get(KEY_TECHNOLOGY_AUTO) and not get(KEY_TECHNOLOGIES):
        tech_display = "Pending agent recommendation"
    else:
        tech_display = ", ".join(get(KEY_TECHNOLOGIES) or [get(KEY_TECHNOLOGY) or "—"])

    supporting_names = ", ".join(d.get("filename", "?") for d in supporting)
    supporting_display = f"{len(supporting)} — {supporting_names}" if supporting else "None"

    rows = [
        ("BRD", f"{brd.get('filename', '—')} ({brd.get('word_count', 0):,} words)"),
        ("Supporting Documents", supporting_display),
        ("Discussion Notes", f"{len(notes):,} characters" if notes else "None"),
        ("Target Technology", tech_display),
        ("Consultant", metadata.get("consultant") or "—"),
        ("Client", metadata.get("client") or "—"),
        ("Project", metadata.get("project") or "—"),
    ]
    rows_html = "".join(
        f'<div class="epm-card-row"><span class="epm-label">{html.escape(label)}</span>'
        f'<span class="epm-value">{html.escape(str(value))}</span></div>'
        for label, value in rows
    )
    st.markdown(
        f'<div class="epm-card"><div class="epm-card-title">📋 Input Summary — Review Before Analysis</div>{rows_html}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# CHANGE 4 — Section generation progress tiles
# ---------------------------------------------------------------------------

def _tile_state_for_section(section_num: str, batches: list, batch_status: list, active_batch_index) -> str:
    for i, batch in enumerate(batches):
        if section_num in {s["number"] for s in batch}:
            if batch_status[i] == "done":
                return "done"
            if batch_status[i] == "failed":
                return "failed"
            if i == active_batch_index:
                return "active"
            return "pending"
    return "pending"


def _render_section_tiles(section_structure: list, batches: list, batch_status: list, active_batch_index=None) -> None:
    css_by_state = {
        "pending": "epm-tile-pending",
        "done": "epm-tile-done",
        "active": "epm-tile-active",
        "failed": "epm-tile-failed",
    }
    tiles = []
    for s in section_structure:
        state = _tile_state_for_section(s["number"], batches, batch_status, active_batch_index)
        title = s["title"]
        short_title = title if len(title) <= 20 else title[:18] + "…"
        tiles.append(
            f'<div class="epm-tile {css_by_state[state]}">'
            f'<span class="epm-tile-num">{html.escape(s["number"])}</span>{html.escape(short_title)}'
            f"</div>"
        )
    st.markdown(f'<div class="epm-tile-grid">{"".join(tiles)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CHANGE 5 — Document download card
# ---------------------------------------------------------------------------

def _estimate_word_count(section_content: dict) -> int:
    text = " ".join(str(v) for v in section_content.values())
    return len(text.split())


def _render_download_card(doc_type: str, filename: str, file_bytes: bytes, section_content: dict, generated_at) -> None:
    word_count = _estimate_word_count(section_content)
    page_count = max(1, round(word_count / 400))
    timestamp_str = generated_at.strftime("%Y-%m-%d %H:%M:%S") if generated_at else "—"
    st.markdown(
        f'<div class="epm-download-card">'
        f'<div class="epm-download-title">📄 {html.escape(doc_type)} Ready</div>'
        f'<div class="epm-download-meta"><b>Filename:</b> {html.escape(filename)}</div>'
        f'<div class="epm-download-meta"><b>Word count:</b> {word_count:,} words (~{page_count} pages)</div>'
        f'<div class="epm-download-meta"><b>Generated:</b> {timestamp_str}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.download_button(
        label=f"⬇️ Download {doc_type} (.docx)",
        data=file_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Batched generation helpers — shared loop logic for FSD and TSD panels
# ---------------------------------------------------------------------------

def _run_batches(doc_label: str, batches: list, section_structure: list, content_key: str, status_key: str, generate_one_batch) -> None:
    """Run all not-yet-completed batches, persisting progress after each one.

    Stops (without raising) on the first batch failure so already-completed
    batches are preserved and only the failed batch needs retrying (NFR-08).
    """
    section_content = get(content_key) or {}
    batch_status = get(status_key) or ["pending"] * len(batches)

    tiles_placeholder = st.empty()
    status_placeholder = st.empty()

    def _render_tiles(active_idx=None):
        with tiles_placeholder.container():
            _render_section_tiles(section_structure, batches, batch_status, active_idx)

    _render_tiles()
    for i, batch in enumerate(batches):
        if batch_status[i] == "done":
            continue
        first_num, last_num = batch[0]["number"], batch[-1]["number"]
        status_placeholder.info(f"📄 Generating {doc_label} — Sections {first_num}–{last_num} of {len(section_structure)}…")
        _render_tiles(active_idx=i)
        try:
            raw = generate_one_batch(batch)
            _track_usage()
            section_content.update(parse_batch_sections(raw))
            batch_status[i] = "done"
            set_value(content_key, section_content)
            set_value(status_key, batch_status)
            _render_tiles()
        except LLMError as exc:
            batch_status[i] = "failed"
            set_value(status_key, batch_status)
            _render_tiles()
            status_placeholder.error(f"❌ Batch {i + 1} (Sections {first_num}–{last_num}) failed: {exc}")
            return
    status_placeholder.success(f"✅ {doc_label} sections generated")


def _render_batch_progress(section_structure: list, batches: list, status_key: str) -> tuple:
    """Return (completed_count, failed_index) for the current batch status."""
    batch_status = get(status_key) or ["pending"] * len(batches)
    completed = sum(1 for s in batch_status if s == "done")
    failed_index = next((i for i, s in enumerate(batch_status) if s == "failed"), None)
    return completed, failed_index


def _reset_failed_batch(status_key: str, failed_index: int) -> None:
    """Clear a failed batch's status back to pending so the next run retries it."""
    batch_status = get(status_key) or []
    batch_status[failed_index] = "pending"
    set_value(status_key, batch_status)


def _section_options(section_structure: list) -> list:
    return [f"{s['number']}. {s['title']}" for s in section_structure]


# ---------------------------------------------------------------------------
# Interactive generate -> review -> refine -> lock loop (CLAUDE.md §3.7/§3.8a)
#
# Per-section sequence, driven entirely from session state so each Streamlit rerun
# picks up exactly where the last one left off:
#   (a) pending_questions is None  -> fetch up to 6 pre-generation questions
#   (b) pending_answers is None    -> render the batch question form (or skip
#                                      straight through if zero questions came back)
#   (c) draft is None              -> stream the section content into the panel
#   (d) draft is set               -> pure correction review (no new questions)
#   (e) approve                    -> lock (content + pre-gen Q&A + correction
#                                      history stored as separate fields) and advance
#
# The loop logic itself lives in core/interactive_generator.py; everything here is
# UI plumbing plus the Skip Review fast-mode hand-off (point 4).
# ---------------------------------------------------------------------------

def _run_fast_mode(section_structure: list, locked_sections: dict, current_index: int, generate_one_batch, split_into_batches) -> dict:
    """Hand the not-yet-locked sections off to the existing legacy batch generator
    (SECTION_WEIGHT/split_into_batches/generate_*_batch — no new batching logic),
    preserving already-locked content and asking no pre-generation questions."""
    section_content = {num: entry["content"] for num, entry in locked_sections.items()}
    remaining = section_structure[current_index:]
    if not remaining:
        return section_content

    locked_context = interactive_gen.build_locked_context_text(locked_sections, section_structure)
    batches = split_into_batches(remaining)
    progress = st.empty()
    for i, batch in enumerate(batches, start=1):
        first_num, last_num = batch[0]["number"], batch[-1]["number"]
        progress.info(f"⚡ Fast mode — generating Sections {first_num}–{last_num} ({i} of {len(batches)})…")
        raw = generate_one_batch(batch, locked_context)
        _track_usage()
        section_content.update(parse_batch_sections(raw))
    progress.success("✅ Remaining sections generated via fast mode.")
    return section_content


def _render_fast_mode_button(loop_keys: dict, locked_sections: dict, current_index: int) -> bool:
    """Render the Skip Review escape hatch. Returns True if it was clicked (and thus
    already handled — caller should stop rendering the rest of the loop this run)."""
    doc_type = loop_keys["doc_type"]
    st.caption("Prefer not to review every section? Hand the rest off to fast batch generation.")
    if not st.button(f"⚡ Skip Review — Generate Full {doc_type} Now", key=f"fast_mode_btn_{doc_type}"):
        return False
    with st.spinner(f"Generating remaining {doc_type} sections via fast mode…"):
        section_content = loop_keys["fast_mode_generate"](locked_sections, current_index)
    set_value(loop_keys["content_key"], section_content)
    doc_bytes = loop_keys["build_document"](section_content)
    set_value(loop_keys["bytes_key"], doc_bytes)
    set_value(loop_keys["generated_at_key"], datetime.now())
    advance_to(loop_keys["next_step"])
    st.rerun()
    return True


def _render_pregeneration_question_form(loop_keys: dict, target_section: dict, questions: list) -> None:
    """Step (b): batch question form for ONE section, asked before any content for
    it exists. Every field is optional; Skip bypasses with no answers at all."""
    doc_type = loop_keys["doc_type"]
    num = target_section["number"]
    st.markdown(f"#### Section {num}: {target_section['title']} — Open Questions Before Drafting")
    st.caption(f"The agent identified {len(questions)} question(s) for this section. All are optional.")

    answers = {}
    for i, question in enumerate(questions):
        st.markdown(f"**Q{i + 1}.** {question}")
        answers[question] = st.text_input(
            "Answer (optional)",
            key=f"pregen_answer_{doc_type}_{num}_{i}",
            label_visibility="collapsed",
            placeholder="Type your answer here, or leave blank to skip…",
        )

    col1, col2 = st.columns(2)
    with col1:
        submit = st.button("✅ Submit Answers & Generate Section", type="primary", key=f"pregen_submit_{doc_type}_{num}")
    with col2:
        skip = st.button("⏭ Skip & Generate Section", key=f"pregen_skip_{doc_type}_{num}")

    if submit:
        set_value(loop_keys["pending_answers_key"], answers)
        st.rerun()
    elif skip:
        set_value(loop_keys["pending_answers_key"], {})
        st.rerun()


def _stream_draft(loop_keys: dict, locked_sections: dict, target_section: dict, instructions: str, pending_answers: dict, revision_count: int) -> str:
    """Step (c)/(d): stream the section content into the right-hand panel as it
    arrives, rather than blocking until the full section is generated."""
    doc_type = loop_keys["doc_type"]
    num = target_section["number"]
    max_attempts = interactive_gen.get_max_regeneration_attempts()
    label = (
        f"Generating {doc_type} Section {num} — {target_section['title']}…"
        if revision_count == 0
        else f"Refining {doc_type} Section {num} — attempt {revision_count} of {max_attempts}…"
    )
    st.markdown(f"#### Section {num}: {target_section['title']}")
    st.caption(label)
    placeholder = st.empty()

    if revision_count == 0:
        chunk_iter = loop_keys["stream_draft"](locked_sections, target_section, instructions, pending_answers)
    else:
        previous_draft = get(loop_keys["draft_prev_key"])
        feedback_text = get(loop_keys["draft_feedback_key"])
        chunk_iter = loop_keys["stream_regenerate"](locked_sections, target_section, instructions, pending_answers, previous_draft, feedback_text)

    buffer = ""
    for chunk in chunk_iter:
        buffer += chunk
        placeholder.markdown(buffer + " ▌")
    placeholder.markdown(buffer)
    return buffer.strip()


def _render_draft_review(draft: dict, num: str, title: str) -> tuple:
    """Step (d): pure content correction — never surfaces a new question."""
    st.markdown(f"#### Section {num}: {title}")
    st.markdown(draft["content"])

    correction_text = st.text_input(
        "Does this look right? Leave blank to approve, or describe a correction to regenerate.",
        key=f"correction_input_{num}_{len(draft.get('content') or '')}",
    )
    col1, col2 = st.columns(2)
    with col1:
        approve = st.button("✅ Approve & Lock", type="primary", key=f"approve_{num}_{id(draft)}")
    with col2:
        correct = st.button("🔁 Submit Correction & Regenerate", key=f"correct_{num}_{id(draft)}")
    return correction_text, approve, correct


def _render_interactive_loop(loop_keys: dict) -> None:
    """Drive one step of the interactive section loop for either FSD or TSD.

    `loop_keys` bundles the doc-type-specific session keys and callables so the
    loop logic (owned by core/interactive_generator.py) is written exactly once.
    """
    doc_type = loop_keys["doc_type"]
    section_structure = loop_keys["section_structure"]
    locked_sections = get(loop_keys["locked_key"]) or {}
    current_index = get(loop_keys["index_key"]) or 0

    if current_index >= len(section_structure):
        _finalise_interactive_document(loop_keys, section_structure, locked_sections)
        return

    if _render_fast_mode_button(loop_keys, locked_sections, current_index):
        return

    target_section = section_structure[current_index]
    num = target_section["number"]
    instructions = loop_keys["section_instructions"].get(num, target_section["description"])

    # (a) Pre-generation questions — fetched once per section, before any content exists.
    pending_questions = get(loop_keys["pending_questions_key"])
    if pending_questions is None:
        with st.spinner(f"Checking for open questions on {doc_type} Section {num}…"):
            pending_questions = loop_keys["generate_questions"](target_section, locked_sections)
        set_value(loop_keys["pending_questions_key"], pending_questions)
        set_value(loop_keys["pending_answers_key"], None)
        st.rerun()
        return

    # (b) Batch question form — skipped automatically if zero questions came back.
    pending_answers = get(loop_keys["pending_answers_key"])
    if pending_answers is None:
        if not pending_questions:
            set_value(loop_keys["pending_answers_key"], {})
            st.rerun()
            return
        _render_pregeneration_question_form(loop_keys, target_section, pending_questions)
        return

    # (c)/(d) Streamed content generation, then pure-correction review.
    revision_count = get(loop_keys["revision_key"]) or 0
    max_attempts = interactive_gen.get_max_regeneration_attempts()
    draft = get(loop_keys["draft_key"])

    if draft is None:
        try:
            content = _stream_draft(loop_keys, locked_sections, target_section, instructions, pending_answers, revision_count)
            _track_usage()
            set_value(loop_keys["draft_key"], {"content": content})
            st.rerun()
        except LLMError as exc:
            st.error(f"❌ {doc_type} Section {num} generation failed: {exc}")
        return

    correction_text, approve, correct = _render_draft_review(draft, num, target_section["title"])

    if approve:
        _lock_and_advance(loop_keys, locked_sections, current_index, num, draft, pending_questions, pending_answers, revision_count, force_locked=False)
    elif correct:
        _handle_correction(loop_keys, locked_sections, current_index, num, draft, pending_questions, pending_answers, correction_text, revision_count, max_attempts)


def _handle_correction(loop_keys: dict, locked_sections: dict, current_index: int, num: str, draft: dict, pending_questions: list, pending_answers: dict, correction_text: str, revision_count: int, max_attempts: int) -> None:
    """Either force-lock the latest draft (cap reached) or queue a feedback regeneration."""
    if not correction_text.strip():
        st.warning("Enter a correction, or use Approve & Lock to accept the draft as-is.")
        return

    history = (get(loop_keys["correction_history_key"]) or []) + [correction_text]
    set_value(loop_keys["correction_history_key"], history)

    if interactive_gen.should_force_lock(revision_count):
        _lock_and_advance(loop_keys, locked_sections, current_index, num, draft, pending_questions, pending_answers, revision_count, force_locked=True)
        st.warning(f"⚠️ Section {num} force-locked after {max_attempts} regeneration attempt(s) — flagged for manual review.")
    else:
        set_value(loop_keys["draft_prev_key"], draft)
        set_value(loop_keys["draft_feedback_key"], correction_text)
        set_value(loop_keys["revision_key"], revision_count + 1)
        set_value(loop_keys["draft_key"], None)
        st.rerun()


def _lock_and_advance(loop_keys: dict, locked_sections: dict, current_index: int, num: str, draft: dict, pending_questions: list, pending_answers: dict, revision_count: int, force_locked: bool) -> None:
    """Lock the current section — content, pre-generation Q&A, and correction history
    stored as separate fields (CLAUDE.md §3.8a) — reset per-section state, and advance."""
    correction_history = get(loop_keys["correction_history_key"]) or []
    locked_sections = interactive_gen.lock_section(
        locked_sections, num, draft, pending_questions, pending_answers, correction_history, revision_count, force_locked,
    )
    set_value(loop_keys["locked_key"], locked_sections)
    set_value(loop_keys["index_key"], current_index + 1)
    set_value(loop_keys["revision_key"], 0)
    set_value(loop_keys["draft_key"], None)
    set_value(loop_keys["draft_prev_key"], None)
    set_value(loop_keys["draft_feedback_key"], None)
    set_value(loop_keys["pending_questions_key"], None)
    set_value(loop_keys["pending_answers_key"], None)
    set_value(loop_keys["correction_history_key"], None)
    st.rerun()


def _finalise_interactive_document(loop_keys: dict, section_structure: list, locked_sections: dict) -> None:
    """All sections locked: flag force-locked ones, assemble the document, advance the workflow."""
    final_locked = interactive_gen.append_open_questions_addendum(locked_sections, section_structure)
    if final_locked != locked_sections:
        set_value(loop_keys["locked_key"], final_locked)
        locked_sections = final_locked

    content_dict = {num: entry["content"] for num, entry in locked_sections.items()}
    set_value(loop_keys["content_key"], content_dict)
    doc_bytes = loop_keys["build_document"](content_dict)
    set_value(loop_keys["bytes_key"], doc_bytes)
    set_value(loop_keys["generated_at_key"], datetime.now())
    advance_to(loop_keys["next_step"])
    st.rerun()


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_apply_custom_styles()
init_session_state()

current_step = get(KEY_WORKFLOW_STEP) or STEP_UPLOAD

nav_col, main_col = st.columns([0.22, 0.78], gap="large")

with nav_col:
    _render_step_navigator(current_step)
    if INTERACTIVE_GENERATION and current_step == STEP_GENERATE_FSD:
        fsd_nav_structure = get(KEY_FSD_SECTION_STRUCTURE) or fsd_gen.resolve_section_structure(get(KEY_FSD_TEMPLATE))
        _render_section_status_nav(fsd_nav_structure, get(KEY_FSD_LOCKED_SECTIONS) or {}, get(KEY_FSD_CURRENT_SECTION_INDEX) or 0)
    elif INTERACTIVE_GENERATION and current_step == STEP_GENERATE_TSD:
        tsd_nav_structure = get(KEY_TSD_SECTION_STRUCTURE) or tsd_gen.resolve_section_structure(get(KEY_TSD_TEMPLATE))
        _render_section_status_nav(tsd_nav_structure, get(KEY_TSD_LOCKED_SECTIONS) or {}, get(KEY_TSD_CURRENT_SECTION_INDEX) or 0)

with main_col:
    # ---------------------------------------------------------------------------
    # Page header
    # ---------------------------------------------------------------------------

    st.title(f"📋 {APP_TITLE}")
    st.caption(
        "Upload a Business Requirements Document, select the target SAP technology, "
        "and generate professional FSD and TSD Word documents in minutes."
    )
    st.divider()

    # ---------------------------------------------------------------------------
    # Step 1 — Upload BRD
    # ---------------------------------------------------------------------------

    with st.expander(f"**{_step_label(STEP_UPLOAD)} — Upload Business Requirements Document**", expanded=(current_step == STEP_UPLOAD)):
        st.markdown("Upload your BRD in **PDF** or **Word (.docx)** format. Maximum file size: 50 MB.")

        uploaded_brd = st.file_uploader(
            "BRD Document",
            type=["pdf", "docx"],
            key="brd_uploader",
            label_visibility="collapsed",
        )

        if uploaded_brd is not None:
            try:
                file_bytes, filename = validate_and_read_brd(uploaded_brd)
                with st.spinner(f"Parsing {filename}…"):
                    brd_dict = parse_brd(file_bytes, filename)

                set_value(KEY_BRD_DICT, brd_dict)
                st.success(
                    f"✅ **{filename}** uploaded successfully. "
                    f"({brd_dict['page_count']} pages, {brd_dict['word_count']:,} words)"
                )

                if current_step == STEP_UPLOAD:
                    advance_to(STEP_ADDITIONAL_INPUT)
                    st.rerun()

            except (FileValidationError, BRDParseError) as exc:
                st.error(f"❌ {exc}")
                set_value(KEY_BRD_DICT, None)

        elif get(KEY_BRD_DICT):
            brd = get(KEY_BRD_DICT)
            st.success(f"✅ **{brd['filename']}** ({brd['page_count']} pages, {brd['word_count']:,} words)")

    # ---------------------------------------------------------------------------
    # Step 2 — Supporting Documents, Discussion Notes, Project Metadata (all optional)
    # ---------------------------------------------------------------------------

    if current_step >= STEP_ADDITIONAL_INPUT and get(KEY_BRD_DICT):
        with st.expander(f"**{_step_label(STEP_ADDITIONAL_INPUT)} — Supporting Documents, Discussion Notes & Project Details (optional)**", expanded=(current_step == STEP_ADDITIONAL_INPUT)):
            st.markdown("**Supporting Documents (optional)** — meeting minutes, data dictionaries, process flows, existing reports, client emails")
            uploaded_supporting = st.file_uploader(
                "Supporting Documents",
                type=["pdf", "docx"],
                accept_multiple_files=True,
                key="supporting_docs_uploader",
                label_visibility="collapsed",
            )

            st.markdown("**Discussion Notes / Client Commentary (optional)**")
            discussion_notes = st.text_area(
                "Discussion Notes",
                value=get(KEY_DISCUSSION_NOTES) or "",
                max_chars=5000,
                placeholder="Paste notes from client workshops, verbal clarifications, email threads, or any additional context not captured in the BRD...",
                label_visibility="collapsed",
                key="discussion_notes_input",
            )

            st.markdown("**Project Metadata (optional)**")
            metadata = get(KEY_METADATA) or dict(DEFAULT_METADATA)
            col1, col2 = st.columns(2)
            with col1:
                consultant = st.text_input("Consultant Name", value=metadata.get("consultant", ""), key="meta_consultant")
                client = st.text_input("Client / Account Name", value=metadata.get("client", ""), key="meta_client")
            with col2:
                project = st.text_input("Project Name", value=metadata.get("project", ""), key="meta_project")
                engagement_code = st.text_input("Engagement Code", value=metadata.get("engagement_code", ""), key="meta_engagement")

            if st.button("Continue →", type="primary", key="continue_additional_input_btn"):
                try:
                    supporting_files = validate_and_read_supporting_docs(uploaded_supporting)
                    parsed_supporting = parse_supporting_docs(supporting_files)
                    set_value(KEY_SUPPORTING_DOCS, parsed_supporting)

                    set_value(KEY_DISCUSSION_NOTES, validate_discussion_notes(discussion_notes))
                    set_value(KEY_METADATA, {
                        "consultant": consultant or DEFAULT_METADATA["consultant"],
                        "client": client or DEFAULT_METADATA["client"],
                        "project": project or DEFAULT_METADATA["project"],
                        "engagement_code": engagement_code,
                    })

                    if parsed_supporting:
                        st.success(f"✅ {len(parsed_supporting)} supporting document(s) processed.")

                    if current_step == STEP_ADDITIONAL_INPUT:
                        advance_to(STEP_SELECT_TECHNOLOGY)
                        st.rerun()

                except (FileValidationError, BRDParseError) as exc:
                    st.error(f"❌ {exc}")

    # ---------------------------------------------------------------------------
    # Step 3 — Select SAP Technology
    # ---------------------------------------------------------------------------

    if current_step >= STEP_SELECT_TECHNOLOGY and get(KEY_BRD_DICT):
        with st.expander(f"**{_step_label(STEP_SELECT_TECHNOLOGY)} — Select SAP Technology and Optional Templates**", expanded=(current_step == STEP_SELECT_TECHNOLOGY)):

            col_left, col_right = st.columns([2, 1])

            with col_left:
                auto_mode = st.checkbox(
                    "I'm not sure — let the agent recommend the best technology",
                    value=get(KEY_TECHNOLOGY_AUTO) or False,
                    key="tech_auto_checkbox",
                )

                selected_technologies = []
                if not auto_mode:
                    selected_technologies = st.multiselect(
                        "Target SAP Technology (select one or more)",
                        options=SAP_TECHNOLOGIES,
                        default=get(KEY_TECHNOLOGIES) or [],
                        key="tech_multiselect",
                    )
                    for tech in selected_technologies:
                        st.info(f"**{tech}** — {SAP_TECHNOLOGY_DESCRIPTIONS.get(tech, '')}")
                else:
                    st.caption("Technology selection is disabled — the agent will recommend one or more technologies once the BRD is analysed in Step 4.")

            with col_right:
                st.markdown("**Optional: Upload document templates**")
                st.caption("Upload blank .docx files to use as structural skeletons. Generation proceeds without them.")

                fsd_template_file = st.file_uploader("FSD Template (.docx)", type=["docx"], key="fsd_tpl_uploader")

            if st.button("Confirm Technology & Proceed →", type="primary", key="confirm_tech_btn"):
                try:
                    if not auto_mode and not selected_technologies:
                        raise FileValidationError("Please select at least one SAP technology, or check 'I'm not sure'.")

                    fsd_tpl_bytes = validate_template(fsd_template_file)

                    set_value(KEY_TECHNOLOGY_AUTO, auto_mode)
                    if auto_mode:
                        set_value(KEY_TECHNOLOGIES, [])
                        set_value(KEY_TECHNOLOGY, "auto")
                    else:
                        set_value(KEY_TECHNOLOGIES, selected_technologies)
                        set_value(KEY_TECHNOLOGY, "+".join(selected_technologies))
                    set_value(KEY_FSD_TEMPLATE, fsd_tpl_bytes)

                    if fsd_tpl_bytes:
                        st.success("✅ FSD template uploaded.")

                    advance_to(STEP_ANALYSE)
                    st.rerun()

                except FileValidationError as exc:
                    st.error(f"❌ {exc}")

        if get(KEY_TECHNOLOGY) and current_step > STEP_SELECT_TECHNOLOGY:
            if get(KEY_TECHNOLOGY_AUTO) and not get(KEY_TECHNOLOGIES):
                st.markdown("**Technology selection:** pending agent recommendation")
            else:
                st.markdown(f"**Technology selected:** {', '.join(get(KEY_TECHNOLOGIES) or [get(KEY_TECHNOLOGY)])}")

    # ---------------------------------------------------------------------------
    # Step 4 — Analyse Input (pre-summarisation + domain auto-detection)
    # ---------------------------------------------------------------------------

    if current_step >= STEP_ANALYSE and get(KEY_BRD_DICT) and get(KEY_TECHNOLOGY):
        step4_title = (
            f"**{_step_label(STEP_ANALYSE)} — Analyse Input**"
            if INTERACTIVE_GENERATION
            else f"**{_step_label(STEP_ANALYSE)} — Analyse Input and Generate Clarification Questions**"
        )
        with st.expander(step4_title, expanded=(current_step == STEP_ANALYSE)):
            st.markdown(
                "The agent will pre-summarise all input (BRD, supporting documents, and discussion notes) into a "
                "structured requirements dict, auto-detect the relevant functional domain(s), and identify any gaps."
            )
            if INTERACTIVE_GENERATION:
                st.caption(
                    "Clarification is now handled inline: each FSD/TSD section may surface at most one "
                    "targeted question while it is being drafted, instead of an upfront question batch."
                )

            awaiting_tech_confirmation = (
                get(KEY_TECHNOLOGY_AUTO)
                and get(KEY_STRUCTURED_SUMMARY) is not None
                and current_step == STEP_ANALYSE
            )

            if current_step == STEP_ANALYSE and not get(KEY_STRUCTURED_SUMMARY):
                _render_input_summary_card()

            if not awaiting_tech_confirmation and st.button("🔍 Analyse Input", type="primary", key="analyse_btn"):
                with st.spinner("Pre-summarising all input documents…"):
                    try:
                        sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
                        combined_text = build_combined_input(
                            get(KEY_BRD_DICT), get(KEY_SUPPORTING_DOCS), get(KEY_DISCUSSION_NOTES),
                        )
                        structured_summary = generate_structured_summary(
                            combined_text, get(KEY_TECHNOLOGY), sap_skill, technology_options=SAP_TECHNOLOGIES,
                        )
                        _track_usage()
                        set_value(KEY_STRUCTURED_SUMMARY, structured_summary)
                        set_value(KEY_DETECTED_DOMAINS, structured_summary["domain"])

                        if get(KEY_TECHNOLOGY_AUTO):
                            set_value(KEY_RECOMMENDED_TECHNOLOGIES, structured_summary.get("recommended_technologies") or [])
                            st.rerun()
                        elif INTERACTIVE_GENERATION:
                            # FR-09/CLAUDE.md §3.7: the upfront clarification batch is
                            # superseded by per-section targeted questions in the loop.
                            set_value(KEY_ANSWERS, {})
                            advance_to(STEP_GENERATE_FSD)
                            st.rerun()
                        else:
                            domain_skills = load_domain_skills(structured_summary["domain"])
                            questions = generate_questions(
                                structured_summary=structured_summary,
                                technology=get(KEY_TECHNOLOGY),
                                sap_skill=sap_skill,
                                domain_skills=domain_skills,
                            )
                            _track_usage()
                            set_value(KEY_QUESTIONS, questions)
                            advance_to(STEP_QUESTIONS)
                            st.rerun()
                    except (BRDParseError, BRDSummariserError, LLMError) as exc:
                        st.error(f"❌ Input analysis failed: {exc}")

            if awaiting_tech_confirmation:
                recommended = [t for t in (get(KEY_RECOMMENDED_TECHNOLOGIES) or []) if t in SAP_TECHNOLOGIES]
                if recommended:
                    st.info(
                        "**Recommended technology/technologies:** " + ", ".join(recommended) +
                        "\n\nBased on the requirements, KPIs, and data sources identified in the BRD."
                    )
                else:
                    st.warning("The agent could not confidently recommend a technology from the BRD. Please select manually below.")

                confirmed_technologies = st.multiselect(
                    "Confirm or override the recommended technology/technologies",
                    options=SAP_TECHNOLOGIES,
                    default=recommended,
                    key="tech_recommendation_confirm",
                )

                accept_label = "✅ Accept & Continue" if INTERACTIVE_GENERATION else "✅ Accept & Generate Clarification Questions"
                if st.button(accept_label, type="primary", key="confirm_recommendation_btn"):
                    if not confirmed_technologies:
                        st.error("❌ Please select at least one SAP technology to proceed.")
                    else:
                        set_value(KEY_TECHNOLOGIES, confirmed_technologies)
                        set_value(KEY_TECHNOLOGY, "+".join(confirmed_technologies))

                        if INTERACTIVE_GENERATION:
                            # FR-09/CLAUDE.md §3.7: the upfront clarification batch is
                            # superseded by per-section targeted questions in the loop.
                            set_value(KEY_ANSWERS, {})
                            advance_to(STEP_GENERATE_FSD)
                            st.rerun()
                        else:
                            try:
                                structured_summary = get(KEY_STRUCTURED_SUMMARY)
                                sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
                                domain_skills = load_domain_skills(structured_summary["domain"])
                                questions = generate_questions(
                                    structured_summary=structured_summary,
                                    technology=get(KEY_TECHNOLOGY),
                                    sap_skill=sap_skill,
                                    domain_skills=domain_skills,
                                )
                                _track_usage()
                                set_value(KEY_QUESTIONS, questions)
                                advance_to(STEP_QUESTIONS)
                                st.rerun()
                            except LLMError as exc:
                                st.error(f"❌ Clarification question generation failed: {exc}")

            if get(KEY_STRUCTURED_SUMMARY) and current_step > STEP_ANALYSE:
                domains = get(KEY_DETECTED_DOMAINS) or []
                st.caption(f"Detected domain(s): {', '.join(domains) if domains else 'none — using all domain skills'}")

    # ---------------------------------------------------------------------------
    # Step 5 — Clarification Questions
    # ---------------------------------------------------------------------------

    if not INTERACTIVE_GENERATION and current_step >= STEP_QUESTIONS and get(KEY_QUESTIONS) is not None:
        questions = get(KEY_QUESTIONS)

        with st.expander(f"**{_step_label(STEP_QUESTIONS)} — Clarification Questions**", expanded=(current_step == STEP_QUESTIONS)):
            if not questions:
                st.info("✅ The input is sufficiently complete. No clarification questions required.")
                answers = {}
            else:
                st.markdown(
                    f"The agent identified **{len(questions)} clarification question(s)**. "
                    "All questions are optional — leave any blank to skip."
                )
                answers = get(KEY_ANSWERS) or {}

                for q in questions:
                    qid = str(q.get("id", ""))
                    category = q.get("category", "")
                    impact = q.get("impact", "")
                    question_text = q.get("question", "")

                    st.markdown(f"**Q{qid}** _{category}_")
                    st.markdown(question_text)
                    if impact:
                        st.caption(f"Impact: {impact}")
                    answer = st.text_input(
                        "Answer (optional)",
                        value=answers.get(qid, ""),
                        key=f"answer_{qid}",
                        label_visibility="collapsed",
                        placeholder="Type your answer here, or leave blank to skip…",
                    )
                    answers[qid] = answer
                    st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚡ Generate FSD", type="primary", key="generate_btn"):
                    set_value(KEY_ANSWERS, answers)
                    advance_to(STEP_GENERATE_FSD)
                    st.rerun()
            with col2:
                if st.button("⏭ Skip All & Generate FSD", key="skip_btn"):
                    set_value(KEY_ANSWERS, {})
                    advance_to(STEP_GENERATE_FSD)
                    st.rerun()

    # ---------------------------------------------------------------------------
    # Step 6 — FSD Generation (interactive per-section loop, or legacy batch fallback)
    # ---------------------------------------------------------------------------

    if current_step == STEP_GENERATE_FSD:
        with st.expander(f"**{_step_label(STEP_GENERATE_FSD)} — Generating Functional Specification Document (FSD)**", expanded=True):
            section_structure = get(KEY_FSD_SECTION_STRUCTURE)
            if section_structure is None:
                section_structure = fsd_gen.resolve_section_structure(get(KEY_FSD_TEMPLATE))
                set_value(KEY_FSD_SECTION_STRUCTURE, section_structure)

            sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
            domain_skills = load_domain_skills(get(KEY_DETECTED_DOMAINS))

            if INTERACTIVE_GENERATION:
                def _fsd_generate_questions(target_section, locked_sections):
                    return interactive_gen.generate_section_questions(
                        section_spec=target_section,
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology_context={"technology": get(KEY_TECHNOLOGY), "sap_skill": sap_skill, "domain_skills": domain_skills},
                        locked_sections=locked_sections,
                        doc_type="FSD",
                    )

                def _fsd_stream_draft(locked_sections, target_section, instructions, pending_answers):
                    return interactive_gen.stream_section_draft(
                        doc_type="FSD",
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        pre_generation_answers=pending_answers,
                        metadata=get(KEY_METADATA),
                        section_structure=section_structure,
                        locked_sections=locked_sections,
                        target_section=target_section,
                        instructions=instructions,
                    )

                def _fsd_stream_regenerate(locked_sections, target_section, instructions, pending_answers, previous_draft, feedback_text):
                    return interactive_gen.stream_feedback_regeneration(
                        doc_type="FSD",
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        pre_generation_answers=pending_answers,
                        metadata=get(KEY_METADATA),
                        section_structure=section_structure,
                        locked_sections=locked_sections,
                        target_section=target_section,
                        instructions=instructions,
                        previous_content=(previous_draft or {}).get("content", ""),
                        feedback_text=feedback_text,
                    )

                def _fsd_fast_mode_generate(locked_sections, current_index):
                    def _one_batch(batch, locked_context):
                        return fsd_gen.generate_fsd_batch(
                            structured_summary=get(KEY_STRUCTURED_SUMMARY),
                            technology=get(KEY_TECHNOLOGY),
                            sap_skill=sap_skill,
                            domain_skills=domain_skills,
                            clarification_answers={},
                            metadata=get(KEY_METADATA),
                            section_structure=section_structure,
                            batch_sections=batch,
                            locked_context=locked_context,
                        )
                    return _run_fast_mode(section_structure, locked_sections, current_index, _one_batch, fsd_gen.split_into_batches)

                _render_interactive_loop({
                    "doc_type": "FSD",
                    "section_structure": section_structure,
                    "locked_key": KEY_FSD_LOCKED_SECTIONS,
                    "index_key": KEY_FSD_CURRENT_SECTION_INDEX,
                    "pending_questions_key": KEY_FSD_PENDING_QUESTIONS,
                    "pending_answers_key": KEY_FSD_PENDING_ANSWERS,
                    "draft_key": KEY_FSD_CURRENT_DRAFT,
                    "revision_key": KEY_FSD_REVISION_COUNT,
                    "draft_prev_key": KEY_FSD_DRAFT_PREV,
                    "draft_feedback_key": KEY_FSD_DRAFT_FEEDBACK,
                    "correction_history_key": KEY_FSD_CORRECTION_HISTORY,
                    "section_instructions": fsd_gen.FSD_SECTION_INSTRUCTIONS,
                    "generate_questions": _fsd_generate_questions,
                    "stream_draft": _fsd_stream_draft,
                    "stream_regenerate": _fsd_stream_regenerate,
                    "fast_mode_generate": _fsd_fast_mode_generate,
                    "content_key": KEY_FSD_SECTION_CONTENT,
                    "bytes_key": KEY_FSD_BYTES,
                    "build_document": lambda content_dict: fsd_gen.build_fsd_bytes(content_dict, section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA)),
                    "generated_at_key": KEY_FSD_GENERATED_AT,
                    "next_step": STEP_FSD_DOWNLOAD,
                })
            else:
                batches = fsd_gen.split_into_batches(section_structure)
                completed, failed_index = _render_batch_progress(section_structure, batches, KEY_FSD_BATCH_STATUS)
                st.progress(completed / len(batches) if batches else 1.0)

                if not (failed_index is None and completed >= len(batches)):
                    _render_section_tiles(section_structure, batches, get(KEY_FSD_BATCH_STATUS) or ["pending"] * len(batches))

                def _generate_one_fsd_batch(batch):
                    return fsd_gen.generate_fsd_batch(
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        clarification_answers=get(KEY_ANSWERS) or {},
                        metadata=get(KEY_METADATA),
                        section_structure=section_structure,
                        batch_sections=batch,
                    )

                if failed_index is not None:
                    batch = batches[failed_index]
                    st.error(f"Batch {failed_index + 1} (Sections {batch[0]['number']}–{batch[-1]['number']}) failed to generate.")
                    if st.button("🔁 Retry Failed Batch", type="primary", key="retry_fsd_batch_btn"):
                        _reset_failed_batch(KEY_FSD_BATCH_STATUS, failed_index)
                        _run_batches("FSD", batches, section_structure, KEY_FSD_SECTION_CONTENT, KEY_FSD_BATCH_STATUS, _generate_one_fsd_batch)
                        st.rerun()
                elif completed < len(batches):
                    if st.button("⚡ Generate FSD", type="primary", key="run_fsd_batches_btn"):
                        _run_batches("FSD", batches, section_structure, KEY_FSD_SECTION_CONTENT, KEY_FSD_BATCH_STATUS, _generate_one_fsd_batch)
                        st.rerun()
                else:
                    fsd_bytes = fsd_gen.build_fsd_bytes(get(KEY_FSD_SECTION_CONTENT), section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA))
                    set_value(KEY_FSD_BYTES, fsd_bytes)
                    set_value(KEY_FSD_GENERATED_AT, datetime.now())
                    advance_to(STEP_FSD_DOWNLOAD)
                    st.rerun()

    # ---------------------------------------------------------------------------
    # Step 7 — FSD Download, Section Regeneration, Proceed to TSD Gate
    # ---------------------------------------------------------------------------

    if current_step >= STEP_FSD_DOWNLOAD and get(KEY_FSD_BYTES):
        with st.expander(f"**{_step_label(STEP_FSD_DOWNLOAD)} — Download FSD and Optionally Regenerate a Section**", expanded=(current_step == STEP_FSD_DOWNLOAD)):
            st.success("🎉 The FSD has been generated successfully!")

            brd_name = get(KEY_BRD_DICT).get("filename", "brd").rsplit(".", 1)[0]
            tech_slug = (get(KEY_TECHNOLOGY) or "sap").replace(" ", "_").replace("/", "-")
            fsd_filename = f"{brd_name}_{tech_slug}_FSD.docx"

            _render_download_card(
                "FSD", fsd_filename, get(KEY_FSD_BYTES),
                get(KEY_FSD_SECTION_CONTENT) or {}, get(KEY_FSD_GENERATED_AT),
            )

            st.divider()
            st.markdown("**Regenerate a Section**")
            fsd_section_structure = get(KEY_FSD_SECTION_STRUCTURE)
            fsd_options = _section_options(fsd_section_structure)
            selected_fsd_section = st.selectbox("Section to regenerate", fsd_options, key="fsd_regen_select")

            if st.button("🔁 Regenerate Section", key="fsd_regen_btn"):
                num = selected_fsd_section.split(".", 1)[0]
                target_section = next(s for s in fsd_section_structure if s["number"] == num)
                instructions = fsd_gen.FSD_SECTION_INSTRUCTIONS.get(num, target_section["description"])
                sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
                domain_skills = load_domain_skills(get(KEY_DETECTED_DOMAINS))

                with st.spinner(f"Regenerating Section {num}…"):
                    try:
                        new_content = regenerate_section(
                            doc_type="FSD",
                            technology=get(KEY_TECHNOLOGY),
                            sap_skill=sap_skill,
                            domain_skills=domain_skills,
                            structured_summary=get(KEY_STRUCTURED_SUMMARY),
                            clarification_answers=get(KEY_ANSWERS) or {},
                            existing_section_titles=fsd_options,
                            target_section=target_section,
                            instructions=instructions,
                        )
                        _track_usage()
                        section_content = get(KEY_FSD_SECTION_CONTENT)
                        section_content[num] = new_content
                        set_value(KEY_FSD_SECTION_CONTENT, section_content)

                        fsd_bytes = fsd_gen.build_fsd_bytes(section_content, fsd_section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA))
                        set_value(KEY_FSD_BYTES, fsd_bytes)
                        set_value(KEY_FSD_GENERATED_AT, datetime.now())
                        st.success(f"✅ Section {num} regenerated. Re-download above.")
                        st.rerun()
                    except LLMError as exc:
                        st.error(f"❌ Regeneration failed: {exc}")

            st.divider()
            if st.button("➡️ Proceed to TSD Generation", type="primary", key="proceed_tsd_btn"):
                advance_to(STEP_TSD_INPUT)
                st.rerun()

    # ---------------------------------------------------------------------------
    # Step 8 — TSD Input Choice (Use Session FSD vs Re-upload Revised FSD)
    # ---------------------------------------------------------------------------

    if current_step >= STEP_TSD_INPUT:
        with st.expander(f"**{_step_label(STEP_TSD_INPUT)} — Provide FSD Input for TSD Generation**", expanded=(current_step == STEP_TSD_INPUT)):
            st.markdown(
                "The TSD will be generated from the full content of the FSD above. "
                "If you revised the FSD locally, upload your revised version before proceeding."
            )

            fsd_input_option = st.radio(
                "FSD Input",
                ["Use Session FSD", "Upload Revised FSD"],
                key="tsd_input_option",
            )

            reuploaded_fsd = None
            if fsd_input_option == "Upload Revised FSD":
                reuploaded_fsd = st.file_uploader("Revised FSD (.docx)", type=["docx"], key="tsd_fsd_reupload")

            tsd_template_file = st.file_uploader("TSD Template (.docx) — optional", type=["docx"], key="tsd_tpl_uploader")

            if st.button("Confirm & Continue →", type="primary", key="confirm_tsd_input_btn"):
                try:
                    tsd_tpl_bytes = validate_template(tsd_template_file)

                    if fsd_input_option == "Use Session FSD":
                        fsd_bytes_to_parse, fsd_source_name = get(KEY_FSD_BYTES), "generated_fsd.docx"
                    else:
                        if reuploaded_fsd is None:
                            raise FileValidationError("Please upload a revised FSD .docx file.")
                        fsd_bytes_to_parse, fsd_source_name = validate_and_read_brd(reuploaded_fsd)

                    fsd_parsed = parse_brd(fsd_bytes_to_parse, fsd_source_name)
                    set_value(KEY_FSD_FULL_TEXT, fsd_parsed["raw_text"])
                    set_value(KEY_TSD_TEMPLATE, tsd_tpl_bytes)

                    st.success(f"✅ FSD input confirmed ({fsd_parsed['word_count']:,} words).")

                    if current_step == STEP_TSD_INPUT:
                        advance_to(STEP_GENERATE_TSD)
                        st.rerun()

                except (FileValidationError, BRDParseError) as exc:
                    st.error(f"❌ {exc}")

    # ---------------------------------------------------------------------------
    # Step 9 — TSD Generation (interactive per-section loop, or legacy batch fallback)
    # ---------------------------------------------------------------------------

    if current_step == STEP_GENERATE_TSD:
        with st.expander(f"**{_step_label(STEP_GENERATE_TSD)} — Generating Technical Specification Document (TSD)**", expanded=True):
            tsd_section_structure = get(KEY_TSD_SECTION_STRUCTURE)
            if tsd_section_structure is None:
                tsd_section_structure = tsd_gen.resolve_section_structure(get(KEY_TSD_TEMPLATE))
                set_value(KEY_TSD_SECTION_STRUCTURE, tsd_section_structure)

            sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
            domain_skills = load_domain_skills(get(KEY_DETECTED_DOMAINS))

            if INTERACTIVE_GENERATION:
                def _tsd_generate_questions(target_section, locked_sections):
                    return interactive_gen.generate_section_questions(
                        section_spec=target_section,
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology_context={"technology": get(KEY_TECHNOLOGY), "sap_skill": sap_skill, "domain_skills": domain_skills},
                        locked_sections=locked_sections,
                        doc_type="TSD",
                    )

                def _tsd_stream_draft(locked_sections, target_section, instructions, pending_answers):
                    return interactive_gen.stream_section_draft(
                        doc_type="TSD",
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        pre_generation_answers=pending_answers,
                        metadata=get(KEY_METADATA),
                        section_structure=tsd_section_structure,
                        locked_sections=locked_sections,
                        target_section=target_section,
                        instructions=instructions,
                        fsd_full_text=get(KEY_FSD_FULL_TEXT),
                    )

                def _tsd_stream_regenerate(locked_sections, target_section, instructions, pending_answers, previous_draft, feedback_text):
                    return interactive_gen.stream_feedback_regeneration(
                        doc_type="TSD",
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        pre_generation_answers=pending_answers,
                        metadata=get(KEY_METADATA),
                        section_structure=tsd_section_structure,
                        locked_sections=locked_sections,
                        target_section=target_section,
                        instructions=instructions,
                        previous_content=(previous_draft or {}).get("content", ""),
                        feedback_text=feedback_text,
                        fsd_full_text=get(KEY_FSD_FULL_TEXT),
                    )

                def _tsd_fast_mode_generate(locked_sections, current_index):
                    def _one_batch(batch, locked_context):
                        return tsd_gen.generate_tsd_batch(
                            fsd_full_text=get(KEY_FSD_FULL_TEXT),
                            technology=get(KEY_TECHNOLOGY),
                            sap_skill=sap_skill,
                            domain_skills=domain_skills,
                            structured_summary=get(KEY_STRUCTURED_SUMMARY),
                            clarification_answers={},
                            metadata=get(KEY_METADATA),
                            section_structure=tsd_section_structure,
                            batch_sections=batch,
                            locked_context=locked_context,
                        )
                    return _run_fast_mode(tsd_section_structure, locked_sections, current_index, _one_batch, tsd_gen.split_into_batches)

                _render_interactive_loop({
                    "doc_type": "TSD",
                    "section_structure": tsd_section_structure,
                    "locked_key": KEY_TSD_LOCKED_SECTIONS,
                    "index_key": KEY_TSD_CURRENT_SECTION_INDEX,
                    "pending_questions_key": KEY_TSD_PENDING_QUESTIONS,
                    "pending_answers_key": KEY_TSD_PENDING_ANSWERS,
                    "draft_key": KEY_TSD_CURRENT_DRAFT,
                    "revision_key": KEY_TSD_REVISION_COUNT,
                    "draft_prev_key": KEY_TSD_DRAFT_PREV,
                    "draft_feedback_key": KEY_TSD_DRAFT_FEEDBACK,
                    "correction_history_key": KEY_TSD_CORRECTION_HISTORY,
                    "section_instructions": tsd_gen.TSD_SECTION_INSTRUCTIONS,
                    "generate_questions": _tsd_generate_questions,
                    "stream_draft": _tsd_stream_draft,
                    "stream_regenerate": _tsd_stream_regenerate,
                    "fast_mode_generate": _tsd_fast_mode_generate,
                    "content_key": KEY_TSD_SECTION_CONTENT,
                    "bytes_key": KEY_TSD_BYTES,
                    "build_document": lambda content_dict: tsd_gen.build_tsd_bytes(content_dict, tsd_section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA)),
                    "generated_at_key": KEY_TSD_GENERATED_AT,
                    "next_step": STEP_TSD_DOWNLOAD,
                })
            else:
                tsd_batches = tsd_gen.split_into_batches(tsd_section_structure)
                completed, failed_index = _render_batch_progress(tsd_section_structure, tsd_batches, KEY_TSD_BATCH_STATUS)
                st.progress(completed / len(tsd_batches) if tsd_batches else 1.0)

                if not (failed_index is None and completed >= len(tsd_batches)):
                    _render_section_tiles(tsd_section_structure, tsd_batches, get(KEY_TSD_BATCH_STATUS) or ["pending"] * len(tsd_batches))

                def _generate_one_tsd_batch(batch):
                    return tsd_gen.generate_tsd_batch(
                        fsd_full_text=get(KEY_FSD_FULL_TEXT),
                        technology=get(KEY_TECHNOLOGY),
                        sap_skill=sap_skill,
                        domain_skills=domain_skills,
                        structured_summary=get(KEY_STRUCTURED_SUMMARY),
                        clarification_answers=get(KEY_ANSWERS) or {},
                        metadata=get(KEY_METADATA),
                        section_structure=tsd_section_structure,
                        batch_sections=batch,
                    )

                if failed_index is not None:
                    batch = tsd_batches[failed_index]
                    st.error(f"Batch {failed_index + 1} (Sections {batch[0]['number']}–{batch[-1]['number']}) failed to generate.")
                    if st.button("🔁 Retry Failed Batch", type="primary", key="retry_tsd_batch_btn"):
                        _reset_failed_batch(KEY_TSD_BATCH_STATUS, failed_index)
                        _run_batches("TSD", tsd_batches, tsd_section_structure, KEY_TSD_SECTION_CONTENT, KEY_TSD_BATCH_STATUS, _generate_one_tsd_batch)
                        st.rerun()
                elif completed < len(tsd_batches):
                    if st.button("⚡ Generate TSD", type="primary", key="run_tsd_batches_btn"):
                        _run_batches("TSD", tsd_batches, tsd_section_structure, KEY_TSD_SECTION_CONTENT, KEY_TSD_BATCH_STATUS, _generate_one_tsd_batch)
                        st.rerun()
                else:
                    tsd_bytes = tsd_gen.build_tsd_bytes(get(KEY_TSD_SECTION_CONTENT), tsd_section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA))
                    set_value(KEY_TSD_BYTES, tsd_bytes)
                    set_value(KEY_TSD_GENERATED_AT, datetime.now())
                    advance_to(STEP_TSD_DOWNLOAD)
                    st.rerun()

    # ---------------------------------------------------------------------------
    # Step 10 — TSD Download, Section Regeneration, Start Over
    # ---------------------------------------------------------------------------

    if current_step >= STEP_TSD_DOWNLOAD and get(KEY_TSD_BYTES):
        with st.expander(f"**{_step_label(STEP_TSD_DOWNLOAD)} — Download TSD and Optionally Regenerate a Section**", expanded=True):
            st.success("🎉 The TSD has been generated successfully!")

            brd_name = get(KEY_BRD_DICT).get("filename", "brd").rsplit(".", 1)[0]
            tech_slug = (get(KEY_TECHNOLOGY) or "sap").replace(" ", "_").replace("/", "-")
            tsd_filename = f"{brd_name}_{tech_slug}_TSD.docx"

            _render_download_card(
                "TSD", tsd_filename, get(KEY_TSD_BYTES),
                get(KEY_TSD_SECTION_CONTENT) or {}, get(KEY_TSD_GENERATED_AT),
            )

            st.divider()
            st.markdown("**Regenerate a Section**")
            tsd_section_structure = get(KEY_TSD_SECTION_STRUCTURE)
            tsd_options = _section_options(tsd_section_structure)
            selected_tsd_section = st.selectbox("Section to regenerate", tsd_options, key="tsd_regen_select")

            if st.button("🔁 Regenerate Section", key="tsd_regen_btn"):
                num = selected_tsd_section.split(".", 1)[0]
                target_section = next(s for s in tsd_section_structure if s["number"] == num)
                instructions = tsd_gen.TSD_SECTION_INSTRUCTIONS.get(num, target_section["description"])
                sap_skill = load_sap_skill(get(KEY_TECHNOLOGY))
                domain_skills = load_domain_skills(get(KEY_DETECTED_DOMAINS))

                with st.spinner(f"Regenerating Section {num}…"):
                    try:
                        new_content = regenerate_section(
                            doc_type="TSD",
                            technology=get(KEY_TECHNOLOGY),
                            sap_skill=sap_skill,
                            domain_skills=domain_skills,
                            structured_summary=get(KEY_STRUCTURED_SUMMARY),
                            clarification_answers=get(KEY_ANSWERS) or {},
                            existing_section_titles=tsd_options,
                            target_section=target_section,
                            instructions=instructions,
                            fsd_full_text=get(KEY_FSD_FULL_TEXT),
                        )
                        _track_usage()
                        section_content = get(KEY_TSD_SECTION_CONTENT)
                        section_content[num] = new_content
                        set_value(KEY_TSD_SECTION_CONTENT, section_content)

                        tsd_bytes = tsd_gen.build_tsd_bytes(section_content, tsd_section_structure, get(KEY_TECHNOLOGY), get(KEY_METADATA))
                        set_value(KEY_TSD_BYTES, tsd_bytes)
                        set_value(KEY_TSD_GENERATED_AT, datetime.now())
                        st.success(f"✅ Section {num} regenerated. Re-download above.")
                        st.rerun()
                    except LLMError as exc:
                        st.error(f"❌ Regeneration failed: {exc}")

            st.divider()
            if st.button("🔄 Start Over — Process a New BRD", key="reset_btn"):
                reset_all()
                st.rerun()

_render_cost_footer()
