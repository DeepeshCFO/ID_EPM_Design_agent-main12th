"""Clarification question generation from the pre-summarised BRD content."""

import json
import logging
import os

from core.llm_client import call_llm
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)


def generate_questions(structured_summary: dict, technology: str, sap_skill: dict, domain_skills: list) -> list:
    """Generate clarification questions from the structured BRD summary.

    Returns a list of question dicts: [{id, question, category, impact}, ...].
    Returns an empty list (never raises) if the LLM response cannot be parsed —
    questions are advisory and the workflow must continue regardless.
    """
    try:
        system_prompt = _render_system_prompt(sap_skill, domain_skills)
        user_prompt = _render_brd_analysis_prompt(structured_summary, technology)
        max_tokens = int(os.getenv("MAX_TOKENS_QUESTIONS", "1500"))

        raw = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
        questions = _parse_questions(raw)
        logger.info("Generated %d clarification questions", len(questions))
        return questions
    except Exception as exc:
        logger.error("Question generation failed: %s", exc)
        return []


def _render_system_prompt(sap_skill: dict, domain_skills: list) -> str:
    """Render the base system prompt with skill context."""
    env = get_jinja_env()
    template = env.get_template("base_system.j2")
    return template.render(
        app_title=os.getenv("APP_TITLE", "SAP EPM Design Agent"),
        sap_skill=sap_skill,
        domain_skills=domain_skills,
    )


def _render_brd_analysis_prompt(structured_summary: dict, technology: str) -> str:
    """Render the BRD analysis prompt for question generation."""
    env = get_jinja_env()
    template = env.get_template("brd_analysis.j2")
    return template.render(structured_summary=structured_summary, technology=technology)


def _parse_questions(raw: str) -> list:
    """Parse the LLM JSON response into a list of question dicts."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [q for q in data if isinstance(q, dict) and "question" in q]
        return []
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse question JSON: %s. Raw: %.200s", exc, raw)
        return []
