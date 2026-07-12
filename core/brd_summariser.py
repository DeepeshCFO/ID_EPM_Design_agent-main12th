"""BRD pre-summarisation — condenses raw input into a structured requirements dict."""

import json
import logging
import os
from collections import Counter

from core.llm_client import call_llm
from utils.jinja_env import get_jinja_env

logger = logging.getLogger(__name__)

_SUMMARY_KEYS = [
    "requirements", "kpis", "data_sources", "domain", "key_entities", "open_gaps",
    "recommended_technologies",
]

# Part 1 — dynamic token budget thresholds (word count -> output max_tokens)
_SMALL_INPUT_WORDS = 5_000
_MAX_TOKENS_SMALL = 2000
_MEDIUM_INPUT_WORDS = 15_000
_MAX_TOKENS_MEDIUM = 4000
_MAX_TOKENS_LARGE = 6000

# Part 2 — chunking thresholds for large documents
_CHUNK_THRESHOLD_WORDS = 12_000
_CHUNK_SIZE_WORDS = 8_000
_CHUNK_OVERLAP_WORDS = 500


class BRDSummariserError(Exception):
    """Raised when the pre-summarisation call fails or returns unusable output."""


def generate_structured_summary(
    combined_text: str, technology: str, sap_skill: dict, technology_options: list | None = None,
) -> dict:
    """Run the pre-summarisation LLM call and return the structured summary dict.

    Output keys: requirements, kpis, data_sources, domain, key_entities, open_gaps,
    recommended_technologies (populated only when technology == "auto").
    Large inputs are automatically chunked (see chunk_and_summarise); everything else
    runs as a single call with a token budget sized to the input.
    Raises BRDSummariserError if the LLM response cannot be parsed into that shape —
    every downstream call depends on this dict, so failure here must not be silent.
    """
    word_count = len(combined_text.split())
    logger.info("Combined input word count: %d", word_count)

    if word_count > _CHUNK_THRESHOLD_WORDS:
        return chunk_and_summarise(combined_text, technology, sap_skill, technology_options)

    return _summarise_single(combined_text, technology, sap_skill, technology_options)


def chunk_and_summarise(
    combined_text: str, technology: str, sap_skill: dict, technology_options: list | None,
) -> dict:
    """Summarise a large document by splitting it into overlapping chunks and merging results.

    Used when the input exceeds _CHUNK_THRESHOLD_WORDS. Each chunk is summarised
    independently with the same prompt, then the per-chunk summaries are merged into
    one structured summary dict.
    """
    words = combined_text.split()
    chunks = _split_into_chunks(words, _CHUNK_SIZE_WORDS, _CHUNK_OVERLAP_WORDS)
    logger.info(
        "Input exceeds %d words — split into %d chunks of ~%d words (overlap %d) for summarisation.",
        _CHUNK_THRESHOLD_WORDS, len(chunks), _CHUNK_SIZE_WORDS, _CHUNK_OVERLAP_WORDS,
    )

    chunk_summaries = []
    for i, chunk_text in enumerate(chunks, start=1):
        logger.info("Summarising chunk %d/%d (%d words)", i, len(chunks), len(chunk_text.split()))
        chunk_summaries.append(_summarise_single(chunk_text, technology, sap_skill, technology_options))

    return _merge_chunk_summaries(chunk_summaries)


def _summarise_single(
    combined_text: str, technology: str, sap_skill: dict, technology_options: list | None,
) -> dict:
    """Run a single summarisation LLM call on text sized to fit one request."""
    system_prompt = _render_system_prompt(sap_skill)
    user_prompt = _render_summarisation_prompt(combined_text, technology, technology_options)

    max_tokens = _compute_max_tokens(len(combined_text.split()))
    raw = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=max_tokens, allow_truncation=True)

    summary = parse_summary_response(raw)
    logger.info(
        "Structured summary generated: %d requirements, %d open gaps, domains=%s",
        len(summary["requirements"]), len(summary["open_gaps"]), summary["domain"],
    )
    return summary


def _compute_max_tokens(word_count: int) -> int:
    """Size the output token budget to the input word count. Never exceeds 6000."""
    if word_count < _SMALL_INPUT_WORDS:
        max_tokens = _MAX_TOKENS_SMALL
    elif word_count <= _MEDIUM_INPUT_WORDS:
        max_tokens = _MAX_TOKENS_MEDIUM
    else:
        max_tokens = _MAX_TOKENS_LARGE
    logger.info("Input word count: %d — selected max_tokens budget: %d", word_count, max_tokens)
    return max_tokens


def _split_into_chunks(words: list, chunk_size: int, overlap: int) -> list:
    """Slide a window of chunk_size words across the word list with the given overlap."""
    step = chunk_size - overlap
    total = len(words)
    chunks = []
    start = 0
    while start < total:
        end = min(start + chunk_size, total)
        chunks.append(" ".join(words[start:end]))
        if end == total:
            break
        start += step
    return chunks


def _merge_chunk_summaries(summaries: list) -> dict:
    """Merge per-chunk structured summaries into one deduplicated summary dict."""
    return {
        "requirements": _dedup_union(s["requirements"] for s in summaries),
        "kpis": _dedup_union(s["kpis"] for s in summaries),
        "data_sources": _dedup_union(s["data_sources"] for s in summaries),
        "domain": _most_frequent_domain(s["domain"] for s in summaries),
        "key_entities": _dedup_union(s["key_entities"] for s in summaries),
        "open_gaps": [item for s in summaries for item in s["open_gaps"]],
        "recommended_technologies": _dedup_union(s["recommended_technologies"] for s in summaries),
    }


def _dedup_union(lists) -> list:
    """Flatten a sequence of lists into an order-preserving, deduplicated list."""
    seen = set()
    result = []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _most_frequent_domain(domain_lists) -> list:
    """Return the domain(s) occurring most often across chunk-level domain detections."""
    counts = Counter()
    for domains in domain_lists:
        counts.update(domains)
    if not counts:
        return []
    top_count = max(counts.values())
    return [domain for domain, count in counts.items() if count == top_count]


def _render_system_prompt(sap_skill: dict) -> str:
    """Render the base system prompt. Domain skills are not yet known at this stage."""
    env = get_jinja_env()
    template = env.get_template("base_system.j2")
    return template.render(
        app_title=os.getenv("APP_TITLE", "SAP EPM Design Agent"),
        sap_skill=sap_skill,
        domain_skills=[],
    )


def _render_summarisation_prompt(combined_text: str, technology: str, technology_options: list | None) -> str:
    """Render the pre-summarisation prompt."""
    env = get_jinja_env()
    template = env.get_template("brd_summarisation.j2")
    return template.render(
        combined_text=combined_text, technology=technology, technology_options=technology_options or [],
    )


def parse_summary_response(raw: str) -> dict:
    """Parse the LLM JSON response into the structured summary dict, tolerating truncation.

    Strips markdown code fences, then tries a straight json.loads(). If that fails,
    attempts to recover a partial object by scanning backwards for the last closing
    bracket that yields valid JSON once any open strings/arrays/objects are balanced.
    Missing keys are always filled with empty lists. Raises BRDSummariserError only
    if no valid JSON object can be recovered at all.
    """
    cleaned = _strip_code_fences(raw)

    data = _try_load_json(cleaned)
    truncated = False
    if data is None:
        data = _recover_truncated_json(cleaned)
        truncated = data is not None

    if data is None:
        raise BRDSummariserError("Could not parse the pre-summarisation response as JSON.")

    if not isinstance(data, dict):
        raise BRDSummariserError("Pre-summarisation response was not a JSON object.")

    if truncated:
        recovered_keys = [key for key in _SUMMARY_KEYS if key in data]
        logger.warning(
            "Summary response was truncated — partial recovery succeeded. Fields recovered: %s",
            recovered_keys,
        )

    return {key: (data.get(key) or []) for key in _SUMMARY_KEYS}


# Backward-compatible alias — existing callers/tests refer to this as _parse_summary.
_parse_summary = parse_summary_response


def _strip_code_fences(raw: str) -> str:
    """Strip a leading/trailing ``` or ```json code fence, if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])
    return raw.strip()


def _try_load_json(text: str):
    """Attempt a direct json.loads(), returning None on failure instead of raising."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _recover_truncated_json(text: str):
    """Recover a JSON object from truncated text.

    Scans backwards over closing bracket positions, and for each candidate, balances
    any strings/arrays/objects left open by the cutoff before attempting to parse.
    Returns the first candidate that parses successfully, or None if none do.
    """
    start = text.find("{")
    if start == -1:
        return None

    for idx in range(len(text) - 1, start - 1, -1):
        if text[idx] not in "}]":
            continue
        repaired = _close_open_brackets(text[start:idx + 1])
        if repaired is None:
            continue
        candidate = _try_load_json(repaired)
        if candidate is not None:
            return candidate
    return None


def _close_open_brackets(snippet: str):
    """Balance a JSON snippet by closing any strings, arrays, or objects left open.

    Returns None if the snippet contains mismatched brackets (i.e. is not a valid
    prefix of some JSON document), so the caller can move on to the next candidate.
    """
    stack = []
    in_string = False
    escape = False
    for ch in snippet:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                return None
            opener = stack.pop()
            if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                return None

    repaired = snippet
    if in_string:
        repaired += '"'
    for opener in reversed(stack):
        repaired += "}" if opener == "{" else "]"
    return repaired
