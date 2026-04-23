"""Tests for auditor.signals."""

from __future__ import annotations

import datetime
from typing import Any

import pytest

from web_research.auditor.signals import AuditSignals, HeuristicChecker


class TestAuditSignals:
    def test_is_frozen(self):
        signals = AuditSignals(
            query="test",
            result_count=0,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        with pytest.raises(Exception, match="cannot assign"):
            signals.query = "new"


class TestCompute:
    def test_empty_entries_returns_zero_results(self):
        checker = HeuristicChecker()
        signals = checker.compute("test query", [])
        assert signals.result_count == 0
        assert signals.sources == []
        assert signals.most_recent_fetch is None
        assert signals.oldest_fetch is None

    def test_extracts_unique_domains(self):
        entries = [
            {"url": "https://example.com/a", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://example.com/b", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://other.org/c", "extracted_at": "2023-01-01T00:00:00+00:00"},
        ]
        checker = HeuristicChecker()
        signals = checker.compute("test query", entries)
        assert set(signals.sources) == {"example.com", "other.org"}

    def test_sorts_sources_alphabetically(self):
        entries = [
            {"url": "https://z.com/a", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://a.com/b", "extracted_at": "2023-01-01T00:00:00+00:00"},
        ]
        checker = HeuristicChecker()
        signals = checker.compute("test query", entries)
        assert signals.sources == ["a.com", "z.com"]

    def test_sets_most_recent_fetch(self):
        entries = [
            {"url": "https://example.com/a", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://example.com/b", "extracted_at": "2023-01-02T00:00:00+00:00"},
        ]
        checker = HeuristicChecker()
        signals = checker.compute("test query", entries)
        expected = datetime.datetime(2023, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc)
        assert signals.most_recent_fetch == expected

    def test_sets_oldest_fetch(self):
        entries = [
            {"url": "https://example.com/a", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://example.com/b", "extracted_at": "2023-01-02T00:00:00+00:00"},
        ]
        checker = HeuristicChecker()
        signals = checker.compute("test query", entries)
        expected = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        assert signals.oldest_fetch == expected

    def test_preserves_query(self):
        entries: list[dict[str, Any]] = []
        checker = HeuristicChecker()
        signals = checker.compute("search term", entries)
        assert signals.query == "search term"


class TestObviouslyInsufficient:
    def test_returns_true_when_result_count_zero(self):
        signals = AuditSignals(
            query="test",
            result_count=0,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        checker = HeuristicChecker()
        assert checker.obviously_insufficient(signals)

    def test_returns_true_when_result_count_one(self):
        signals = AuditSignals(
            query="test",
            result_count=1,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        checker = HeuristicChecker()
        assert checker.obviously_insufficient(signals)

    def test_returns_false_when_result_count_two(self):
        signals = AuditSignals(
            query="test",
            result_count=2,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        checker = HeuristicChecker()
        assert not checker.obviously_insufficient(signals)

    def test_returns_false_when_result_count_ten(self):
        signals = AuditSignals(
            query="test",
            result_count=10,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        checker = HeuristicChecker()
        assert not checker.obviously_insufficient(signals)

    def test_configurable_min_results(self):
        signals = AuditSignals(
            query="test",
            result_count=4,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        checker = HeuristicChecker(min_results=5)
        assert checker.obviously_insufficient(signals)
