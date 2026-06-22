"""Extractor implementation using Ollama's /api/chat endpoint."""

from __future__ import annotations

import json
import logging
import time

import httpx

from web_research.extraction.prompts import build_prompt
from web_research.extraction.protocols import ExtractionConfig, ExtractionResult

logger = logging.getLogger(__name__)


class OllamaExtractor:
    """Calls Ollama to extract structured data from text."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url

    def extract(self, text: str, config: ExtractionConfig) -> ExtractionResult:
        prompt_text, schema = build_prompt(
            content=text,
            prompt_type=config.prompt_type,
            focus=config.focus,
        )

        logger.debug(
            "extract start: model=%s prompt_type=%s focus=%s input_chars=%d",
            config.model,
            config.prompt_type,
            config.focus,
            len(text),
        )

        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt_text}],
            "format": schema,
            "stream": False,
            "options": {"temperature": config.temperature},
        }

        start = time.monotonic()
        # TODO: option-2 hardening — wrap the POST in try/except httpx.HTTPError,
        # log context, and re-raise as a domain-specific ExtractionError so callers
        # can distinguish transport failures from extraction failures.
        response = httpx.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        elapsed = time.monotonic() - start

        # TODO: option-2 hardening — catch (KeyError, json.JSONDecodeError) here,
        # log the raw response body, and raise a clear error; a malformed model
        # reply currently surfaces as an opaque KeyError/JSONDecodeError.
        try:
            data = json.loads(response.json()["message"]["content"])
        except (KeyError, ValueError):
            logger.warning(
                "extract failed to parse response: model=%s prompt_type=%s "
                "status=%s elapsed=%.2fs",
                config.model,
                config.prompt_type,
                response.status_code,
                elapsed,
            )
            raise

        logger.info(
            "extract ok: model=%s prompt_type=%s elapsed=%.2fs fields=%d",
            config.model,
            config.prompt_type,
            elapsed,
            len(data) if isinstance(data, dict) else 0,
        )

        return ExtractionResult(
            data=data,
            model=config.model,
            prompt_type=config.prompt_type,
            duration_seconds=elapsed,
        )
