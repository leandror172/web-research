"""Model context-window lookup — queries Ollama, with JSON overrides/fallback."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import httpx

_CONFIG_PATH = Path(__file__).parent / "models.json"

# Hardcoded defaults if JSON file is also missing
_DEFAULT_CONTEXT_TOKENS = 8000
_DEFAULT_PROMPT_RESERVE = 2000
_DEFAULT_CHARS_PER_TOKEN = 4


@lru_cache(maxsize=1)
def _load_config() -> dict:
    """Load model overrides from models.json, or return hardcoded defaults."""
    if not _CONFIG_PATH.exists():
        return {
            "defaults": {
                "context_tokens": _DEFAULT_CONTEXT_TOKENS,
                "prompt_reserve_tokens": _DEFAULT_PROMPT_RESERVE,
                "chars_per_token": _DEFAULT_CHARS_PER_TOKEN,
            },
            "models": {},
        }
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: failed to load models.json: {e}. Using hardcoded defaults.")
        return {
            "defaults": {
                "context_tokens": _DEFAULT_CONTEXT_TOKENS,
                "prompt_reserve_tokens": _DEFAULT_PROMPT_RESERVE,
                "chars_per_token": _DEFAULT_CHARS_PER_TOKEN,
            },
            "models": {},
        }


def _get_ollama_context_length(model: str) -> int | None:
    """Fetch context length from Ollama's /api/show endpoint."""
    try:
        response = httpx.post(
            "http://localhost:11434/api/show",
            json={"model": model},
            timeout=5.0,
        )
        response.raise_for_status()

        model_info = response.json().get("model_info", {})
        for key, value in model_info.items():
            if key.endswith(".context_length"):
                return int(value)

        return None
    except (httpx.RequestError, httpx.HTTPStatusError, KeyError, ValueError):
        return None


@lru_cache(maxsize=32)
def max_extract_chars(model: str) -> int:
    """Compute usable content chars for a model, based on its context window."""
    cfg = _load_config()
    defaults = cfg["defaults"]

    # Check JSON override first (explicit cap takes priority over Ollama)
    model_override = cfg["models"].get(model, {})
    context = model_override.get("context_tokens")

    if context is None:
        # Query Ollama for actual context length
        context = _get_ollama_context_length(model)
        if context is None:
            context = defaults["context_tokens"]
            print(f"Note: using default context ({context} tokens) for {model}")

    reserve = defaults["prompt_reserve_tokens"]
    cpt = defaults["chars_per_token"]

    return (context - reserve) * cpt
