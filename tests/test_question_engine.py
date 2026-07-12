"""Tests for core/question_engine.py."""

import json
import pytest
from unittest.mock import patch, MagicMock

from core.question_engine import generate_questions, _parse_questions


SAMPLE_STRUCTURED_SUMMARY = {
    "requirements": ["Daily P&L reporting by legal entity", "Rolling 12-month forecast"],
    "kpis": ["Revenue", "EBITDA", "DSO"],
    "data_sources": ["S/4HANA"],
    "domain": ["finance"],
    "key_entities": ["Legal Entity", "Cost Centre"],
    "open_gaps": ["Source system version not specified"],
}

SAMPLE_SAP_SKILL = {
    "summary": "SAP BW/4HANA analytics",
    "key_concepts": ["aDSO", "ODP extraction"],
    "kpis": ["Revenue", "EBITDA"],
    "sap_objects": ["InfoObject", "DTP"],
    "common_patterns": ["Delta extraction"],
}

SAMPLE_DOMAIN_SKILLS = [
    {
        "domain": "finance",
        "summary": "Finance domain",
        "key_concepts": ["P&L"],
        "kpis": ["EBITDA"],
        "sap_objects": [],
        "common_patterns": [],
    }
]

VALID_QUESTIONS_JSON = json.dumps([
    {"id": 1, "question": "Is the source system SAP ECC or S/4HANA?", "category": "Data Sources", "impact": "Affects extraction method"},
    {"id": 2, "question": "How many company codes are in scope?", "category": "Scope", "impact": "Affects authorisation model"},
])


# ---------------------------------------------------------------------------
# _parse_questions unit tests
# ---------------------------------------------------------------------------

class TestParseQuestions:
    def test_valid_json_returns_list(self):
        result = _parse_questions(VALID_QUESTIONS_JSON)
        assert len(result) == 2
        assert result[0]["question"] == "Is the source system SAP ECC or S/4HANA?"

    def test_json_with_code_fences_parsed(self):
        fenced = f"```json\n{VALID_QUESTIONS_JSON}\n```"
        result = _parse_questions(fenced)
        assert len(result) == 2

    def test_malformed_json_returns_empty_list(self):
        result = _parse_questions("This is not JSON at all.")
        assert result == []

    def test_empty_array_json_returns_empty_list(self):
        result = _parse_questions("[]")
        assert result == []

    def test_non_list_json_returns_empty_list(self):
        result = _parse_questions('{"key": "value"}')
        assert result == []

    def test_missing_question_key_filtered_out(self):
        data = json.dumps([{"id": 1, "category": "Scope"}])  # no "question" key
        result = _parse_questions(data)
        assert result == []


# ---------------------------------------------------------------------------
# generate_questions integration tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestGenerateQuestions:
    @patch("core.question_engine.call_llm")
    def test_valid_summary_returns_questions(self, mock_llm):
        mock_llm.return_value = VALID_QUESTIONS_JSON
        with patch("core.question_engine.get_jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "rendered prompt"
            mock_env.return_value.get_template.return_value = mock_template

            result = generate_questions(SAMPLE_STRUCTURED_SUMMARY, "SAP BW/4HANA", SAMPLE_SAP_SKILL, SAMPLE_DOMAIN_SKILLS)

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("core.question_engine.call_llm")
    def test_empty_summary_returns_empty_list_without_error(self, mock_llm):
        mock_llm.return_value = "[]"
        empty_summary = {"requirements": [], "kpis": [], "data_sources": [], "domain": [], "key_entities": [], "open_gaps": []}
        with patch("core.question_engine.get_jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "rendered prompt"
            mock_env.return_value.get_template.return_value = mock_template

            result = generate_questions(empty_summary, "SAP BW/4HANA", SAMPLE_SAP_SKILL, SAMPLE_DOMAIN_SKILLS)

        assert result == []

    @patch("core.question_engine.call_llm")
    def test_llm_returns_malformed_json_returns_empty_list(self, mock_llm):
        mock_llm.return_value = "I cannot parse this as JSON. Sorry!"
        with patch("core.question_engine.get_jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "rendered prompt"
            mock_env.return_value.get_template.return_value = mock_template

            result = generate_questions(SAMPLE_STRUCTURED_SUMMARY, "SAP BW/4HANA", SAMPLE_SAP_SKILL, SAMPLE_DOMAIN_SKILLS)

        assert result == []

    @patch("core.question_engine.call_llm", side_effect=Exception("API failure"))
    def test_llm_exception_returns_empty_list(self, mock_llm):
        with patch("core.question_engine.get_jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "rendered prompt"
            mock_env.return_value.get_template.return_value = mock_template

            result = generate_questions(SAMPLE_STRUCTURED_SUMMARY, "SAP BW/4HANA", SAMPLE_SAP_SKILL, SAMPLE_DOMAIN_SKILLS)

        assert result == []
