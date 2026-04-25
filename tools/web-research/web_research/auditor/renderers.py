"""Renderer classes for audit signals."""

from __future__ import annotations

import typing
from dataclasses import asdict

import yaml

from web_research.auditor.signals import AuditSignals


class SignalsRenderer(typing.Protocol):
    def render(self, signals: AuditSignals) -> str:
        ...


class YAMLRenderer:
    def render(self, signals: AuditSignals) -> str:
        data = asdict(signals)
        if data["most_recent_fetch"] is not None:
            data["most_recent_fetch"] = data["most_recent_fetch"].isoformat()
        if data["oldest_fetch"] is not None:
            data["oldest_fetch"] = data["oldest_fetch"].isoformat()
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)


class ProseRenderer:
    def render(self, signals: AuditSignals) -> str:
        query = signals.query
        count = signals.result_count
        sources = signals.sources

        if sources:
            source_list = ", ".join(sources)
            sentence1 = (
                f"Research on '{query}': {count} entries "
                f"from {len(sources)} sources ({source_list})."
            )
        else:
            sentence1 = f"Research on '{query}': {count} entries."

        if signals.most_recent_fetch is not None and signals.oldest_fetch is not None:
            oldest = signals.oldest_fetch.isoformat()
            most_recent = signals.most_recent_fetch.isoformat()
            sentence2 = f" Oldest fetch: {oldest}. Most recent fetch: {most_recent}."
        else:
            sentence2 = ""

        return sentence1 + sentence2
