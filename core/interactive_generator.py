"""Interactive, section-by-section generate -> review -> refine -> lock loop.

Owns the single-section generation contract described in CLAUDE.md §3.7/§3.8a and
FSD FR-09/FR-10/FR-15: exactly one section is generated per LLM call, and each call
carries forward every previously locked section's content, pre-generation Q&A, and
correction history as context. No Streamlit imports here — this module is pure
orchestration (CLAUDE.md §3.1).

Per-section sequence (CLAUDE.md §3.7):
  (a) generate_section_questions()   — up to 5-6 questions, BEFORE any content exists
  (b) [UI renders the batch question form]
  (c) stream_section_draft() / stream_feedback_regeneration() — content only, streamed
  (d) [UI renders a pure "does this look right?" correction loop — no new questions]
  (e) lock_section() — stores content + pre_generation_questions + pre_generation_answers
      + correction_history, kept as separate fields
"""

import json
import logging
import os

from core.fsd_generator import SECTION_WEIGHT as FSD_SECTION_WEIGHT
from core.llm_client import call_llm, stream_llm
from core.tsd_generator import SECTION_WEIGHT as TSD_SECTION_WEIGHT
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_WEIGHT = "medium"
_TOKENS_BY_WEIGHT = {"heavy": 6000, "medium": 5000, "light": 3000}
_MAX_PRE_GENERATION_QUESTIONS = 6


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


# ---------------------------------------------------------------------------
# (a) Pre-generation question phase — runs BEFORE any content for the section exists
# ---------------------------------------------------------------------------

def generate_section_questions(
    section_spec: dict,
    structured_summary: dict,
    technology_context: dict,
    locked_sections: dict,
    doc_type: str = "FSD",
) -> list:
    """Return up to 6 targeted pre-generation questions for one section (step a).

    `technology_context` bundles {"technology", "sap_skill", "domain_skills"}.
    Returns an empty list if the agent judges the section unambiguous given the
    structured summary and prior locked sections — never raises, since a failure
    here must not block the section from being generated (mirrors the fail-open
    behaviour of core/question_engine.py).
    """
    try:
        system_prompt = _render_system_prompt(
            technology_context.get("sap_skill"), technology_context.get("domain_skills"),
        )
        user_prompt = _render_section_questions_prompt(
            section_spec, structured_summary, technology_context, locked_sections, doc_type,
        )
        max_tokens = int(os.getenv("MAX_TOKENS_QUESTIONS", "1500"))
        raw = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)
        questions = _parse_section_questions(raw)
        logger.info(
            "Section %s: generated %d pre-generation question(s)",
            section_spec.get("number"), len(questions),
        )
        return questions
    except Exception as exc:
        logger.error("Pre-generation question generation failed for section %s: %s", section_spec.get("number"), exc)
        return []


def _render_section_questions_prompt(
    section_spec: dict, structured_summary: dict, technology_context: dict, locked_sections: dict, doc_type: str,
) -> str:
    """Render the pre-generation question prompt for one section."""
    env = get_jinja_env()
    template = env.get_template("section_questions_pregeneration.j2")
    return template.render(
        doc_type=doc_type,
        section_spec=section_spec,
        structured_summary=structured_summary,
        technology=technology_context.get("technology"),
        locked_sections=_locked_context_list(locked_sections, titles_by_number={}),
        max_questions=_MAX_PRE_GENERATION_QUESTIONS,
    )


def _parse_section_questions(raw: str) -> list:
    """Parse the LLM JSON response into a list of up to 6 question strings.

    Accepts either a JSON array of strings or of {"question": ...} objects, and
    tolerates markdown code fences. Falls back to an empty list on any parse
    failure — questions are advisory, never a hard requirement.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse pre-generation question JSON: %s. Raw: %.200s", exc, text)
        return []

    if not isinstance(data, list):
        return []

    questions = []
    for item in data:
        if isinstance(item, str) and item.strip():
            questions.append(item.strip())
        elif isinstance(item, dict) and item.get("question"):
            questions.append(str(item["question"]).strip())
    return questions[:_MAX_PRE_GENERATION_QUESTIONS]


# ---------------------------------------------------------------------------
# (c) Content generation — streamed, no questions surfaced here
# ---------------------------------------------------------------------------

def stream_section_draft(
    doc_type: str,
    structured_summary: dict,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    pre_generation_answers: dict,
    metadata: dict,
    section_structure: list,
    locked_sections: dict,
    target_section: dict,
    instructions: str,
    fsd_full_text: str | None = None,
):
    """Stream the FIRST draft of exactly one section. Yields text chunks.

    `pre_generation_answers` is THIS section's {question_text: answer_text} map
    from step (b) — the only clarification input used for this call.
    """
    system_prompt, user_prompt, max_tokens = _build_prompts(
        doc_type, structured_summary, technology, sap_skill, domain_skills,
        pre_generation_answers, metadata, section_structure, locked_sections,
        target_section, instructions, fsd_full_text, feedback=None,
    )
    yield from stream_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)


def stream_feedback_regeneration(
    doc_type: str,
    structured_summary: dict,
    technology: str,
    sap_skill: dict,
    domain_skills: list,
    pre_generation_answers: dict,
    metadata: dict,
    section_structure: list,
    locked_sections: dict,
    target_section: dict,
    instructions: str,
    previous_content: str,
    feedback_text: str,
    fsd_full_text: str | None = None,
):
    """Stream a regenerated draft (step d), reusing the SAME pre-generation answers
    from step (b) plus the user's correction text. Yields text chunks."""
    feedback = {"previous_content": previous_content, "feedback_text": feedback_text}
    system_prompt, user_prompt, max_tokens = _build_prompts(
        doc_type, structured_summary, technology, sap_skill, domain_skills,
        pre_generation_answers, metadata, section_structure, locked_sections,
        target_section, instructions, fsd_full_text, feedback=feedback,
    )
    yield from stream_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens)


def _build_prompts(
    doc_type, structured_summary, technology, sap_skill, domain_skills,
    pre_generation_answers, metadata, section_structure, locked_sections,
    target_section, instructions, fsd_full_text, feedback,
) -> tuple:
    """Render the system + user prompt and resolve the token budget for one
    content-generation call (first draft or feedback regeneration)."""
    system_prompt = _render_system_prompt(sap_skill, domain_skills)
    user_prompt = _render_interactive_prompt(
        doc_type, structured_summary, technology, pre_generation_answers, metadata,
        section_structure, locked_sections, target_section, instructions, fsd_full_text, feedback,
    )
    max_tokens = _resolve_max_tokens(doc_type, target_section["number"])
    logger.info(
        "%s interactive generation: section=%s feedback=%s max_tokens=%d",
        doc_type, target_section["number"], bool(feedback), max_tokens,
    )
    return system_prompt, user_prompt, max_tokens


# ---------------------------------------------------------------------------
# (e) Locking
# ---------------------------------------------------------------------------

def lock_section(
    locked_sections: dict,
    section_number: str,
    draft: dict,
    pre_generation_questions: list,
    pre_generation_answers: dict,
    correction_history: list,
    revision_count: int,
    force_locked: bool = False,
) -> dict:
    """Store one section's final content into locked_sections. Returns a new dict.

    pre_generation_answers (step b) and correction_history (step d) are stored as
    separate fields — they serve different purposes in later sections' prompt
    context and must never be collapsed into one (CLAUDE.md §3.8a).
    """
    updated = dict(locked_sections)
    updated[section_number] = {
        "content": draft.get("content", ""),
        "pre_generation_questions": list(pre_generation_questions or []),
        "pre_generation_answers": dict(pre_generation_answers or {}),
        "correction_history": list(correction_history or []),
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


# ---------------------------------------------------------------------------
# Skip Review / fast-mode hand-off (point 4) — pure context-building helper.
# The batch generation loop itself lives in fsd_generator.py/tsd_generator.py
# (SECTION_WEIGHT/split_into_batches/generate_*_batch) and app.py; this only
# renders already-locked content into plain text so continuity isn't lost.
# ---------------------------------------------------------------------------

def build_locked_context_text(locked_sections: dict, section_structure: list) -> str:
    """Render already-locked sections' final content as plain text context, so the
    Skip Review fast-mode hand-off to the legacy batch generator stays continuous
    with what the user already approved. Returns "" if nothing is locked yet."""
    if not locked_sections:
        return ""
    titles_by_number = {s["number"]: s["title"] for s in section_structure}
    parts = []
    for num, entry in sorted(locked_sections.items(), key=_section_sort_key_from_pair):
        title = titles_by_number.get(num, num)
        parts.append(f"### Section {num}: {title} (locked)\n{entry.get('content', '')}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Shared prompt-rendering helpers
# ---------------------------------------------------------------------------

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
    doc_type, structured_summary, technology, pre_generation_answers, metadata,
    section_structure, locked_sections, target_section, instructions, fsd_full_text, feedback,
) -> str:
    """Render the single-section interactive content-generation prompt."""
    env = get_jinja_env()
    template = env.get_template("section_generation_interactive.j2")
    titles_by_number = {s["number"]: s["title"] for s in section_structure}
    return template.render(
        doc_type=doc_type,
        structured_summary=structured_summary,
        technology=technology,
        pre_generation_answers=pre_generation_answers or {},
        metadata=metadata,
        all_section_titles=[f"{s['number']}. {s['title']}" for s in section_structure],
        locked_sections=_locked_context_list(locked_sections, titles_by_number),
        target_section=target_section,
        instructions=instructions,
        fsd_full_text=fsd_full_text,
        feedback=feedback,
    )


def _locked_context_list(locked_sections: dict, titles_by_number: dict) -> list:
    """Turn the locked_sections dict into an ordered list for template rendering,
    carrying pre_generation_questions/answers and correction_history separately
    (CLAUDE.md §3.8a) so later sections' prompts have full context on both."""
    return [
        {
            "number": num,
            "title": titles_by_number.get(num, num),
            "content": entry["content"],
            "pre_generation_questions": entry.get("pre_generation_questions", []),
            "pre_generation_answers": entry.get("pre_generation_answers", {}),
            "correction_history": entry.get("correction_history", []),
        }
        for num, entry in sorted(locked_sections.items(), key=_section_sort_key_from_pair)
    ]


def _section_sort_key_from_pair(item):
    number = item[0]
    try:
        return (0, int(number))
    except ValueError:
        return (1, number)


def _resolve_max_tokens(doc_type: str, section_number: str) -> int:
    """Pick a token budget matching the section's relative size (same weights used
    for batch generation and single-section regeneration)."""
    weight_map = FSD_SECTION_WEIGHT if doc_type == "FSD" else TSD_SECTION_WEIGHT
    weight = weight_map.get(section_number, _DEFAULT_WEIGHT)
    return _TOKENS_BY_WEIGHT[weight]
