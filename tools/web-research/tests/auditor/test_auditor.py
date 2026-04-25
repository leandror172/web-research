"""Tests for the Auditor orchestrator (cascade)."""

from __future__ import annotations

import pytest

from web_research.auditor.auditor import Auditor
from web_research.auditor.model_checker import SufficiencyVerdict
from web_research.auditor.signals import AuditSignals, HeuristicChecker


class _StubStore:
    def __init__(self, entries: list[dict]):
        self._entries = entries
        self.query_calls: list[str] = []

    def query(self, topic: str, limit: int = 10) -> list[dict]:
        self.query_calls.append(topic)
        return self._entries


class _StubModelChecker:
    def __init__(self, verdict: SufficiencyVerdict):
        self._verdict = verdict
        self.called_with: tuple | None = None

    def check(self, signals: AuditSignals, entries: list[dict]) -> SufficiencyVerdict:
        self.called_with = (signals, entries)
        return self._verdict


@pytest.fixture
def rich_verdict() -> SufficiencyVerdict:
    return SufficiencyVerdict(
        sufficient=True,
        confidence="high",
        reasoning="model says yes",
        missing_topics=[],
        recommended_queries=[],
    )


class TestCheck:
    def test_heuristic_gate_skips_model_when_obviously_insufficient(self, rich_verdict):
        store = _StubStore(entries=[])
        model = _StubModelChecker(verdict=rich_verdict)
        auditor = Auditor(heuristic=HeuristicChecker(), model=model, store=store)

        verdict = auditor.check("some query")

        assert verdict.sufficient is False
        assert model.called_with is None

    def test_escalates_to_model_when_not_obviously_insufficient(self, rich_verdict):
        entries = [
            {"url": "https://example.com/a", "extracted_at": "2023-01-01T00:00:00+00:00"},
            {"url": "https://other.org/b", "extracted_at": "2023-01-02T00:00:00+00:00"},
        ]
        store = _StubStore(entries=entries)
        model = _StubModelChecker(verdict=rich_verdict)
        auditor = Auditor(heuristic=HeuristicChecker(), model=model, store=store)

        verdict = auditor.check("some query")

        assert verdict is rich_verdict
        assert model.called_with is not None
        signals, passed_entries = model.called_with
        assert signals.query == "some query"
        assert signals.result_count == 2
        assert passed_entries == entries

    def test_queries_store_with_the_query_string(self, rich_verdict):
        store = _StubStore(entries=[])
        model = _StubModelChecker(verdict=rich_verdict)
        auditor = Auditor(heuristic=HeuristicChecker(), model=model, store=store)

        auditor.check("my topic")

        assert store.query_calls == ["my topic"]

    def test_gate_verdict_includes_result_count_in_reasoning(self, rich_verdict):
        store = _StubStore(entries=[{"url": "https://x.com", "extracted_at": "2023-01-01T00:00:00+00:00"}])
        model = _StubModelChecker(verdict=rich_verdict)
        auditor = Auditor(
            heuristic=HeuristicChecker(min_results=2),
            model=model,
            store=store,
        )

        verdict = auditor.check("q")

        assert "1" in verdict.reasoning
