"""Signal processing for audit of web research results."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class AuditSignals:
    query: str
    result_count: int
    sources: list[str]
    most_recent_fetch: datetime.datetime | None
    oldest_fetch: datetime.datetime | None


class HeuristicChecker:
    def __init__(self, min_results: int = 2) -> None:
        self._min_results = min_results

    def compute(self, query: str, entries: list[dict[str, Any]]) -> AuditSignals:
        result_count = len(entries)
        sources = sorted(
            {urlparse(entry["url"]).netloc for entry in entries if "url" in entry}
        )
        timestamps = [
            datetime.datetime.fromisoformat(entry["extracted_at"])
            for entry in entries
            if "extracted_at" in entry
        ]
        most_recent_fetch = max(timestamps) if timestamps else None
        oldest_fetch = min(timestamps) if timestamps else None

        return AuditSignals(
            query=query,
            result_count=result_count,
            sources=sources,
            most_recent_fetch=most_recent_fetch,
            oldest_fetch=oldest_fetch,
        )

    def obviously_insufficient(self, signals: AuditSignals) -> bool:
        return signals.result_count < self._min_results
