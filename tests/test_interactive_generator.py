"""Tests for core/interactive_generator.py — the interactive per-section loop
(CLAUDE.md §3.7/§3.8a, FSD FR-09/FR-10/FR-15).

Sequence under test: (a) pre-generation questions are generated in their own call,
strictly before any content exists, and never resurface during the post-draft review
loop; (b)/(c) content generation streams chunks using this section's own pre-generation
answers; (e) locking stores pre_generation_questions, pre_generation_answers, and
correction_history as separate fields, all carried forward as context to later
sections; the Skip Review fast-mode hand-off renders already-locked content as plain
text for the legacy batch generator.
"""

import json
from unittest.mock import MagicMock, patch

from core.fsd_generator import generate_fsd_batch, split_into_batches
from core.interactive_generator import (
    append_open_questions_addendum,
    build_locked_context_text,
    generate_section_questions,
    get_max_regeneration_attempts,
    lock_section,
    should_force_lock,
    stream_feedback_regeneration,
    stream_section_draft,
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
SAMPLE_TECH_CONTEXT = {"technology": "SAP BW/4HANA", "sap_skill": SAMPLE_SAP_SKILL, "domain_skills": SAMPLE_DOMAIN_SKILLS}

SECTION_1 = FSD_DEFAULT_SECTIONS[0]
SECTION_2 = FSD_DEFAULT_SECTIONS[1]


def _mock_jinja_env(rendered: str = "rendered prompt"):
    mock_template = MagicMock()
    mock_template.render.return_value = rendered
    mock_env = MagicMock()
    mock_env.get_template.return_value = mock_template
    return mock_env


def _template_names(mock_env) -> list:
    return [call.args[0] for call in mock_env.get_template.call_args_list]


# ---------------------------------------------------------------------------
# (a) Pre-generation questions — generated before any content exists
# ---------------------------------------------------------------------------

class TestGenerateSectionQuestions:
    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_calls_llm_exactly_once_and_returns_parsed_questions(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = json.dumps(["Should currency translation use a fixed rate?", "Which legal entities are in scope?"])

        questions = generate_section_questions(
            section_spec=SECTION_1,
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology_context=SAMPLE_TECH_CONTEXT,
            locked_sections={},
        )

        mock_llm.assert_called_once()
        assert questions == ["Should currency translation use a fixed rate?", "Which legal entities are in scope?"]

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_uses_the_pregeneration_template_not_the_content_template(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = "[]"

        generate_section_questions(SECTION_1, SAMPLE_STRUCTURED_SUMMARY, SAMPLE_TECH_CONTEXT, {})

        names = _template_names(mock_env.return_value)
        assert "section_questions_pregeneration.j2" in names
        assert "section_generation_interactive.j2" not in names

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_zero_questions_is_a_valid_result(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = "[]"

        questions = generate_section_questions(SECTION_1, SAMPLE_STRUCTURED_SUMMARY, SAMPLE_TECH_CONTEXT, {})

        assert questions == []

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_caps_at_six_questions(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = json.dumps([f"Question {i}?" for i in range(10)])

        questions = generate_section_questions(SECTION_1, SAMPLE_STRUCTURED_SUMMARY, SAMPLE_TECH_CONTEXT, {})

        assert len(questions) == 6

    @patch("core.interactive_generator.call_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_malformed_json_degrades_to_empty_list_never_raises(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = "not json"

        questions = generate_section_questions(SECTION_1, SAMPLE_STRUCTURED_SUMMARY, SAMPLE_TECH_CONTEXT, {})

        assert questions == []

    @patch("core.interactive_generator.call_llm", side_effect=RuntimeError("boom"))
    @patch("core.interactive_generator.get_jinja_env")
    def test_llm_failure_degrades_to_empty_list_never_raises(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()

        questions = generate_section_questions(SECTION_1, SAMPLE_STRUCTURED_SUMMARY, SAMPLE_TECH_CONTEXT, {})

        assert questions == []


# ---------------------------------------------------------------------------
# (c)/(d) Streamed content generation — never surfaces a question
# ---------------------------------------------------------------------------

class TestStreamSectionDraft:
    @patch("core.interactive_generator.stream_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_yields_chunks_from_stream_llm(self, mock_env, mock_stream_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_stream_llm.return_value = iter(["Section content ", "streamed in pieces."])

        chunks = list(stream_section_draft(
            doc_type="FSD",
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            pre_generation_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            locked_sections={},
            target_section=SECTION_1,
            instructions="Write section 1.",
        ))

        assert chunks == ["Section content ", "streamed in pieces."]
        mock_stream_llm.assert_called_once()

    @patch("core.interactive_generator.stream_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_uses_the_content_template_not_the_question_template(self, mock_env, mock_stream_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_stream_llm.return_value = iter(["content"])

        list(stream_section_draft(
            doc_type="FSD", structured_summary=SAMPLE_STRUCTURED_SUMMARY, technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL, domain_skills=SAMPLE_DOMAIN_SKILLS, pre_generation_answers={},
            metadata=SAMPLE_METADATA, section_structure=FSD_DEFAULT_SECTIONS, locked_sections={},
            target_section=SECTION_1, instructions="Write section 1.",
        ))

        names = _template_names(mock_env.return_value)
        assert "section_generation_interactive.j2" in names
        assert "section_questions_pregeneration.j2" not in names

    @patch("core.interactive_generator.stream_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_passes_this_sections_pre_generation_answers_to_the_prompt(self, mock_env, mock_stream_llm):
        mock_jinja_env = _mock_jinja_env()
        mock_env.return_value = mock_jinja_env
        mock_stream_llm.return_value = iter(["content"])
        answers = {"Fixed rate or real-time feed?": "Fixed monthly rate."}

        list(stream_section_draft(
            doc_type="FSD", structured_summary=SAMPLE_STRUCTURED_SUMMARY, technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL, domain_skills=SAMPLE_DOMAIN_SKILLS, pre_generation_answers=answers,
            metadata=SAMPLE_METADATA, section_structure=FSD_DEFAULT_SECTIONS, locked_sections={},
            target_section=SECTION_1, instructions="Write section 1.",
        ))

        render_kwargs = mock_jinja_env.get_template.return_value.render.call_args.kwargs
        assert render_kwargs["pre_generation_answers"] == answers
        assert render_kwargs["target_section"] == SECTION_1


class TestStreamFeedbackRegeneration:
    @patch("core.interactive_generator.stream_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_yields_chunks_and_includes_feedback_in_the_prompt(self, mock_env, mock_stream_llm):
        mock_jinja_env = _mock_jinja_env()
        mock_env.return_value = mock_jinja_env
        mock_stream_llm.return_value = iter(["Revised ", "draft."])

        chunks = list(stream_feedback_regeneration(
            doc_type="FSD", structured_summary=SAMPLE_STRUCTURED_SUMMARY, technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL, domain_skills=SAMPLE_DOMAIN_SKILLS, pre_generation_answers={},
            metadata=SAMPLE_METADATA, section_structure=FSD_DEFAULT_SECTIONS, locked_sections={},
            target_section=SECTION_1, instructions="Write section 1.",
            previous_content="Original draft.", feedback_text="Use Y instead.",
        ))

        assert "".join(chunks) == "Revised draft."
        render_kwargs = mock_jinja_env.get_template.return_value.render.call_args.kwargs
        assert render_kwargs["feedback"] == {"previous_content": "Original draft.", "feedback_text": "Use Y instead."}


# ---------------------------------------------------------------------------
# locked_sections schema — pre_generation_answers and correction_history are
# separate fields, both carried forward as context to later sections
# ---------------------------------------------------------------------------

class TestLockSectionSchema:
    def test_stores_pre_generation_and_correction_fields_separately(self):
        locked = lock_section(
            {}, "1", {"content": "Section 1 body."},
            pre_generation_questions=["Q1?", "Q2?"],
            pre_generation_answers={"Q1?": "A1", "Q2?": ""},
            correction_history=["Make it shorter."],
            revision_count=1,
        )

        entry = locked["1"]
        assert entry["content"] == "Section 1 body."
        assert entry["pre_generation_questions"] == ["Q1?", "Q2?"]
        assert entry["pre_generation_answers"] == {"Q1?": "A1", "Q2?": ""}
        assert entry["correction_history"] == ["Make it shorter."]
        assert entry["revision_count"] == 1
        assert entry["force_locked"] is False

    def test_does_not_mutate_the_input_dict(self):
        original = {"1": {"content": "old"}}
        updated = lock_section(original, "2", {"content": "new"}, [], {}, [], 0)

        assert "2" not in original
        assert "2" in updated

    def test_locking_multiple_sections_accumulates_without_losing_earlier_ones(self):
        locked = lock_section({}, "1", {"content": "Section 1 body."}, [], {}, [], 0)
        locked = lock_section(locked, "2", {"content": "Section 2 body."}, ["Q?"], {"Q?": "A"}, ["fix this"], 1)

        assert set(locked.keys()) == {"1", "2"}
        assert locked["2"]["pre_generation_answers"] == {"Q?": "A"}
        assert locked["2"]["correction_history"] == ["fix this"]


class TestContextCarryForward:
    @patch("core.interactive_generator.stream_llm")
    @patch("core.interactive_generator.get_jinja_env")
    def test_second_section_prompt_includes_first_locked_sections_pregen_and_correction_fields(self, mock_env, mock_stream_llm):
        mock_jinja_env = _mock_jinja_env()
        mock_env.return_value = mock_jinja_env
        mock_stream_llm.return_value = iter(["content"])

        locked_sections = lock_section(
            {}, "1", {"content": "Executive summary body."},
            pre_generation_questions=["What is the reporting horizon?"],
            pre_generation_answers={"What is the reporting horizon?": "3 years."},
            correction_history=["Tighten the second paragraph."],
            revision_count=1,
        )

        list(stream_section_draft(
            doc_type="FSD", structured_summary=SAMPLE_STRUCTURED_SUMMARY, technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL, domain_skills=SAMPLE_DOMAIN_SKILLS, pre_generation_answers={},
            metadata=SAMPLE_METADATA, section_structure=FSD_DEFAULT_SECTIONS, locked_sections=locked_sections,
            target_section=SECTION_2, instructions="Write section 2.",
        ))

        render_kwargs = mock_jinja_env.get_template.return_value.render.call_args.kwargs
        rendered_locked = render_kwargs["locked_sections"]
        assert len(rendered_locked) == 1
        assert rendered_locked[0]["number"] == "1"
        assert rendered_locked[0]["content"] == "Executive summary body."
        assert rendered_locked[0]["pre_generation_questions"] == ["What is the reporting horizon?"]
        assert rendered_locked[0]["pre_generation_answers"] == {"What is the reporting horizon?": "3 years."}
        assert rendered_locked[0]["correction_history"] == ["Tighten the second paragraph."]


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
        locked = lock_section({}, "4", {"content": "Best-effort draft."}, [], {}, ["still not right"], 5, force_locked=True)
        assert locked["4"]["force_locked"] is True
        assert locked["4"]["revision_count"] == 5


# ---------------------------------------------------------------------------
# Open Questions Register addendum for force-locked sections
# ---------------------------------------------------------------------------

class TestOpenQuestionsAddendum:
    def test_no_addendum_when_nothing_force_locked(self):
        locked = lock_section({}, "1", {"content": "Body."}, [], {}, [], 0)
        result = append_open_questions_addendum(locked, FSD_DEFAULT_SECTIONS)
        assert result == locked

    def test_addendum_appended_to_open_questions_register_section(self):
        locked = lock_section({}, "4", {"content": "Domain context."}, [], {}, ["x"], 5, force_locked=True)
        locked = lock_section(locked, "12", {"content": "Open questions body."}, [], {}, [], 0)

        result = append_open_questions_addendum(locked, FSD_DEFAULT_SECTIONS)

        assert "Section 4" in result["12"]["content"]
        assert "manual review" in result["12"]["content"].lower() or "recommend" in result["12"]["content"].lower()
        # Original dict is untouched
        assert "Section 4" not in locked["12"]["content"]

    def test_no_target_section_returns_unchanged_dict(self):
        sections_without_register = [s for s in FSD_DEFAULT_SECTIONS if "open question" not in s["title"].lower() and "assumption" not in s["title"].lower()]
        locked = lock_section({}, "4", {"content": "Domain context."}, [], {}, ["x"], 5, force_locked=True)

        result = append_open_questions_addendum(locked, sections_without_register)

        assert result == locked


# ---------------------------------------------------------------------------
# Skip Review fast-mode hand-off — context text for the legacy batch generator
# ---------------------------------------------------------------------------

class TestBuildLockedContextText:
    def test_empty_locked_sections_returns_empty_string(self):
        assert build_locked_context_text({}, FSD_DEFAULT_SECTIONS) == ""

    def test_renders_locked_section_number_title_and_content(self):
        locked = lock_section({}, "1", {"content": "Document Control body."}, [], {}, [], 0)

        text = build_locked_context_text(locked, FSD_DEFAULT_SECTIONS)

        assert "Section 1" in text
        assert "Document Control" in text
        assert "Document Control body." in text

    def test_orders_sections_numerically(self):
        locked = lock_section({}, "10", {"content": "Ten body."}, [], {}, [], 0)
        locked = lock_section(locked, "2", {"content": "Two body."}, [], {}, [], 0)

        text = build_locked_context_text(locked, FSD_DEFAULT_SECTIONS)

        assert text.index("Two body.") < text.index("Ten body.")


class TestFastModeHandoffEndToEnd:
    """Simulates the Skip Review button's core-layer effect: already-locked sections'
    content is preserved as context, and the remaining sections are generated purely
    through the legacy batch generator — no pre-generation question call is made."""

    @patch("core.fsd_generator.call_llm")
    @patch("core.fsd_generator.get_jinja_env")
    def test_locked_content_reaches_the_batch_prompt_with_no_question_call(self, mock_env, mock_llm):
        mock_template = MagicMock()
        mock_template.render.return_value = "rendered"
        mock_env.return_value.get_template.return_value = mock_template
        mock_llm.return_value = "## SECTION_2:\nContent."

        # Section 1 was already approved via the interactive loop before the user
        # clicked "Skip Review — Generate Full FSD Now".
        locked_sections = lock_section(
            {}, "1", {"content": "Document Control body — already approved."}, [], {}, [], 0,
        )
        locked_context = build_locked_context_text(locked_sections, FSD_DEFAULT_SECTIONS)
        assert "Document Control body — already approved." in locked_context

        remaining = [s for s in FSD_DEFAULT_SECTIONS if s["number"] != "1"]
        batches = split_into_batches(remaining)
        generate_fsd_batch(
            structured_summary=SAMPLE_STRUCTURED_SUMMARY,
            technology="SAP BW/4HANA",
            sap_skill=SAMPLE_SAP_SKILL,
            domain_skills=SAMPLE_DOMAIN_SKILLS,
            clarification_answers={},
            metadata=SAMPLE_METADATA,
            section_structure=FSD_DEFAULT_SECTIONS,
            batch_sections=batches[0],
            locked_context=locked_context,
        )

        render_kwargs = mock_template.render.call_args.kwargs
        assert "Document Control body — already approved." in render_kwargs["locked_context"]
        # Exactly one LLM call for this batch — no separate pre-generation question call.
        mock_llm.assert_called_once()
