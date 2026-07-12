"""Tests for core/brd_summariser.py."""

import json
import pytest
from unittest.mock import patch, MagicMock

from core.brd_summariser import generate_structured_summary, BRDSummariserError, _parse_summary


SAMPLE_SAP_SKILL = {
    "summary": "SAP BW/4HANA",
    "key_concepts": ["aDSO"],
    "kpis": ["Revenue"],
    "sap_objects": ["InfoObject"],
    "common_patterns": ["Delta extraction"],
}

VALID_SUMMARY_JSON = json.dumps({
    "requirements": ["Daily P&L reporting"],
    "kpis": ["EBITDA", "Revenue"],
    "data_sources": ["S/4HANA"],
    "domain": ["finance"],
    "key_entities": ["Legal Entity"],
    "open_gaps": ["Source system version not specified"],
})


def _mock_jinja_env(rendered: str = "rendered prompt"):
    mock_template = MagicMock()
    mock_template.render.return_value = rendered
    mock_env = MagicMock()
    mock_env.get_template.return_value = mock_template
    return mock_env


# ---------------------------------------------------------------------------
# _parse_summary unit tests
# ---------------------------------------------------------------------------

class TestParseSummary:
    def test_valid_json_returns_full_shape(self):
        result = _parse_summary(VALID_SUMMARY_JSON)
        assert set(result.keys()) == {
            "requirements", "kpis", "data_sources", "domain", "key_entities", "open_gaps",
            "recommended_technologies",
        }
        assert result["domain"] == ["finance"]
        assert result["recommended_technologies"] == []

    def test_recommended_technologies_passed_through_when_present(self):
        data = json.loads(VALID_SUMMARY_JSON)
        data["recommended_technologies"] = ["SAP BW/4HANA"]
        result = _parse_summary(json.dumps(data))
        assert result["recommended_technologies"] == ["SAP BW/4HANA"]

    def test_code_fenced_json_parsed(self):
        fenced = f"```json\n{VALID_SUMMARY_JSON}\n```"
        result = _parse_summary(fenced)
        assert result["requirements"] == ["Daily P&L reporting"]

    def test_missing_keys_default_to_empty_list(self):
        result = _parse_summary(json.dumps({"requirements": ["A requirement"]}))
        assert result["requirements"] == ["A requirement"]
        assert result["kpis"] == []
        assert result["domain"] == []

    def test_malformed_json_raises(self):
        with pytest.raises(BRDSummariserError):
            _parse_summary("this is not JSON")

    def test_non_object_json_raises(self):
        with pytest.raises(BRDSummariserError):
            _parse_summary("[1, 2, 3]")


# ---------------------------------------------------------------------------
# generate_structured_summary integration tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestGenerateStructuredSummary:
    @patch("core.brd_summariser.call_llm")
    @patch("core.brd_summariser.get_jinja_env")
    def test_returns_structured_dict(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = VALID_SUMMARY_JSON

        result = generate_structured_summary("combined BRD text", "SAP BW/4HANA", SAMPLE_SAP_SKILL)

        assert result["domain"] == ["finance"]
        assert "Daily P&L reporting" in result["requirements"]

    @patch("core.brd_summariser.call_llm")
    @patch("core.brd_summariser.get_jinja_env")
    def test_malformed_llm_response_raises(self, mock_env, mock_llm):
        mock_env.return_value = _mock_jinja_env()
        mock_llm.return_value = "not valid JSON at all"

        with pytest.raises(BRDSummariserError):
            generate_structured_summary("combined BRD text", "SAP BW/4HANA", SAMPLE_SAP_SKILL)

    @patch("core.brd_summariser.call_llm")
    @patch("core.brd_summariser.get_jinja_env")
    def test_technology_options_passed_to_prompt_in_auto_mode(self, mock_env, mock_llm):
        mock_template = MagicMock()
        mock_template.render.return_value = "rendered"
        mock_env.return_value.get_template.return_value = mock_template
        mock_llm.return_value = VALID_SUMMARY_JSON

        generate_structured_summary(
            "combined BRD text", "auto", SAMPLE_SAP_SKILL, technology_options=["SAP BW/4HANA", "SAP PaPM"],
        )

        render_kwargs = mock_template.render.call_args.kwargs
        assert render_kwargs["technology"] == "auto"
        assert render_kwargs["technology_options"] == ["SAP BW/4HANA", "SAP PaPM"]
