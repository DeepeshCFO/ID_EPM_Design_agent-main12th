"""Anthropic API gateway — the only file that imports or calls the Anthropic SDK."""

import logging
import os
import time

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 2.0  # seconds

_last_usage = {"input_tokens": 0, "output_tokens": 0}


class LLMError(Exception):
    """Raised when the LLM call fails after all retries."""


def get_last_usage() -> dict:
    """Return the input/output token counts from the most recent successful call_llm invocation."""
    return dict(_last_usage)


def _get_client() -> anthropic.Anthropic:
    """Instantiate an Anthropic client using the API key and optional base URL from the environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
        logger.info("Using custom Anthropic base URL: %s", base_url)
    return anthropic.Anthropic(**kwargs)


def call_llm(prompt: str, system: str, max_tokens: int, allow_truncation: bool = False) -> str:
    """Call the Anthropic Claude API and return the response text.

    Retries up to _MAX_RETRIES times with exponential backoff on transient errors.
    Raises LLMError with a user-readable message if all retries are exhausted.
    If allow_truncation is True, a max_tokens cutoff returns the partial text instead
    of raising, so the caller can attempt its own recovery from the truncated response.
    """
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    client = _get_client()

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info("LLM call attempt %d/%d (model=%s, max_tokens=%d)", attempt, _MAX_RETRIES, model, max_tokens)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            if not response.content:
                raise LLMError("The API returned an empty response. Check your model and token limits.")
            block = response.content[0]
            if not hasattr(block, "text"):
                raise LLMError(f"Unexpected response content type '{getattr(block, 'type', 'unknown')}'. Expected text.")
            text = block.text
            if response.usage is not None:
                _last_usage["input_tokens"] = response.usage.input_tokens
                _last_usage["output_tokens"] = response.usage.output_tokens
            logger.info("LLM call succeeded (attempt %d, stop_reason=%s)", attempt, response.stop_reason)
            if response.stop_reason == "max_tokens":
                if allow_truncation:
                    logger.warning(
                        "LLM response truncated at max_tokens=%d; returning partial text for caller-side recovery.",
                        max_tokens,
                    )
                    return text
                raise LLMError(
                    f"The response was truncated after hitting the max_tokens limit ({max_tokens}). "
                    "Increase the relevant MAX_TOKENS_* setting in .env and try again."
                )
            return text
        except anthropic.RateLimitError as exc:
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.warning("Rate limit hit (attempt %d). Retrying in %.1fs. %s", attempt, wait, exc)
            if attempt == _MAX_RETRIES:
                raise LLMError(f"Rate limit exceeded after {_MAX_RETRIES} attempts. Please try again later.") from exc
            time.sleep(wait)
        except anthropic.APIStatusError as exc:
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.error("API status error (attempt %d, status=%d): %s", attempt, exc.status_code, exc.message)
            if attempt == _MAX_RETRIES or exc.status_code < 500:
                raise LLMError(f"Anthropic API error (status {exc.status_code}): {exc.message}") from exc
            time.sleep(wait)
        except anthropic.APIConnectionError as exc:
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.error("API connection error (attempt %d): %s", attempt, exc)
            if attempt == _MAX_RETRIES:
                raise LLMError(f"Cannot connect to Anthropic API after {_MAX_RETRIES} attempts. Check your internet connection.") from exc
            time.sleep(wait)

    raise LLMError(f"LLM call failed after {_MAX_RETRIES} attempts.")


def stream_llm(prompt: str, system: str, max_tokens: int):
    """Stream a Claude response, yielding text chunks as they arrive.

    Retries up to _MAX_RETRIES times with exponential backoff — but only while no
    chunk has been yielded yet. Once the caller has started rendering partial text
    to the user, a failure is raised immediately rather than silently restarting
    output that has already been shown (CLAUDE.md §3.7: streaming section drafts).
    """
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    client = _get_client()

    for attempt in range(1, _MAX_RETRIES + 1):
        started = False
        try:
            logger.info("LLM stream attempt %d/%d (model=%s, max_tokens=%d)", attempt, _MAX_RETRIES, model, max_tokens)
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    started = True
                    yield text
                final_message = stream.get_final_message()

            if final_message.usage is not None:
                _last_usage["input_tokens"] = final_message.usage.input_tokens
                _last_usage["output_tokens"] = final_message.usage.output_tokens
            logger.info("LLM stream succeeded (attempt %d, stop_reason=%s)", attempt, final_message.stop_reason)
            if final_message.stop_reason == "max_tokens":
                raise LLMError(
                    f"The response was truncated after hitting the max_tokens limit ({max_tokens}). "
                    "Increase the relevant MAX_TOKENS_* setting in .env and try again."
                )
            return
        except anthropic.RateLimitError as exc:
            if started:
                raise LLMError(f"Rate limit hit mid-stream: {exc}") from exc
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.warning("Rate limit hit (attempt %d). Retrying in %.1fs. %s", attempt, wait, exc)
            if attempt == _MAX_RETRIES:
                raise LLMError(f"Rate limit exceeded after {_MAX_RETRIES} attempts. Please try again later.") from exc
            time.sleep(wait)
        except anthropic.APIStatusError as exc:
            if started:
                raise LLMError(f"API error mid-stream (status {exc.status_code}): {exc.message}") from exc
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.error("API status error (attempt %d, status=%d): %s", attempt, exc.status_code, exc.message)
            if attempt == _MAX_RETRIES or exc.status_code < 500:
                raise LLMError(f"Anthropic API error (status {exc.status_code}): {exc.message}") from exc
            time.sleep(wait)
        except anthropic.APIConnectionError as exc:
            if started:
                raise LLMError(f"Connection lost mid-stream: {exc}") from exc
            wait = _RETRY_BACKOFF_BASE ** attempt
            logger.error("API connection error (attempt %d): %s", attempt, exc)
            if attempt == _MAX_RETRIES:
                raise LLMError(f"Cannot connect to Anthropic API after {_MAX_RETRIES} attempts. Check your internet connection.") from exc
            time.sleep(wait)

    raise LLMError(f"LLM stream failed after {_MAX_RETRIES} attempts.")
