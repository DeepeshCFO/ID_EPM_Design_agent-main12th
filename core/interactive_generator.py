"""Interactive, section-by-section generate -> review -> refine -> lock loop.

Owns the single-section generation contract described in CLAUDE.md §3.7/§3.8a and
FSD FR-09/FR-10/FR-15: exactly one section is generated per LLM call, and each call
carries forward every previously locked section's content and Q&A as context. No
Streamlit imports here — this module is pure orchestration (CLAUDE.md §3.1).
"""

import logging
import os

from core.fsd_generator import SECTION_WEIGHT as FSD_SECTION_WEIGHT
from core.llm_client import call_llm
from core.tsd_generator import SECTION_WEIGHT as TSD_SECTION_WEIGHT
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_WEIGHT = "medium"
_TOKENS_BY_WEIGHT = {"heavy": 6000, "medium": 5000, "light": 3000}

_CONTENT_MARKER = "## SECTION_CONTENT:"
_QUESTION_MARKER = "## SECTION_QUESTION:"
_NO_QUESTION = "NONE"


def get_max_regeneration_attempts() -> int:
    """Read MAX_SECTION_REGENERATION_ATTEMPTS from the environment (default 5)."""
    try:
        return int(os.getenv("MAX_SECTION_REGENERATION_ATTEMPTS", str(_DEFAULT_MAX_ATTEMPTS)))
    except ValueError:
        return _DEFAULT_MAX_ATTEMPTS


def should_force_lock(revision_count: int) -> bool:
    """True once `revision_count` completed regenerations already reached the cap.

    When true, the next correction must force-lock the latest draft instead of
    triggering another LLM call (FR-10: "if exceeded, the section is force-locked
    using the latest draft").
    """
    return revision_count >= get_max_regeneration_attempts()


def generate_section_draft(
    doc_type: str,
    structured_summary: dict,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    locked_sections: dict,
    target_section: dict,
    instructions: str,
    fsd_full_text: str | None = None,
) -> dict:
    """Generate the FIRST draft of exactly one section. Returns {"content", "question"}."""
    return _generate(
        doc_type, structured_summary, technology, sap_skill, domain_skills,
        clarification_answers, metadata, section_structure, locked_sections,
        target_section, instructions, fsd_full_text, feedback=None,
    )


def apply_feedback_and_regenerate(
    doc_type: str,
    structured_summary: dict,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    clarification_answers: dict,
    metadata: dict,
    section_structure: list,
    locked_sections: dict,
    target_section: dict,
    instructions: str,
    previous_draft: dict,
    feedback_text: str,
    fsd_full_text: str | None = None,
) -> dict:
    """Regenerate the current section's draft, incorporating the user's correction text."""
    feedback = {"previous_content": previous_draft.get("content", ""), "feedback_text": feedback_text}
    return _generate(
        doc_type, structured_summary, technology, sap_skill, domain_skills,
        clarification_answers, metadata, section_structure, locked_sections,
        target_section, instructions, fsd_full_text, feedback=feedback,
    )


def lock_section(
    locked_sections: dict,
    section_number: str,
    draft: dict,
    answer_text: str | None,
    revision_count: int,
    force_locked: bool = False,
) -> dict:
    """Store one section's final content + Q&A into locked_sections. Returns a new dict."""
    updated = dict(locked_sections)
    updated[section_number] = {
        "content": draft.get("content", ""),
        "question": draft.get("question"),
        "answer": answer_text or "",
        "revision_count": revision_count,
        "force_locked": force_locked,
    }
    return updated


def append_open_questions_addendum(locked_sections: dict, section_structure: list) -> dict:
    """Flag every force-locked section in the Open Questions Register (or nearest
    equivalent) section's locked content. Safe to call once, after the final section
    locks. Returns a new locked_sections dict — never mutates the input (FR-10)."""
    forced = [(num, entry) for num, entry in locked_sections.items() if entry.get("force_locked")]
    if not forced:
        return locked_sections

    target_number = _find_addendum_target(section_structure, locked_sections)
    if target_number is None:
        logger.warning(
            "No Open Questions Register or Assumptions section found to flag %d force-locked section(s)",
            len(forced),
        )
        return locked_sections

    title_by_number = {s["number"]: s["title"] for s in section_structure}
    lines = ["", "**Sections Locked After Maximum Revisions — Recommend Manual Review:**"]
    for num, _entry in sorted(forced, key=_section_sort_key_from_pair):
        lines.append(f"- Section {num} ({title_by_number.get(num, 'Unknown')})")

    updated = dict(locked_sections)
    target_entry = dict(updated[target_number])
    target_entry["content"] = target_entry.get("content", "") + "\n" + "\n".join(lines)
    updated[target_number] = target_entry
    return updated


def _find_addendum_target(section_structure: list, locked_sections: dict) -> str | None:
    """Locate a locked section whose title matches the Open Questions Register, falling
    back to an Assumptions-style section (used by both FSD and TSD default structures)."""
    for keyword in ("open question", "assumption"):
        for section in section_structure:
            if keyword in section["title"].lower() and section["number"] in locked_sections:
                return section["number"]
    return None


def _resolve_max_tokens(doc_type: str, section_number: str) -> int:
    """Pick a token budget matching the section's relative size (same weights used
    for batch generation and single-section regeneration)."""
    weight_map = FSD_SECTION_WEIGHT if doc_type == "FSD" else TSD_SECTION_WEIGHT
    weight = weight_map.get(section_number, _DEFAULT_WEIGHT)
    return _TOKENS_BY_WEIGHT[weight]


def _generate(
    doc_type, structured_summary, technology, sap_skill, domain_skills,
    clarification_answers, metadata, section_structure, locked_sections,
    target_section, instructions, fsd_full_text, feedback,
) -> dict:
    """Render the interactive prompt, call the LLM once, and parse the section draft."""
    system_prompt = _render_system_prompt(sap_skill, domain_skills)
    user_prompt = _render_interactive_prompt(
        doc_type, structured_summary, technology, clarification_answers, metadata,
        section_structure, locked_sections, target_section, instructions, fsd_full_text, feedback,
    )
    max_tokens = _resolve_max_tokens(doc_type, target_section["number"])
    logger.info(
        "%s interactive generation: section=%s feedback=%s max_tokens=%d",
        doc_type, target_section["number"], bool(feedback), max_tokens,
    )
    raw = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
    return _parse_draft(raw)


def _render_system_prompt(sap_skill: dict, domain_skills: list) -> str:
    """Render the base system prompt."""
    env = get_jinja_env()
    template = env.get_template("base_system.j2")
    return template.render(
        app_title=os.getenv("APP_TITLE", "SAP EPM Design Agent"),
        sap_skill=sap_skill,
        domain_skills=domain_skills,
    )


def _render_interactive_prompt(
    doc_type, structured_summary, technology, clarification_answers, metadata,
    section_structure, locked_sections, target_section, instructions, fsd_full_text, feedback,
) -> str:
    """Render the single-section interactive generation prompt."""
    env = get_jinja_env()
    template = env.get_template("section_generation_interactive.j2")
    titles_by_number = {s["number"]: s["title"] for s in section_structure}
    locked_context = [
        {
            "number": num,
            "title": titles_by_number.get(num, num),
            "content": entry["content"],
            "question": entry.get("question"),
            "answer": entry.get("answer"),
        }
        for num, entry in sorted(locked_sections.items(), key=_section_sort_key_from_pair)
    ]
    return template.render(
        doc_type=doc_type,
        structured_summary=structured_summary,
        technology=technology,
        clarification_answers=clarification_answers or {},
        metadata=metadata,
        all_section_titles=[f"{s['number']}. {s['title']}" for s in section_structure],
        locked_sections=locked_context,
        target_section=target_section,
        instructions=instructions,
        fsd_full_text=fsd_full_text,
        feedback=feedback,
    )


def _section_sort_key_from_pair(item):
    number = item[0]
    try:
        return (0, int(number))
    except ValueError:
        return (1, number)


def _parse_draft(raw: str) -> dict:
    """Parse the LLM response into {"content": str, "question": str|None}.

    Falls back to treating the whole response as content (no question) if the
    model did not follow the required marker format.
    """
    text = raw.strip()
    c_idx = text.find(_CONTENT_MARKER)
    q_idx = text.find(_QUESTION_MARKER)

    if c_idx == -1 and q_idx == -1:
        return {"content": text, "question": None}

    if c_idx != -1 and q_idx != -1 and q_idx > c_idx:
        content = text[c_idx + len(_CONTENT_MARKER):q_idx].strip()
        question = _clean_question(text[q_idx + len(_QUESTION_MARKER):])
    elif c_idx != -1:
        content = text[c_idx + len(_CONTENT_MARKER):].strip()
        question = None
    else:
        content = text[:q_idx].strip()
        question = _clean_question(text[q_idx + len(_QUESTION_MARKER):])

    return {"content": content, "question": question}


def _clean_question(raw_question: str) -> str | None:
    """Return the stripped question text, or None if the model signalled no question."""
    question = raw_question.strip()
    if not question or question.upper() == _NO_QUESTION:
        return None
    return question
