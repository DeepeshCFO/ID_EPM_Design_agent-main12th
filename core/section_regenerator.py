"""Single-section regeneration for an already-generated FSD or TSD (FR-12 / FR-17)."""

import logging
import os

from core.fsd_generator import SECTION_WEIGHT as FSD_SECTION_WEIGHT
from core.llm_client import call_llm
from core.tsd_generator import SECTION_WEIGHT as TSD_SECTION_WEIGHT
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)

_DEFAULT_WEIGHT = "medium"
_TOKENS_BY_WEIGHT = {"heavy": 6000, "medium": 5000, "light": 3000}


def _resolve_max_tokens(doc_type: str, section_number: str) -> tuple:
    """Pick a token budget matching the section's relative size (same weights as batch generation)."""
    weight_map = FSD_SECTION_WEIGHT if doc_type == "FSD" else TSD_SECTION_WEIGHT
    weight = weight_map.get(section_number, _DEFAULT_WEIGHT)
    return weight, _TOKENS_BY_WEIGHT[weight]


def regenerate_section(
    doc_type: str,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    structured_summary: dict,
    clarification_answers: dict,
    existing_section_titles: list,
    target_section: dict,
    instructions: str,
    fsd_full_text: str | None = None,
) -> str:
    """Regenerate the body content for ONE section. Returns the new section content string.

    Raises LLMError (from core.llm_client) on failure — the caller keeps the existing
    section content unchanged until a regeneration succeeds.
    """
    system_prompt = _render_system_prompt(sap_skill, domain_skills)
    user_prompt = _render_regeneration_prompt(
        doc_type, technology, structured_summary, clarification_answers,
        existing_section_titles, target_section, instructions, fsd_full_text,
    )
    weight, max_tokens = _resolve_max_tokens(doc_type, target_section["number"])
    logger.info(
        "Regenerating %s section %s (weight=%s, max_tokens=%d)",
        doc_type, target_section["number"], weight, max_tokens,
    )
    content = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
    return content.strip()


def _render_system_prompt(sap_skill: dict, domain_skills: list) -> str:
    """Render the base system prompt."""
    env = get_jinja_env()
    template = env.get_template("base_system.j2")
    return template.render(
        app_title=os.getenv("APP_TITLE", "SAP EPM Design Agent"),
        sap_skill=sap_skill,
        domain_skills=domain_skills,
    )


def _render_regeneration_prompt(
    doc_type: str,
    technology: str,
    structured_summary: dict,
    clarification_answers: dict,
    existing_section_titles: list,
    target_section: dict,
    instructions: str,
    fsd_full_text: str | None,
) -> str:
    """Render the single-section regeneration prompt."""
    env = get_jinja_env()
    template = env.get_template("section_regeneration.j2")
    return template.render(
        doc_type=doc_type,
        technology=technology,
        structured_summary=structured_summary,
        clarification_answers=clarification_answers or {},
        existing_section_titles=existing_section_titles,
        target_section=target_section,
        instructions=instructions,
        fsd_full_text=fsd_full_text,
    )
