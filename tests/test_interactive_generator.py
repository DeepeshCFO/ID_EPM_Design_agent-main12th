"""Tests for core/interactive_generator.py — the interactive per-section loop
(CLAUDE.md §3.7/§3.8a, FSD FR-09/FR-10/FR-15)."""

from unittest.mock import MagicMock, patch

from core.interactive_generator import (
    append_open_questions_addendum,
    apply_feedback_and_regenerate,
    generate_section_draft,
    get_max_regeneration_attempts,
    lock_section,
    should_force_lock,
)
from templates.fsd_default_structure import FSD_DEFAULT_SECTIONS

SAMPLE_STRUCTURED_SUMMARY = {
    "requirements": ["Daily P&L reporting on BW/4HANA"],
    "kpis": ["Revenue", "EBITDA"],
    "data_sources": ["S/4HANA"],
    "domain": ["finance"],
    "key_entities": ["Legal Entity"],
    "open_gaps": [],
}

SAMPLE_SAP_SKILL = {
    "summary": "SAP BW/4HANA",
    "key_concepts": ["aDSO"],
    "kpis": ["Revenue"],
    "sap_objects": ["InfoObject"],
    "common_patterns": ["Delta extraction"],
}

SAMPLE_DOMAIN_SKILLS = [
    {"domain": "finance", "summary": "Finance", "key_concepts": [], "kpis": [], "sap_objects": [], "common_patterns": []}
]

SAMPLE_METADATA = {"consultant": "Jane Doe", "client": "Acme Corp", "project": "EPM Rollout", "engagement_code": "ENG-001"}

SECTION_1 = FSD_DEFAULT_SECTIONS[0]
SECTION_2 = FSD_DEFAULT_SECTIONS[1]


def _mock_jinja_env(rendered: str = "rendered prompt"):
    mock_template = MagicMock()
    mock_template.render.return_value = rendered
    mock_env = MagicMock()
    mock_env.get_template.return_value = mock_template
    return mock_env


def _draft_response(content: str = "Section content.", question: str = "NONE") -> str:
    return f"## SECTION_CONTENT:\n{content}\n## SECTION_QUESTION:\n{question}"


# ---------------------------------------------------------------------------
# One-section-per-call contract
# ---------------------------------------------------------------------------

class TestOneSectionPerCall:
    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_generate_section_draft_calls_llm_exactly_once(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = _draft_response("Draft for section 1.")

        draft = generate_section_draft(
            doc_type="FSD",
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            clarification_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            locked_sections={},
            target_section=SECTION_1,
            instructions="Write section 1.",
        )

        mock_llm.assert_called_once()
        assert draft == {"content": "Draft for section 1.", "question": None}

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_apply_feedback_and_regenerate_calls_llm_exactly_once(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = _draft_response("Revised draft.", "Should X use Y or Z?")

        draft = apply_feedback_and_regenerate(
            doc_type="FSD",
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            clarification_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            locked_sections={},
            target_section=SECTION_1,
            instructions="Write section 1.",
            previous_draft={"content": "Original draft.", "question": None},
            feedback_text="Use Y instead.",
        )

        mock_llm.assert_called_once()
        assert draft == {"content": "Revised draft.", "question": "Should X use Y or Z?"}

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_prompt_only_mentions_the_single_target_section(self, mock_env, mock_llm):
        """The section's own template render call must be given exactly one target_section."""
        mock_jinja_env = _mock_jinja_env()
        mock_env.return_value = mock_jinja_env
        mock_llm.return_value = _draft_response()

        generate_section_draft(
            doc_type="FSD",
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            clarification_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            locked_sections={},
            target_section=SECTION_2,
            instructions="Write section 2.",
        )

        render_kwargs = mock_jinja_env.get_template.return_value.render.call_args.kwargs
        assert render_kwargs["target_section"] == SECTION_2
        assert isinstance(render_kwargs["target_section"], dict)


# ---------------------------------------------------------------------------
# locked_sections accumulation
# ---------------------------------------------------------------------------

class TestLockedSectionsAccumulation:
    def test_locking_multiple_sections_accumulates_without_losing_earlier_ones(self):
        locked = {}
        locked = lock_section(locked, "1", {"content": "Section 1 body.", "question": None}, "", 0)
        locked = lock_section(locked, "2", {"content": "Section 2 body.", "question": "Q?"}, "my answer", 1)

        assert set(locked.keys()) == {"1", "2"}
        assert locked["1"]["content"] == "Section 1 body."
        assert locked["1"]["revision_count"] == 0
        assert locked["2"]["content"] == "Section 2 body."
        assert locked["2"]["question"] == "Q?"
        assert locked["2"]["answer"] == "my answer"
        assert locked["2"]["revision_count"] == 1

    def test_lock_section_does_not_mutate_the_input_dict(self):
        original = {"1": {"content": "old", "question": None, "answer": "", "revision_count": 0, "force_locked": False}}
        updated = lock_section(original, "2", {"content": "new", "question": None}, "", 0)

        assert "2" not in original
        assert "2" in updated


# ---------------------------------------------------------------------------
# Context carry-forward: later sections' prompts contain earlier locked content
# ---------------------------------------------------------------------------

class TestContextCarryForward:
    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_second_section_prompt_includes_first_locked_section(self, mock_env, mock_llm):
        mock_jinja_env = _mock_jinja_env()
        mock_env.return_value = mock_jinja_env
        mock_llm.return_value = _draft_response()

        locked_sections = lock_section(
            {}, "1", {"content": "Executive summary body.", "question": None}, "looks good", 0,
        )

        generate_section_draft(
            doc_type="FSD",
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            clarification_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            locked_sections=locked_sections,
            target_section=SECTION_2,
            instructions="Write section 2.",
        )

        render_kwargs = mock_jinja_env.get_template.return_value.render.call_args.kwargs
        rendered_locked = render_kwargs["locked_sections"]
        assert len(rendered_locked) == 1
        assert rendered_locked[0]["number"] == "1"
        assert rendered_locked[0]["content"] == "Executive summary body."
        assert rendered_locked[0]["answer"] == "looks good"


# ---------------------------------------------------------------------------
# Regeneration attempt counter and force-lock behaviour
# ---------------------------------------------------------------------------

class TestForceLockBehaviour:
    def test_default_max_attempts_is_5(self, monkeypatch):
        monkeypatch.delenv("MAX_SECTION_REGENERATION_ATTEMPTS", raising=False)
        assert get_max_regeneration_attempts() == 5

    def test_max_attempts_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("MAX_SECTION_REGENERATION_ATTEMPTS", "3")
        assert get_max_regeneration_attempts() == 3

    def test_should_not_force_lock_below_cap(self, monkeypatch):
        monkeypatch.setenv("MAX_SECTION_REGENERATION_ATTEMPTS", "5")
        for revision_count in range(0, 5):
            assert should_force_lock(revision_count) is False

    def test_should_force_lock_once_cap_reached(self, monkeypatch):
        monkeypatch.setenv("MAX_SECTION_REGENERATION_ATTEMPTS", "5")
        assert should_force_lock(5) is True
        assert should_force_lock(6) is True

    def test_force_locked_section_is_flagged_in_locked_sections(self):
        locked = lock_section({}, "4", {"content": "Best-effort draft.", "question": None}, "still not right", 5, force_locked=True)
        assert locked["4"]["force_locked"] is True
        assert locked["4"]["revision_count"] == 5


# ---------------------------------------------------------------------------
# Open Questions Register addendum for force-locked sections
# ---------------------------------------------------------------------------

class TestOpenQuestionsAddendum:
    def test_no_addendum_when_nothing_force_locked(self):
        locked = lock_section({}, "1", {"content": "Body.", "question": None}, "", 0)
        result = append_open_questions_addendum(locked, FSD_DEFAULT_SECTIONS)
        assert result == locked

    def test_addendum_appended_to_open_questions_register_section(self):
        locked = lock_section({}, "4", {"content": "Domain context.", "question": None}, "x", 5, force_locked=True)
        locked = lock_section(locked, "12", {"content": "Open questions body.", "question": None}, "", 0)

        result = append_open_questions_addendum(locked, FSD_DEFAULT_SECTIONS)

        assert "Section 4" in result["12"]["content"]
        assert "manual review" in result["12"]["content"].lower() or "recommend" in result["12"]["content"].lower()
        # Original dict is untouched
        assert "Section 4" not in locked["12"]["content"]

    def test_no_target_section_returns_unchanged_dict(self):
        sections_without_register = [s for s in FSD_DEFAULT_SECTIONS if "open question" not in s["title"].lower() and "assumption" not in s["title"].lower()]
        locked = lock_section({}, "4", {"content": "Domain context.", "question": None}, "x", 5, force_locked=True)

        result = append_open_questions_addendum(locked, sections_without_register)

        assert result == locked
