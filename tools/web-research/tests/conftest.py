"""Shared fixtures for web_research test suite."""

from __future__ import annotations

import pytest

from web_research.extraction.protocols import CleanResult, ExtractionResult


@pytest.fixture
def sample_clean() -> CleanResult:
    return CleanResult(
        text="Sample content about Python web scraping.",
        links=["https://example.com", "https://docs.python.org"],
    )


@pytest.fixture
def sample_extraction() -> ExtractionResult:
    return ExtractionResult(
        data={
            "name": "SomeTool",
            "summary": "A web scraping tool",
            "key_features": ["fast", "clean"],
            "use_cases": ["research", "monitoring"],
            "technical_details": {"language": "Python"},
            "links": [{"url": "https://example.com", "text": "Docs"}],
            "limitations": ["no JS support"],
        },
        model="qwen3:14b",
        prompt_type="open",
        duration_seconds=2.5,
    )


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test.db")
