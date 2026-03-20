"""Protocols and data types for the extraction spike.

Each protocol defines a single boundary in the extraction pipeline:
    Fetcher  →  Cleaner  →  Extractor  →  OutputWriter

Components are independently callable. A Dispatcher agent can compose
them in any order, choosing implementations via parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# Data types flowing between components
# ---------------------------------------------------------------------------


@dataclass
class FetchResult:
    """Raw content retrieved from a URL."""

    url: str
    html: str
    status_code: int
    content_type: str | None = None


@dataclass
class CleanResult:
    """Cleaned text extracted from raw HTML."""

    text: str
    links: list[str] = field(default_factory=list)


@dataclass
class ExtractionConfig:
    """Parameters controlling a single extraction call."""

    model: str = "qwen3.5:9b"
    prompt_type: str = "open"       # "open" or "focused"
    focus: str | None = None        # required when prompt_type="focused"
    temperature: float = 0.1


@dataclass
class ExtractionResult:
    """Structured data produced by a model extraction."""

    data: dict
    model: str
    duration_seconds: float


# ---------------------------------------------------------------------------
# Protocols (contracts — implementations satisfy these structurally)
# ---------------------------------------------------------------------------


class Fetcher(Protocol):
    """Retrieves raw HTML from a URL."""

    def fetch(self, url: str) -> FetchResult: ...


class Cleaner(Protocol):
    """Converts raw HTML into clean text suitable for LLM consumption."""

    def clean(self, html: str) -> CleanResult: ...


class Extractor(Protocol):
    """Sends text to a model and returns structured extraction."""

    def extract(self, text: str, config: ExtractionConfig) -> ExtractionResult: ...


class OutputWriter(Protocol):
    """Persists extraction results."""

    def save(self, url: str, clean: CleanResult, extraction: ExtractionResult) -> str:
        """Returns the path where results were saved."""
        ...
