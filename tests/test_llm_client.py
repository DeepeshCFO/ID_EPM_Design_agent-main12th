"""Tests for core/llm_client.py streaming support (stream_llm) — CLAUDE.md §3.7
point 3: section drafts must stream, with retry/backoff preserved for stream
failures that happen before any chunk has reached the caller."""

from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest

from core.llm_client import LLMError, get_last_usage, stream_llm

_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


class _FakeStreamContext:
    """Minimal stand-in for the context manager returned by client.messages.stream()."""

    def __init__(self, chunks=(), stop_reason="end_turn", usage=None, raise_on_enter=None, raise_mid_stream=None):
        self._chunks = list(chunks)
        self._stop_reason = stop_reason
        self._usage = usage or MagicMock(input_tokens=10, output_tokens=20)
        self._raise_on_enter = raise_on_enter
        self._raise_mid_stream = raise_mid_stream

    def __enter__(self):
        if self._raise_on_enter is not None:
            raise self._raise_on_enter
        return self

    def __exit__(self, *args):
        return False

    @property
    def text_stream(self):
        for chunk in self._chunks:
            yield chunk
        if self._raise_mid_stream is not None:
            raise self._raise_mid_stream

    def get_final_message(self):
        message = MagicMock()
        message.stop_reason = self._stop_reason
        message.usage = self._usage
        return message


def _fake_client(*stream_contexts):
    client = MagicMock()
    client.messages.stream.side_effect = list(stream_contexts)
    return client


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr("core.llm_client.time.sleep", lambda seconds: None)


class TestStreamLlmHappyPath:
    @patch("core.llm_client._get_client")
    def test_yields_all_chunks_in_order(self, mock_get_client):
        mock_get_client.return_value = _fake_client(_FakeStreamContext(["Hello, ", "world."]))

        chunks = list(stream_llm(prompt="p", system="s", max_tokens=100))

        assert chunks == ["Hello, ", "world."]
        assert "".join(chunks) == "Hello, world."

    @patch("core.llm_client._get_client")
    def test_updates_last_usage_after_stream_completes(self, mock_get_client):
        usage = MagicMock(input_tokens=42, output_tokens=99)
        mock_get_client.return_value = _fake_client(_FakeStreamContext(["hi"], usage=usage))

        list(stream_llm(prompt="p", system="s", max_tokens=100))

        assert get_last_usage() == {"input_tokens": 42, "output_tokens": 99}

    @patch("core.llm_client._get_client")
    def test_max_tokens_stop_reason_raises_llm_error(self, mock_get_client):
        mock_get_client.return_value = _fake_client(_FakeStreamContext(["partial"], stop_reason="max_tokens"))

        with pytest.raises(LLMError):
            list(stream_llm(prompt="p", system="s", max_tokens=10))


class TestStreamLlmRetryBeforeFirstChunk:
    @patch("core.llm_client._get_client")
    def test_retries_transparently_when_connection_error_precedes_any_chunk(self, mock_get_client):
        failing = _FakeStreamContext(raise_on_enter=anthropic.APIConnectionError(request=_REQUEST))
        succeeding = _FakeStreamContext(["ok"])
        client = _fake_client(failing, succeeding)
        mock_get_client.return_value = client

        chunks = list(stream_llm(prompt="p", system="s", max_tokens=100))

        assert "".join(chunks) == "ok"
        assert client.messages.stream.call_count == 2

    @patch("core.llm_client._get_client")
    def test_raises_llm_error_after_max_retries_all_failing_pre_chunk(self, mock_get_client):
        always_failing = [
            _FakeStreamContext(raise_on_enter=anthropic.APIConnectionError(request=_REQUEST))
            for _ in range(5)
        ]
        mock_get_client.return_value = _fake_client(*always_failing)

        with pytest.raises(LLMError):
            list(stream_llm(prompt="p", system="s", max_tokens=100))


class TestStreamLlmMidStreamFailure:
    @patch("core.llm_client._get_client")
    def test_mid_stream_failure_raises_immediately_without_retry(self, mock_get_client):
        mid_stream_failure = _FakeStreamContext(
            chunks=["partial content "],
            raise_mid_stream=anthropic.APIConnectionError(request=_REQUEST),
        )
        client = _fake_client(mid_stream_failure)
        mock_get_client.return_value = client

        with pytest.raises(LLMError):
            list(stream_llm(prompt="p", system="s", max_tokens=100))

        # No retry attempted once the caller has already seen partial output.
        assert client.messages.stream.call_count == 1
