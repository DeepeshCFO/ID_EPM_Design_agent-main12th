"""TSD generation orchestration — batched prompt assembly and LLM calls.

Document assembly itself lives entirely in core/document_builder.py.
"""

import logging
import os

from core.document_builder import assemble_document, extract_template_structure
from core.llm_client import LLMError, call_llm
from templates.tsd_default_structure import TSD_DEFAULT_SECTIONS
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)

# Relative size of each section, used for adaptive batch sizing (CLAUDE.md §3.7).
# Heavy sections always get a dedicated API call; medium sections are paired;
# light sections are grouped up to three per call. Sections from an uploaded
# template that aren't in this map (renumbered/custom structure) fall back to
# "medium" — a safe middle-ground batch size and token budget.
SECTION_WEIGHT: dict = {
    "1": "light", "2": "medium", "3": "heavy", "4": "heavy", "5": "heavy",
    "6": "heavy", "7": "heavy", "8": "heavy", "9": "medium", "10": "medium",
    "11": "light", "12": "medium", "13": "medium", "14": "light",
}
_DEFAULT_WEIGHT = "medium"
_BATCH_QUOTA = {"heavy": 1, "medium": 2, "light": 3}
_BATCH_MAX_TOKENS = {"heavy": 6000, "medium": 5000, "light": 3000}
_FALLBACK_MAX_TOKENS = 4000

# Detailed per-section writing instructions, keyed by the TSD_DEFAULT_SECTIONS section number.
# Sections coming from a user-uploaded template (not in this map) fall back to their own
# `description` field instead.
TSD_SECTION_INSTRUCTIONS: dict = {
    "1": (
        "Table with: Document Title, Version (1.0), Status (Draft), Author (use the "
        "metadata consultant name), Date, Client, Project, SAP Technology, SAP System "
        "Version (from clarification or assumed). Include a Revision History table."
    ),
    "2": (
        "Component diagram (ASCII/Unicode), deployment model description, technology stack "
        "table (Component | Technology | Version | Notes), and system landscape (DEV / QA / PROD)."
    ),
    "3": (
        "For BW/4HANA: InfoObject design table (Object Name | Object Type | Description | "
        "Data Type | Length). For SAC/Datasphere: dimension and measure design. For S/4HANA "
        "Embedded: CDS view layer design. Include an entity-relationship description."
    ),
    "4": (
        "Field mapping table: Source Object | Source Field | Source Type | Target Object | "
        "Target Field | Target Type | Transformation Logic | Delta Strategy. Cover all data "
        "flows implied by the FSD. Include the error handling approach."
    ),
    "5": (
        "Table: Object Name | Object Type | Description | Key Figures | Characteristics | "
        "Variables / Filters | Consumer (AFO/SAC/Fiori). One row per query/story/report from "
        "the FSD's reporting catalogue."
    ),
    "6": (
        "If planning is in scope per the FSD: aggregation level design, planning function "
        "specifications (name | type | logic description), planning sequences, data slice "
        "definitions, version management approach. If not in scope, state explicitly."
    ),
    "7": (
        "Complete object list table: Object Name | Object Type | Description | Status "
        "(New / Modify / Reuse) | Transport Priority. Include ALL objects to be created or modified."
    ),
    "8": (
        "For each custom development item: Object Name | Development Type | Purpose | "
        "Called By | Technical Description | Estimated Complexity (S/M/L). If no custom ABAP "
        "is required, state explicitly."
    ),
    "9": (
        "Table: Area | Recommendation | Rationale | Threshold. Include partitioning strategy, "
        "aggregation/index recommendations, expected data volumes, query performance SLAs, "
        "and load window constraints."
    ),
    "10": (
        "Table: Role Name | Auth Objects | Field Values | Data Restrictions. Include analysis "
        "authorisations, BW authorisation variables, or HANA privileges as appropriate for "
        "the technology."
    ),
    "11": (
        "Table: Interface ID | Source System | Target System | Protocol/Method | Object/API | "
        "Field Mapping Reference | Frequency | Error Handling. One row per integration point."
    ),
    "12": (
        "Table: TC # | Object Reference | Test Scenario | Test Steps (summary) | Expected "
        "Result | Test Type (Unit/Integration/UAT). One scenario per major object."
    ),
    "13": (
        "Table: Object Type | Naming Pattern | Example | Notes. Cover all SAP object types "
        "in scope (InfoObjects, DataSources, Queries, CDS views, ABAP classes, etc.)."
    ),
    "14": (
        "Table: Assumption # | Assumption | Category (Environment/Version/Performance/Data) | "
        "Impact if Wrong. Every technical assumption must be documented here."
    ),
}


def resolve_section_structure(template_bytes: bytes | None) -> list:
    """Return the TSD section structure from an uploaded template or the default schema."""
    if template_bytes:
        extracted = extract_template_structure(template_bytes)
        if extracted:
            logger.info("Using uploaded TSD template structure (%d sections)", len(extracted))
            return extracted
        logger.warning("Template structure extraction yielded no sections — using default")
    return TSD_DEFAULT_SECTIONS


def split_into_batches(section_structure: list) -> list:
    """Group sections into adaptively-sized batches based on SECTION_WEIGHT (CLAUDE.md §3.7).

    Heavy sections are flushed solo, medium sections in pairs, light sections in
    groups of up to three. A run flushes early if the next section has a different
    weight, so batches never mix weight classes — that keeps each batch's token
    budget (see generate_tsd_batch) matched to what it actually contains.
    """
    batches: list = []
    current: list = []
    current_weight: str | None = None

    for section in section_structure:
        weight = SECTION_WEIGHT.get(section["number"], _DEFAULT_WEIGHT)
        if current and (weight != current_weight or len(current) >= _BATCH_QUOTA[current_weight]):
            batches.append(current)
            current = []
        current.append(section)
        current_weight = weight
        if len(current) >= _BATCH_QUOTA[current_weight]:
            batches.append(current)
            current = []
            current_weight = None

    if current:
        batches.append(current)

    return batches


def generate_tsd_batch(
    fsd_full_text: str,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    structured_summary: dict,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    batch_sections: list,
) -> str:
    """Generate the raw LLM response text for ONE batch of TSD sections.

    Never raises LLMError: if the whole-batch call fails after retries, it falls
    back to generating each section individually, and a section that still fails
    becomes a placeholder — one bad batch must never discard the rest of the
    document (CLAUDE.md §3.7 / NFR-08).
    """
    system_prompt = _render_system_prompt(sap_skill, domain_skills)
    section_numbers = [s["number"] for s in batch_sections]
    weight = SECTION_WEIGHT.get(section_numbers[0], _DEFAULT_WEIGHT) if section_numbers else _DEFAULT_WEIGHT
    max_tokens = _BATCH_MAX_TOKENS[weight]
    logger.info("TSD batch: sections=%s weight=%s max_tokens=%d", section_numbers, weight, max_tokens)

    user_prompt = _render_batch_prompt(
        fsd_full_text, technology, structured_summary, clarification_answers,
        metadata, section_structure, batch_sections,
    )
    try:
        return call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
    except LLMError as exc:
        logger.warning(
            "TSD batch (sections=%s) failed after retries: %s — falling back to per-section calls.",
            section_numbers, exc,
        )
        return _generate_tsd_sections_individually(
            fsd_full_text, technology, structured_summary, clarification_answers,
            metadata, section_structure, batch_sections, system_prompt,
        )


def _generate_tsd_sections_individually(
    fsd_full_text: str,
    technology: str,
    structured_summary: dict,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    batch_sections: list,
    system_prompt: str,
) -> str:
    """Fallback for a failed batch: generate each section on its own, one call at a time.

    A section that also fails after its own retries gets a placeholder instead of
    aborting the batch — the user can retry it later via Regenerate Section.
    """
    rendered_parts = []
    for section in batch_sections:
        user_prompt = _render_batch_prompt(
            fsd_full_text, technology, structured_summary, clarification_answers,
            metadata, section_structure, [section],
        )
        try:
            content = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=_FALLBACK_MAX_TOKENS)
        except LLMError as exc:
            logger.warning(
                "TSD section %s failed individually after retries: %s — inserting placeholder.",
                section["number"], exc,
            )
            content = (
                f"## SECTION_{section['number']}:\n"
                f"Section {section['number']} could not be generated. "
                "Please use the Regenerate Section button to retry."
            )
        rendered_parts.append(content)
    return "\n\n".join(rendered_parts)


def build_tsd_bytes(section_content_dict: dict, section_structure: list, technology: str, metadata: dict) -> bytes:
    """Assemble the final TSD .docx from the accumulated section content dict."""
    return assemble_document(
        section_content_dict, section_structure, doc_type="TSD", technology=technology, metadata=metadata,
    )


def _render_system_prompt(sap_skill: dict, domain_skills: list) -> str:
    """Render the base system prompt."""
    env = get_jinja_env()
    template = env.get_template("base_system.j2")
    return template.render(
        app_title=os.getenv("APP_TITLE", "SAP EPM Design Agent"),
        sap_skill=sap_skill,
        domain_skills=domain_skills,
    )


def _render_batch_prompt(
    fsd_full_text: str,
    technology: str,
    structured_summary: dict,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    batch_sections: list,
) -> str:
    """Render the TSD batch generation prompt."""
    env = get_jinja_env()
    template = env.get_template("tsd_generation_batch.j2")
    return template.render(
        fsd_full_text=fsd_full_text or "",
        technology=technology,
        structured_summary=structured_summary,
        clarification_answers=clarification_answers or {},
        metadata=metadata,
        all_section_titles=[f"{s['number']}. {s['title']}" for s in section_structure],
        batch_sections=batch_sections,
        section_instructions=TSD_SECTION_INSTRUCTIONS,
    )
