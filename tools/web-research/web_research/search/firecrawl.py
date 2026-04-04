"""Firecrawl search engine implementation."""

from __future__ import annotations

import json
import subprocess

from web_research.search.protocols import SearchResult


class FirecrawlSearchEngine:
    """Performs web searches using the Firecrawl CLI."""

    def __init__(self, timeout: float = 60.0):
        self._timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search the web via `firecrawl search` and return structured results."""
        result = subprocess.run(
            ["firecrawl", "search", query, "--limit", str(limit), "--json"],
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Firecrawl search failed: {result.stderr}")

        data = json.loads(result.stdout)

        if not data.get("success"):
            raise RuntimeError(f"Firecrawl search failed: {data.get('error')}")

        return [
            SearchResult(
                url=item["url"],
                title=item.get("title", ""),
                description=item.get("description", ""),
                position=item.get("position", i + 1),
            )
            for i, item in enumerate(data["data"]["web"])
        ]
