"""Extractor implementation using Ollama's /api/chat endpoint."""

from __future__ import annotations

import json
import time

import httpx

from spike.prompts import build_prompt
from spike.protocols import ExtractionConfig, ExtractionResult


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

        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt_text}],
            "format": schema,
            "stream": False,
            "options": {"temperature": config.temperature},
        }

        start = time.monotonic()
        response = httpx.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        elapsed = time.monotonic() - start

        data = json.loads(response.json()["message"]["content"])

        return ExtractionResult(
            data=data,
            model=config.model,
            prompt_type=config.prompt_type,
            duration_seconds=elapsed,
        )
