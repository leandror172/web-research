"""MCP server exposing web-research tools to Claude Code.

Three tools:
  research_url    — fetch + extract a single URL (cached if already known)
  search_topic    — search the web and extract top results
  query_knowledge — query the local SQLite knowledge store
"""

from __future__ import annotations

import contextlib
import io
from typing import Any

from mcp.server.fastmcp import FastMCP

from web_research.cli import extract_single_url, search_and_extract
from web_research.knowledge.store import KnowledgeStore

mcp = FastMCP("web-research")

_store = KnowledgeStore()


@contextlib.contextmanager
def _quiet():
    """Suppress stdout from CLI functions (they print progress, not data)."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


@mcp.tool()
def research_url(url: str, focus: str | None = None) -> dict[str, Any]:
    """Fetch and extract structured knowledge from a URL.

    Returns cached result immediately if the URL is already in the knowledge
    store. Otherwise fetches, extracts via Ollama, saves, and returns the result.

    Args:
        url:   The URL to research.
        focus: Optional focus topic (e.g. "rate limiting"). When provided,
               uses the focused extraction prompt instead of open extraction.
    """
    if _store.has_url(url):
        results = _store.query(url, limit=1)
        return results[0] if results else {"url": url, "cached": True}

    prompt_type = "focused" if focus else "open"
    with _quiet():
        extract_single_url(url=url, focus=focus, prompt_type=prompt_type, store=_store)

    results = _store.query(url, limit=1)
    return results[0] if results else {"url": url, "status": "saved"}


@mcp.tool()
def search_topic(query: str, top: int = 3) -> list[dict[str, Any]]:
    """Search the web for a topic and extract from top results.

    Already-known URLs are skipped (deduped via knowledge store). Results
    are saved to the store and returned as structured dicts.

    Args:
        query: Search query string.
        top:   Number of usable results to extract (default 3).
    """
    with _quiet():
        search_and_extract(query=query, top=top, store=_store)
    return _store.query(query, limit=top)


@mcp.tool()
def query_knowledge(topic: str, limit: int = 10) -> list[dict[str, Any]]:
    """Query the local knowledge store for previously extracted information.

    Searches across URL, query, and extracted data fields.

    Args:
        topic: Topic or keyword to search for.
        limit: Maximum number of results to return (default 10).
    """
    return _store.query(topic, limit=limit)


if __name__ == "__main__":
    mcp.run()
