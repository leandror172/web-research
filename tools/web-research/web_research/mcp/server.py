"""MCP server exposing web-research tools to Claude Code.

Three tools:
  research_url    — fetch + extract a single URL (cached if already known)
  search_topic    — iterative research loop driven by Auditor verdicts
  query_knowledge — query the local SQLite knowledge store
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
from typing import Any

from mcp.server.fastmcp import FastMCP

from web_research.cli import extract_single_url, search_and_extract
from web_research.conductor import ResearchResult, build_default_auditor, research_topic
from web_research.knowledge.store import KnowledgeStore

mcp = FastMCP("web-research")

_store = KnowledgeStore()
_auditor = build_default_auditor(_store)


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


def _search_and_extract_fn(query: str, **kwargs) -> list[str]:
    """Thin wrapper so Conductor gets new_urls while stdout is suppressed."""
    with _quiet():
        return search_and_extract(query=query, **kwargs)


def _result_to_dict(result: ResearchResult) -> dict[str, Any]:
    """Serialize ResearchResult to MCP return dict.

    Two-pass collection: (1) query store by original query (catches cached
    hits from iteration 1); (2) query by URL for any new URLs from follow-up
    iterations (which may not match the original query string). Deduped by URL.
    """
    verdict = dataclasses.asdict(result.final_verdict) if result.final_verdict else None

    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    # Pass 1: original query — catches cached entries from iteration 1
    for row in _store.query(result.original_query, limit=20):
        url = row.get("url", "")
        if url not in seen:
            seen.add(url)
            results.append(row)

    # Pass 2: new URLs from follow-up iterations not covered by pass 1
    for url in (url for it in result.iterations for url in it.new_urls):
        if url not in seen:
            seen.add(url)
            rows = _store.query(url, limit=1)
            if rows:
                results.append(rows[0])

    return {
        "query": result.original_query,
        "iterations_run": result.iterations_run,
        "verdict": verdict,
        "audit_failed": result.audit_failed,
        "results": results,
    }


@mcp.tool()
def search_topic(query: str, top: int = 3, max_iterations: int = 3) -> dict[str, Any]:
    """Research a topic iteratively, stopping when knowledge is sufficient.

    Runs one or more rounds of search+extract driven by the Auditor. Each
    round may follow up with a recommended query if the current knowledge is
    insufficient. Returns the final verdict and all accumulated results.

    Args:
        query:          Search query string.
        top:            Usable results to extract per iteration (default 3).
        max_iterations: Maximum research rounds before stopping (default 3).
    """
    result = research_topic(
        query,
        search_and_extract=_search_and_extract_fn,
        auditor=_auditor,
        max_iterations=max_iterations,
        store=_store,
        top=top,
    )
    return _result_to_dict(result)


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
