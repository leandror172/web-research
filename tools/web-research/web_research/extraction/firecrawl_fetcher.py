"""Fetcher implementation using Firecrawl CLI."""

import json
import subprocess

from web_research.extraction.protocols import FetchResult


class FirecrawlFetcher:
    """Fetches JS-rendered HTML from a URL using the Firecrawl CLI."""

    def __init__(self, timeout: float = 60.0):
        self._timeout = timeout

    def fetch(self, url: str) -> FetchResult:
        result = subprocess.run(
            ["firecrawl", "scrape", url, "--format", "html", "--json"],
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Firecrawl scrape failed: {result.stderr.strip()}")

        json_start = result.stdout.find("{")
        if json_start == -1:
            raise ValueError("No valid JSON found in Firecrawl output")

        data = json.loads(result.stdout[json_start:])

        return FetchResult(
            url=url,
            html=data.get("html", ""),
            status_code=data.get("metadata", {}).get("statusCode", 200),
            content_type=data.get("metadata", {}).get("contentType"),
        )
