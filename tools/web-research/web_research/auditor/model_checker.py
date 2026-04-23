"""Model-based sufficiency checker for web research audits."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

import httpx

from web_research.auditor.signals import AuditSignals


SUFFICIENCY_SCHEMA = {
    "type": "object",
    "required": ["sufficient", "confidence", "reasoning", "missing_topics", "recommended_queries"],
    "properties": {
        "sufficient": {"type": "boolean"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "reasoning": {"type": "string"},
        "missing_topics": {"type": "array", "items": {"type": "string"}},
        "recommended_queries": {"type": "array", "items": {"type": "string"}},
    },
}


@dataclass(frozen=True)
class SufficiencyVerdict:
    sufficient: bool
    confidence: str
    reasoning: str
    missing_topics: list[str]
    recommended_queries: list[str]


class ModelChecker:
    def __init__(
        self,
        model: str,
        template_path: pathlib.Path,
        renderer,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._template_path = template_path
        self._renderer = renderer
        self._base_url = base_url

    def check(self, signals: AuditSignals, entries: list[dict]) -> SufficiencyVerdict:
        template = self._template_path.read_text()
        rendered_signals = self._renderer.render(signals)
        rendered_entries = "\n".join(
            f"- {entry['url']}\n  {json.dumps(entry.get('data', entry))}"
            for entry in entries
        )

        filled_prompt = template.format(
            query=signals.query,
            signals=rendered_signals,
            entries=rendered_entries,
        )

        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": filled_prompt}],
            "format": SUFFICIENCY_SCHEMA,
            "stream": False,
        }

        response = httpx.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        data = json.loads(response.json()["message"]["content"])

        return SufficiencyVerdict(
            sufficient=data["sufficient"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            missing_topics=data["missing_topics"],
            recommended_queries=data["recommended_queries"],
        )
