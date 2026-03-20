"""Fetcher implementation using httpx."""

import httpx

from spike.protocols import FetchResult


class HttpxFetcher:
    """Fetches raw HTML from a URL using httpx."""

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    def fetch(self, url: str) -> FetchResult:
        response = httpx.get(
            url,
            timeout=self._timeout,
            follow_redirects=True,
            headers={"User-Agent": "web-research-spike/0.1"},
        )
        return FetchResult(
            url=url,
            html=response.text,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
        )
