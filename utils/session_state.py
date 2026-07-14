"""Streamlit session state key constants and helper functions."""

import streamlit as st

# ---------------------------------------------------------------------------
# Session state key constants — never use raw strings in app.py
# ---------------------------------------------------------------------------

KEY_BRD_DICT = "brd_dict"
KEY_SUPPORTING_DOCS = "supporting_docs"
KEY_DISCUSSION_NOTES = "discussion_notes"
KEY_METADATA = "project_metadata"
KEY_TECHNOLOGY = "selected_technology"
KEY_TECHNOLOGIES = "selected_technologies"
KEY_TECHNOLOGY_AUTO = "technology_auto_mode"
KEY_RECOMMENDED_TECHNOLOGIES = "recommended_technologies"
KEY_FSD_TEMPLATE = "fsd_template_bytes"
KEY_TSD_TEMPLATE = "tsd_template_bytes"
KEY_STRUCTURED_SUMMARY = "structured_summary"
KEY_DETECTED_DOMAINS = "detected_domains"
KEY_QUESTIONS = "clarification_questions"
KEY_ANSWERS = "clarification_answers"
KEY_FSD_SECTION_STRUCTURE = "fsd_section_structure"
KEY_FSD_SECTION_CONTENT = "fsd_section_content"
KEY_FSD_BATCH_STATUS = "fsd_batch_status"
KEY_FSD_BYTES = "fsd_bytes"
KEY_FSD_FULL_TEXT = "fsd_full_text"
KEY_TSD_SECTION_STRUCTURE = "tsd_section_structure"
KEY_TSD_SECTION_CONTENT = "tsd_section_content"
KEY_TSD_BATCH_STATUS = "tsd_batch_status"
KEY_TSD_BYTES = "tsd_bytes"
KEY_WORKFLOW_STEP = "workflow_step"

# Interactive section-by-section generation loop (CLAUDE.md §3.7/§3.8a) — one entry
# per doc type. locked_sections is keyed by section number: {content,
# pre_generation_questions, pre_generation_answers, correction_history,
# revision_count, force_locked}. current_section_index points at the section
# currently being drafted.
#
# Per-section phase state (reset on lock/advance):
#   pending_questions: None until generate_section_questions() has run for this
#     section (step a); [] or a non-empty list once fetched.
#   pending_answers: None until the step-(b) question form has been submitted
#     (or skipped) for this section; {} or a filled dict once resolved. The
#     None/dict distinction is what drives the phase transition from "asking
#     questions" to "generating content".
#   draft: the in-flight/streamed content draft, or None before the first chunk.
#   draft_prev / draft_feedback: the previous content + correction text used for
#     the most recent regeneration (step d).
#   correction_history: every correction text entered during step d for this
#     section, in order — stored separately from pending_answers when locked.
KEY_FSD_LOCKED_SECTIONS = "fsd_locked_sections"
KEY_FSD_CURRENT_SECTION_INDEX = "fsd_current_section_index"
KEY_FSD_PENDING_QUESTIONS = "fsd_pending_questions"
KEY_FSD_PENDING_ANSWERS = "fsd_pending_answers"
KEY_FSD_CURRENT_DRAFT = "fsd_current_draft"
KEY_FSD_REVISION_COUNT = "fsd_revision_count"
KEY_FSD_DRAFT_PREV = "fsd_draft_prev"
KEY_FSD_DRAFT_FEEDBACK = "fsd_draft_feedback"
KEY_FSD_CORRECTION_HISTORY = "fsd_correction_history"
KEY_TSD_LOCKED_SECTIONS = "tsd_locked_sections"
KEY_TSD_CURRENT_SECTION_INDEX = "tsd_current_section_index"
KEY_TSD_PENDING_QUESTIONS = "tsd_pending_questions"
KEY_TSD_PENDING_ANSWERS = "tsd_pending_answers"
KEY_TSD_CURRENT_DRAFT = "tsd_current_draft"
KEY_TSD_REVISION_COUNT = "tsd_revision_count"
KEY_TSD_DRAFT_PREV = "tsd_draft_prev"
KEY_TSD_DRAFT_FEEDBACK = "tsd_draft_feedback"
KEY_TSD_CORRECTION_HISTORY = "tsd_correction_history"

# Token usage / cost tracking (CHANGE 2 — token and cost footer)
KEY_STEP_INPUT_TOKENS = "step_input_tokens"
KEY_STEP_OUTPUT_TOKENS = "step_output_tokens"
KEY_SESSION_INPUT_TOKENS = "session_input_tokens"
KEY_SESSION_OUTPUT_TOKENS = "session_output_tokens"

# Document generation timestamps (CHANGE 5 — download card)
KEY_FSD_GENERATED_AT = "fsd_generated_at"
KEY_TSD_GENERATED_AT = "tsd_generated_at"

# claude-sonnet-4-6 pricing (USD per token)
PRICE_PER_INPUT_TOKEN = 3.00 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 15.00 / 1_000_000

_ALL_KEYS = [
    KEY_BRD_DICT,
    KEY_SUPPORTING_DOCS,
    KEY_DISCUSSION_NOTES,
    KEY_METADATA,
    KEY_TECHNOLOGY,
    KEY_TECHNOLOGIES,
    KEY_TECHNOLOGY_AUTO,
    KEY_RECOMMENDED_TECHNOLOGIES,
    KEY_FSD_TEMPLATE,
    KEY_TSD_TEMPLATE,
    KEY_STRUCTURED_SUMMARY,
    KEY_DETECTED_DOMAINS,
    KEY_QUESTIONS,
    KEY_ANSWERS,
    KEY_FSD_SECTION_STRUCTURE,
    KEY_FSD_SECTION_CONTENT,
    KEY_FSD_BATCH_STATUS,
    KEY_FSD_BYTES,
    KEY_FSD_FULL_TEXT,
    KEY_TSD_SECTION_STRUCTURE,
    KEY_TSD_SECTION_CONTENT,
    KEY_TSD_BATCH_STATUS,
    KEY_TSD_BYTES,
    KEY_WORKFLOW_STEP,
    KEY_FSD_LOCKED_SECTIONS,
    KEY_FSD_CURRENT_SECTION_INDEX,
    KEY_FSD_PENDING_QUESTIONS,
    KEY_FSD_PENDING_ANSWERS,
    KEY_FSD_CURRENT_DRAFT,
    KEY_FSD_REVISION_COUNT,
    KEY_FSD_DRAFT_PREV,
    KEY_FSD_DRAFT_FEEDBACK,
    KEY_FSD_CORRECTION_HISTORY,
    KEY_TSD_LOCKED_SECTIONS,
    KEY_TSD_CURRENT_SECTION_INDEX,
    KEY_TSD_PENDING_QUESTIONS,
    KEY_TSD_PENDING_ANSWERS,
    KEY_TSD_CURRENT_DRAFT,
    KEY_TSD_REVISION_COUNT,
    KEY_TSD_DRAFT_PREV,
    KEY_TSD_DRAFT_FEEDBACK,
    KEY_TSD_CORRECTION_HISTORY,
    KEY_STEP_INPUT_TOKENS,
    KEY_STEP_OUTPUT_TOKENS,
    KEY_SESSION_INPUT_TOKENS,
    KEY_SESSION_OUTPUT_TOKENS,
    KEY_FSD_GENERATED_AT,
    KEY_TSD_GENERATED_AT,
]

# Step numbers used by KEY_WORKFLOW_STEP — follows the FSD Section 7 workflow table.
# These are internal control-flow constants (used for `current_step >= STEP_X` checks)
# and must stay stable — they are NOT the numbers shown to the user. STEP_QUESTIONS
# only applies in legacy batched mode (INTERACTIVE_GENERATION=false); when the
# interactive per-section loop is active it is skipped entirely. Use
# active_step_sequence()/display_step_number() below to get the contiguous,
# gap-free numbers that should actually be rendered in the UI.
STEP_UPLOAD = 1               # Upload BRD (mandatory)
STEP_ADDITIONAL_INPUT = 2     # Supporting docs + discussion notes + project metadata (all optional)
STEP_SELECT_TECHNOLOGY = 3    # SAP technology + optional FSD/TSD templates
STEP_ANALYSE = 4              # Pre-summarisation + domain auto-detection
STEP_QUESTIONS = 5            # Clarification questions (legacy batched mode only)
STEP_GENERATE_FSD = 6         # FSD generation (interactive loop or legacy batch)
STEP_FSD_DOWNLOAD = 7         # FSD download + section regeneration + "proceed to TSD" gate
STEP_TSD_INPUT = 8            # FSD input choice (session vs re-upload) + optional TSD template
STEP_GENERATE_TSD = 9         # TSD generation (interactive loop or legacy batch)
STEP_TSD_DOWNLOAD = 10        # TSD download + section regeneration + start over

# Ordered list of every step constant, in display order. active_step_sequence()
# filters this down to whichever steps actually appear for the current generation
# mode, so that display_step_number() always returns contiguous numbers — fixes the
# bug where STEP_QUESTIONS being hidden in interactive mode left the UI jumping
# straight from "Step 4" to "Step 6".
_WORKFLOW_STEP_ORDER: list = [
    STEP_UPLOAD,
    STEP_ADDITIONAL_INPUT,
    STEP_SELECT_TECHNOLOGY,
    STEP_ANALYSE,
    STEP_QUESTIONS,
    STEP_GENERATE_FSD,
    STEP_FSD_DOWNLOAD,
    STEP_TSD_INPUT,
    STEP_GENERATE_TSD,
    STEP_TSD_DOWNLOAD,
]

# Steps that only ever appear in legacy batched mode — excluded from the active
# sequence when the interactive per-section loop is running.
_LEGACY_ONLY_STEPS: set = {STEP_QUESTIONS}


def active_step_sequence(interactive_generation: bool) -> list:
    """Return the STEP_* constants actually shown to the user, in display order,
    for the given generation mode."""
    if interactive_generation:
        return [s for s in _WORKFLOW_STEP_ORDER if s not in _LEGACY_ONLY_STEPS]
    return list(_WORKFLOW_STEP_ORDER)


def display_step_number(step_const: int, interactive_generation: bool) -> int:
    """Map an internal STEP_* constant to its 1-based position in the active step
    sequence, so displayed step numbers are always contiguous regardless of which
    steps are skipped for the current generation mode."""
    sequence = active_step_sequence(interactive_generation)
    try:
        return sequence.index(step_const) + 1
    except ValueError:
        return step_const

DEFAULT_METADATA: dict = {
    "consultant": "SAP EPM Design Agent",
    "client": "Client",
    "project": "SAP EPM Implementation",
    "engagement_code": "",
}

# ---------------------------------------------------------------------------
# Technology dropdown options
# ---------------------------------------------------------------------------

SAP_TECHNOLOGIES: list = [
    "SAP Analytics Cloud – Analytics",
    "SAP Analytics Cloud – Planning (FP&A)",
    "SAP BW/4HANA",
    "SAP BW on HANA (7.5)",
    "SAP BPC (Standard or Embedded)",
    "SAP Group Reporting",
    "SAP PaPM",
    "SAP Business Data Cloud (BDC)",
    "SAP Embedded Analytics (CDS / Fiori)",
    "SAP ABAP Custom Development",
]

SAP_TECHNOLOGY_DESCRIPTIONS: dict = {
    "SAP Analytics Cloud – Analytics": "Cloud-native analytics platform. Connects live to BW/4HANA, S/4HANA, and HANA Cloud for stories, dashboards, and smart insights.",
    "SAP Analytics Cloud – Planning (FP&A)": "Cloud planning tool supporting driver-based budgeting, rolling forecasts, scenario planning, and allocation processes.",
    "SAP BW/4HANA": "SAP's modern cloud-ready data warehouse on HANA. Uses aDSOs, Calculation Views, ODP extraction, and SAC/AFO for reporting.",
    "SAP BW on HANA (7.5)": "Legacy BW platform on HANA database. InfoCubes, DSOs, CompositeProviders, BEx queries, and AFO reporting.",
    "SAP BPC (Standard or Embedded)": "Planning and consolidation platform. BPC Standard uses its own OLAP engine; BPC Embedded runs on BW-IP with Script Logic and FOX formulas.",
    "SAP Group Reporting": "Legal and management consolidation on S/4HANA. Leverages Universal Journal (ACDOCA), intercompany elimination, and currency translation.",
    "SAP PaPM": "Profitability and Performance Management. Driver-based cost allocation, activity-based costing, and profitability modelling on HANA.",
    "SAP Business Data Cloud (BDC)": "Converged SAP data and analytics platform. Datasphere (data integration, semantic layer) plus SAC for unified enterprise analytics.",
    "SAP Embedded Analytics (CDS / Fiori)": "Real-time reporting directly on S/4HANA using ABAP CDS views, the Virtual Data Model (VDM), and Fiori analytical apps.",
    "SAP ABAP Custom Development": "Custom ABAP objects: BAdI implementations, CDS views, AMDP procedures, BW routines, and enhancement spots.",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    """Initialise all session state keys to None if not already set."""
    for key in _ALL_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None
    if st.session_state[KEY_WORKFLOW_STEP] is None:
        st.session_state[KEY_WORKFLOW_STEP] = STEP_UPLOAD
    if st.session_state[KEY_SUPPORTING_DOCS] is None:
        st.session_state[KEY_SUPPORTING_DOCS] = []
    if st.session_state[KEY_DISCUSSION_NOTES] is None:
        st.session_state[KEY_DISCUSSION_NOTES] = ""
    if st.session_state[KEY_METADATA] is None:
        st.session_state[KEY_METADATA] = dict(DEFAULT_METADATA)
    if st.session_state[KEY_TECHNOLOGIES] is None:
        st.session_state[KEY_TECHNOLOGIES] = []
    if st.session_state[KEY_TECHNOLOGY_AUTO] is None:
        st.session_state[KEY_TECHNOLOGY_AUTO] = False
    for token_key in (KEY_STEP_INPUT_TOKENS, KEY_STEP_OUTPUT_TOKENS, KEY_SESSION_INPUT_TOKENS, KEY_SESSION_OUTPUT_TOKENS):
        if st.session_state[token_key] is None:
            st.session_state[token_key] = 0
    for locked_key in (KEY_FSD_LOCKED_SECTIONS, KEY_TSD_LOCKED_SECTIONS):
        if st.session_state[locked_key] is None:
            st.session_state[locked_key] = {}
    for index_key in (KEY_FSD_CURRENT_SECTION_INDEX, KEY_TSD_CURRENT_SECTION_INDEX, KEY_FSD_REVISION_COUNT, KEY_TSD_REVISION_COUNT):
        if st.session_state[index_key] is None:
            st.session_state[index_key] = 0


def get(key: str):
    """Return the current value of a session state key."""
    return st.session_state.get(key)


def set_value(key: str, value) -> None:
    """Set a session state key to the given value."""
    st.session_state[key] = value


def reset_all() -> None:
    """Reset all session state — returns to step 1."""
    for key in _ALL_KEYS:
        st.session_state[key] = None
    st.session_state[KEY_WORKFLOW_STEP] = STEP_UPLOAD
    st.session_state[KEY_SUPPORTING_DOCS] = []
    st.session_state[KEY_DISCUSSION_NOTES] = ""
    st.session_state[KEY_METADATA] = dict(DEFAULT_METADATA)
    st.session_state[KEY_TECHNOLOGIES] = []
    st.session_state[KEY_TECHNOLOGY_AUTO] = False
    st.session_state[KEY_STEP_INPUT_TOKENS] = 0
    st.session_state[KEY_STEP_OUTPUT_TOKENS] = 0
    st.session_state[KEY_SESSION_INPUT_TOKENS] = 0
    st.session_state[KEY_SESSION_OUTPUT_TOKENS] = 0
    st.session_state[KEY_FSD_LOCKED_SECTIONS] = {}
    st.session_state[KEY_TSD_LOCKED_SECTIONS] = {}
    st.session_state[KEY_FSD_CURRENT_SECTION_INDEX] = 0
    st.session_state[KEY_TSD_CURRENT_SECTION_INDEX] = 0
    st.session_state[KEY_FSD_REVISION_COUNT] = 0
    st.session_state[KEY_TSD_REVISION_COUNT] = 0


def advance_to(step: int) -> None:
    """Advance the workflow to the given step number."""
    st.session_state[KEY_WORKFLOW_STEP] = step


def record_llm_usage(input_tokens: int, output_tokens: int) -> None:
    """Record one LLM call's token usage into the per-step and session-total counters."""
    st.session_state[KEY_STEP_INPUT_TOKENS] = input_tokens
    st.session_state[KEY_STEP_OUTPUT_TOKENS] = output_tokens
    st.session_state[KEY_SESSION_INPUT_TOKENS] = (st.session_state.get(KEY_SESSION_INPUT_TOKENS) or 0) + input_tokens
    st.session_state[KEY_SESSION_OUTPUT_TOKENS] = (st.session_state.get(KEY_SESSION_OUTPUT_TOKENS) or 0) + output_tokens


def compute_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for the given token counts at claude-sonnet-4-6 pricing."""
    return input_tokens * PRICE_PER_INPUT_TOKEN + output_tokens * PRICE_PER_OUTPUT_TOKEN
