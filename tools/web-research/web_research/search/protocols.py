"""Protocols and data types for the search pipeline.

Each protocol defines a single boundary in the pipeline:
    SearchEngine → SearchResultWriter

Components are independently callable. A Dispatcher agent can compose
them in any order, choosing implementations via parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


# ---------------------------------------------------------------------------
# Data types flowing between components
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single result from a search query."""

    url: str
    title: str
    description: str
    position: int


# ---------------------------------------------------------------------------
# Protocols (contracts — implementations satisfy these structurally)
# ---------------------------------------------------------------------------


class SearchEngine(Protocol):
    """Performs web searches and returns structured results."""

    def search(self, query: str, limit: int = 5) -> list[SearchResult]: ...
