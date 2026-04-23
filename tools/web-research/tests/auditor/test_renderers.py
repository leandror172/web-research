"""Tests for auditor.renderers."""

from __future__ import annotations

import dataclasses
import datetime

import pytest
import yaml

from web_research.auditor.renderers import ProseRenderer, YAMLRenderer
from web_research.auditor.signals import AuditSignals


@pytest.fixture
def sample_signals() -> AuditSignals:
    return AuditSignals(
        query="test search",
        result_count=4,
        sources=["a.com", "b.com", "c.org"],
        most_recent_fetch=datetime.datetime(2023, 1, 5, 0, 0, 0, tzinfo=datetime.timezone.utc),
        oldest_fetch=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    )


class TestYAMLRenderer:
    def test_render_returns_yaml_string(self, sample_signals: AuditSignals):
        result = YAMLRenderer().render(sample_signals)
        assert isinstance(result, str)

    def test_output_is_parseable_by_yaml_safe_load(self, sample_signals: AuditSignals):
        parsed = yaml.safe_load(YAMLRenderer().render(sample_signals))
        assert parsed["query"] == "test search"
        assert parsed["result_count"] == 4
        assert parsed["sources"] == ["a.com", "b.com", "c.org"]
        assert parsed["most_recent_fetch"] == "2023-01-05T00:00:00+00:00"
        assert parsed["oldest_fetch"] == "2023-01-01T00:00:00+00:00"

    def test_none_datetimes_become_yaml_null(self):
        signals = AuditSignals(
            query="test",
            result_count=0,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        parsed = yaml.safe_load(YAMLRenderer().render(signals))
        assert parsed["most_recent_fetch"] is None
        assert parsed["oldest_fetch"] is None

    def test_sources_list_preserved_in_order(self):
        signals = AuditSignals(
            query="test",
            result_count=0,
            sources=["z.org", "a.com", "b.net"],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        parsed = yaml.safe_load(YAMLRenderer().render(signals))
        assert parsed["sources"] == ["z.org", "a.com", "b.net"]

    def test_query_string_included_verbatim(self):
        signals = AuditSignals(
            query="special chars: & $ @",
            result_count=0,
            sources=[],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        parsed = yaml.safe_load(YAMLRenderer().render(signals))
        assert parsed["query"] == "special chars: & $ @"


class TestProseRenderer:
    def test_output_contains_query(self, sample_signals: AuditSignals):
        result = ProseRenderer().render(sample_signals)
        assert "test search" in result

    def test_output_contains_result_count(self, sample_signals: AuditSignals):
        result = ProseRenderer().render(sample_signals)
        assert "4 entries" in result

    def test_output_lists_all_sources(self, sample_signals: AuditSignals):
        result = ProseRenderer().render(sample_signals)
        assert "a.com" in result
        assert "b.com" in result
        assert "c.org" in result

    def test_empty_sources_omits_source_list(self, sample_signals: AuditSignals):
        signals = dataclasses.replace(sample_signals, sources=[])
        result = ProseRenderer().render(signals)
        assert "from" not in result.lower() or "sources" not in result.lower()

    def test_none_datetimes_no_fetch_dates(self):
        signals = AuditSignals(
            query="test",
            result_count=2,
            sources=["example.com"],
            most_recent_fetch=None,
            oldest_fetch=None,
        )
        result = ProseRenderer().render(signals)
        assert "fetch" not in result.lower()

    def test_with_datetimes_includes_iso_formatted_times(self, sample_signals: AuditSignals):
        result = ProseRenderer().render(sample_signals)
        assert "2023-01-01T00:00:00+00:00" in result
        assert "2023-01-05T00:00:00+00:00" in result
