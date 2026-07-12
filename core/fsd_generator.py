"""FSD generation orchestration — batched prompt assembly and LLM calls.

Document assembly itself lives entirely in core/document_builder.py.
"""

import logging
import os

from core.document_builder import assemble_document, extract_template_structure
from core.llm_client import LLMError, call_llm
from templates.fsd_default_structure import FSD_DEFAULT_SECTIONS
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

# Detailed per-section writing instructions, keyed by the FSD_DEFAULT_SECTIONS section number.
# Sections coming from a user-uploaded template (not in this map) fall back to their own
# `description` field instead.
FSD_SECTION_INSTRUCTIONS: dict = {
    "1": (
        "Generate a table with columns: Item | Detail. Include rows for Document Title, "
        "Version (1.0), Status (Draft), Author (use the metadata consultant name), Date, "
        "Client, Project, SAP Technology. Follow with a Revision History table "
        "(Version | Date | Author | Description of Change) with one placeholder row."
    ),
    "2": (
        "3–4 paragraphs. Business context, project goals, solution approach, and expected "
        "business outcomes. No bullet points — structured prose only."
    ),
    "3": (
        "A table with columns: Req # | Requirement | Source (BRD / Assumed) | Priority "
        "(High/Med/Low) | Status (Open/Confirmed). List every requirement from the "
        "structured requirements summary above."
    ),
    "4": (
        "Identify the primary functional domain(s). Describe relevant KPIs, business "
        "processes, and reporting needs in context, using the domain knowledge available to you."
    ),
    "5": (
        "A text-block architecture diagram using ASCII or Unicode box-drawing characters "
        "showing end-to-end data flow, followed by a narrative description of each layer and "
        "integration point. This section MUST include an architecture diagram — never omit it."
    ),
    "6": (
        "A report catalogue table with columns: Report Name | Report Type | Primary Users | "
        "Data Source | Refresh Frequency | Key Measures | Key Dimensions / Filters. Include "
        "every report and KPI mentioned or implied in the requirements summary."
    ),
    "7": (
        "If the requirements cover planning/budgeting/forecasting, describe the planning "
        "model: versions, planning horizon, planning cycle, driver-based logic, allocation "
        "rules, and workflow. If planning is not in scope, state: \"Planning is not in scope "
        "for this implementation.\""
    ),
    "8": (
        "Table with columns: Data Entity | Entity Type (Master/Transaction) | Source System | "
        "Update Frequency | Key Fields | Data Governance Owner. Include every data source and "
        "key entity from the requirements summary."
    ),
    "9": (
        "Functional role matrix table: Role Name | Description | Data Access Scope | "
        "Permitted Actions | Relevant Report/Planning Access."
    ),
    "10": (
        "Table: Integration Point | Source System | Target System | Data Objects | "
        "Transfer Method | Frequency | Responsible Team."
    ),
    "11": (
        "Table: Assumption # | Assumption | Impact if Wrong | Date. Every assumption made "
        "where the input was silent or a clarification question was skipped must appear here."
    ),
    "12": (
        "Table: OQ # | Question | Raised By | Priority (H/M/L) | Impact | Target Resolution "
        "Date. Include any of the open gaps identified during pre-summarisation that remain "
        "unresolved."
    ),
    "13": (
        "Table: AC # | Requirement Reference | Acceptance Criterion | Test Type | Pass "
        "Criteria. Write testable criteria for every requirement in the Business Requirements "
        "Summary section."
    ),
    "14": (
        "Table: Term | Definition. Include every SAP acronym and domain-specific term used "
        "anywhere in this document."
    ),
}


def resolve_section_structure(template_bytes: bytes | None) -> list:
    """Return the FSD section structure from an uploaded template or the default schema."""
    if template_bytes:
        extracted = extract_template_structure(template_bytes)
        if extracted:
            logger.info("Using uploaded FSD template structure (%d sections)", len(extracted))
            return extracted
        logger.warning("Template structure extraction yielded no sections — using default")
    return FSD_DEFAULT_SECTIONS


def split_into_batches(section_structure: list) -> list:
    """Group sections into adaptively-sized batches based on SECTION_WEIGHT (CLAUDE.md §3.7).

    Heavy sections are flushed solo, medium sections in pairs, light sections in
    groups of up to three. A run flushes early if the next section has a different
    weight, so batches never mix weight classes — that keeps each batch's token
    budget (see generate_fsd_batch) matched to what it actually contains.
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


def generate_fsd_batch(
    structured_summary: dict,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    batch_sections: list,
) -> str:
    """Generate the raw LLM response text for ONE batch of FSD sections.

    Never raises LLMError: if the whole-batch call fails after retries, it falls
    back to generating each section individually, and a section that still fails
    becomes a placeholder — one bad batch must never discard the rest of the
    document (CLAUDE.md §3.7 / NFR-08).
    """
    system_prompt = _render_system_prompt(sap_skill, domain_skills)
    section_numbers = [s["number"] for s in batch_sections]
    weight = SECTION_WEIGHT.get(section_numbers[0], _DEFAULT_WEIGHT) if section_numbers else _DEFAULT_WEIGHT
    max_tokens = _BATCH_MAX_TOKENS[weight]
    logger.info("FSD batch: sections=%s weight=%s max_tokens=%d", section_numbers, weight, max_tokens)

    user_prompt = _render_batch_prompt(
        structured_summary, technology, clarification_answers, metadata, section_structure, batch_sections,
    )
    try:
        return call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
    except LLMError as exc:
        logger.warning(
            "FSD batch (sections=%s) failed after retries: %s — falling back to per-section calls.",
            section_numbers, exc,
        )
        return _generate_fsd_sections_individually(
            structured_summary, technology, clarification_answers, metadata,
            section_structure, batch_sections, system_prompt,
        )


def _generate_fsd_sections_individually(
    structured_summary: dict,
    technology: str,
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
            structured_summary, technology, clarification_answers, metadata, section_structure, [section],
        )
        try:
            content = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=_FALLBACK_MAX_TOKENS)
        except LLMError as exc:
            logger.warning(
                "FSD section %s failed individually after retries: %s — inserting placeholder.",
                section["number"], exc,
            )
            content = (
                f"## SECTION_{section['number']}:\n"
                f"Section {section['number']} could not be generated. "
                "Please use the Regenerate Section button to retry."
            )
        rendered_parts.append(content)
    return "\n\n".join(rendered_parts)


def build_fsd_bytes(section_content_dict: dict, section_structure: list, technology: str, metadata: dict) -> bytes:
    """Assemble the final FSD .docx from the accumulated section content dict."""
    return assemble_document(
        section_content_dict, section_structure, doc_type="FSD", technology=technology, metadata=metadata,
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
    structured_summary: dict,
    technology: str,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    batch_sections: list,
) -> str:
    """Render the FSD batch generation prompt."""
    env = get_jinja_env()
    template = env.get_template("fsd_generation_batch.j2")
    return template.render(
        structured_summary=structured_summary,
        technology=technology,
        clarification_answers=clarification_answers or {},
        metadata=metadata,
        all_section_titles=[f"{s['number']}. {s['title']}" for s in section_structure],
        batch_sections=batch_sections,
        section_instructions=FSD_SECTION_INSTRUCTIONS,
    )
