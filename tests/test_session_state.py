"""Tests for utils/session_state.py step-numbering helpers.

Regression coverage for the "Step 4 -> Step 6" bug: displayed step numbers must
always be contiguous, derived from the actual active step sequence for the current
generation mode, regardless of which steps are skipped (STEP_QUESTIONS only applies
in legacy batched mode).
"""

from utils.session_state import (
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
    display_step_number,
)


class TestActiveStepSequence:
    def test_interactive_mode_excludes_step_questions(self):
        assert STEP_QUESTIONS not in active_step_sequence(True)

    def test_legacy_mode_includes_step_questions(self):
        assert STEP_QUESTIONS in active_step_sequence(False)

    def test_interactive_mode_has_nine_steps(self):
        assert len(active_step_sequence(True)) == 9

    def test_legacy_mode_has_ten_steps(self):
        assert len(active_step_sequence(False)) == 10

    def test_every_other_step_present_in_both_modes(self):
        always_present = [
            STEP_UPLOAD, STEP_ADDITIONAL_INPUT, STEP_SELECT_TECHNOLOGY, STEP_ANALYSE,
            STEP_GENERATE_FSD, STEP_FSD_DOWNLOAD, STEP_TSD_INPUT, STEP_GENERATE_TSD,
            STEP_TSD_DOWNLOAD,
        ]
        for step in always_present:
            assert step in active_step_sequence(True)
            assert step in active_step_sequence(False)


class TestDisplayStepNumberIsContiguous:
    def test_interactive_mode_numbers_have_no_gap(self):
        numbers = [display_step_number(s, True) for s in active_step_sequence(True)]
        assert numbers == list(range(1, len(numbers) + 1))

    def test_legacy_mode_numbers_have_no_gap(self):
        numbers = [display_step_number(s, False) for s in active_step_sequence(False)]
        assert numbers == list(range(1, len(numbers) + 1))

    def test_step_generate_fsd_is_display_number_5_in_interactive_mode(self):
        # Regression check: with STEP_QUESTIONS (raw value 5) skipped, the next step
        # (STEP_GENERATE_FSD, raw value 6) must be renumbered to 5 — not left at 6,
        # which is what produced the "Step 4 -> Step 6" gap.
        assert display_step_number(STEP_GENERATE_FSD, True) == 5

    def test_step_generate_fsd_is_display_number_6_in_legacy_mode(self):
        assert display_step_number(STEP_GENERATE_FSD, False) == 6

    def test_every_downstream_step_shifts_by_one_in_interactive_mode(self):
        downstream_steps = [STEP_FSD_DOWNLOAD, STEP_TSD_INPUT, STEP_GENERATE_TSD, STEP_TSD_DOWNLOAD]
        for step in downstream_steps:
            assert display_step_number(step, True) == display_step_number(step, False) - 1

    def test_unknown_step_constant_falls_back_to_raw_value(self):
        assert display_step_number(999, True) == 999
