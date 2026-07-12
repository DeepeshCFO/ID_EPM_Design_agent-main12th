"""Shared Jinja2 environment factory — the only place a prompts Environment is created."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_env: Environment | None = None


def get_jinja_env() -> Environment:
    """Return the shared Jinja2 Environment pointing at the prompts directory."""
    global _env
    if _env is None:
        _env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)), autoescape=False)
    return _env
