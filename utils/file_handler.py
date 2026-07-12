"""File upload validation and reading utilities."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_BRD_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_TEMPLATE_ALLOWED_EXTENSIONS = {".docx"}
_SUPPORTING_DOC_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_DISCUSSION_NOTES_MAX_CHARS = 5000


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""


def validate_and_read_brd(uploaded_file) -> tuple:
    """Validate and read the BRD upload. Returns (file_bytes, filename).

    Raises FileValidationError with a user-readable message on failure.
    """
    if uploaded_file is None:
        raise FileValidationError("No file uploaded. Please upload a BRD document.")

    filename = uploaded_file.name
    ext = Path(filename).suffix.lower()

    if ext not in _BRD_ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext}'. Please upload a PDF (.pdf) or Word (.docx) document."
        )

    file_bytes = uploaded_file.read()
    _check_file_size(file_bytes, filename)

    logger.info("BRD uploaded: %s (%.2f MB)", filename, get_file_size_mb(file_bytes))
    return file_bytes, filename


def validate_template(uploaded_file) -> bytes | None:
    """Validate and read an optional FSD/TSD template upload. Returns bytes or None.

    Raises FileValidationError if the file is present but invalid.
    """
    if uploaded_file is None:
        return None

    filename = uploaded_file.name
    ext = Path(filename).suffix.lower()

    if ext not in _TEMPLATE_ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Template must be a Word document (.docx). Received: '{ext}'"
        )

    file_bytes = uploaded_file.read()
    _check_file_size(file_bytes, filename)

    logger.info("Template uploaded: %s (%.2f MB)", filename, get_file_size_mb(file_bytes))
    return file_bytes


def validate_and_read_supporting_docs(uploaded_files: list) -> list:
    """Validate and read multiple optional supporting documents.

    Returns a list of (file_bytes, filename) tuples. Raises FileValidationError
    with a user-readable message on the first invalid file (name included).
    """
    if not uploaded_files:
        return []

    results = []
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        ext = Path(filename).suffix.lower()

        if ext not in _SUPPORTING_DOC_ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"'{filename}': unsupported file type '{ext}'. Please upload a PDF (.pdf) or Word (.docx) document."
            )

        file_bytes = uploaded_file.read()
        _check_file_size(file_bytes, filename)
        results.append((file_bytes, filename))

    logger.info("Supporting documents uploaded: %d file(s)", len(results))
    return results


def validate_discussion_notes(notes: str) -> str:
    """Validate the free-text discussion notes against the character limit.

    Returns the notes unchanged. Raises FileValidationError if the limit is exceeded.
    """
    if notes and len(notes) > _DISCUSSION_NOTES_MAX_CHARS:
        raise FileValidationError(
            f"Discussion notes are {len(notes):,} characters, which exceeds the "
            f"{_DISCUSSION_NOTES_MAX_CHARS:,} character limit. Please shorten your input."
        )
    return notes or ""


def get_file_size_mb(file_bytes: bytes) -> float:
    """Return the size of file_bytes in megabytes."""
    return len(file_bytes) / (1024 * 1024)


def _check_file_size(file_bytes: bytes, filename: str) -> None:
    """Raise FileValidationError if the file exceeds the configured size limit."""
    max_mb = float(os.getenv("MAX_FILE_SIZE_MB", "50"))
    size_mb = get_file_size_mb(file_bytes)
    if size_mb > max_mb:
        raise FileValidationError(
            f"'{filename}' is {size_mb:.1f} MB, which exceeds the {max_mb:.0f} MB limit. "
            "Please upload a smaller document."
        )
