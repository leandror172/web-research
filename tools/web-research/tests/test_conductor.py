"""Tests for web_research.conductor (Phase 3.6)."""

from __future__ import annotations

from web_research.auditor.model_checker import SufficiencyVerdict
from web_research.conductor import (
    IterationResult,
    ResearchResult,
    iterate,
    research_topic,
)


def _verdict(
    *,
    sufficient: bool = False,
    confidence: str = "medium",
    recommended_queries: list[str] | None = None,
    missing_topics: list[str] | None = None,
    reasoning: str = "r",
) -> SufficiencyVerdict:
    return SufficiencyVerdict(
        sufficient=sufficient,
        confidence=confidence,
        reasoning=reasoning,
        missing_topics=missing_topics or [],
        recommended_queries=recommended_queries or [],
    )


class FakeAuditor:
    def __init__(self, verdicts: list[SufficiencyVerdict | Exception]):
        self.verdicts = list(verdicts)
        self.calls: list[str] = []

    def check(self, query: str) -> SufficiencyVerdict:
        self.calls.append(query)
        if not self.verdicts:
            raise RuntimeError("FakeAuditor: no more scripted verdicts")
        next_item = self.verdicts.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        return next_item


class FakeSearchAndExtract:
    def __init__(self, urls_per_query: dict[str, list[str]]):
        self.urls_per_query = urls_per_query
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, query: str, **kwargs) -> list[str]:
        self.calls.append((query, kwargs))
        return self.urls_per_query.get(query, [])


class TestIterate:
    def test_stops_on_first_sufficient_verdict(self):
        auditor = FakeAuditor([_verdict(sufficient=True)])
        search = FakeSearchAndExtract({"q": ["u1"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                max_iterations=3,
            )
        )

        assert len(results) == 1
        assert isinstance(results[0], IterationResult)
        assert results[0].iteration == 0
        assert results[0].query_used == "q"
        assert results[0].new_urls == ["u1"]
        assert results[0].verdict is not None
        assert results[0].verdict.sufficient is True
        assert results[0].audit_failed is False
        assert auditor.calls == ["q"]
        assert [c[0] for c in search.calls] == ["q"]

    def test_iterates_up_to_max_iterations_when_never_sufficient(self):
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q2"]),
                _verdict(sufficient=False, recommended_queries=["q3"]),
                _verdict(sufficient=False, recommended_queries=["q4"]),
            ]
        )
        search = FakeSearchAndExtract(
            {"q": ["u1"], "q2": ["u2"], "q3": ["u3"]}
        )

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                max_iterations=3,
            )
        )

        assert len(results) == 3
        assert [r.query_used for r in results] == ["q", "q2", "q3"]
        assert [r.iteration for r in results] == [0, 1, 2]
        assert auditor.calls == ["q", "q2", "q3"]
        assert [c[0] for c in search.calls] == ["q", "q2", "q3"]

    def test_stops_when_recommended_queries_empty(self):
        auditor = FakeAuditor(
            [_verdict(sufficient=False, recommended_queries=[])]
        )
        search = FakeSearchAndExtract({"q": ["u1"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                max_iterations=3,
            )
        )

        assert len(results) == 1
        assert results[0].query_used == "q"
        assert results[0].verdict.sufficient is False
        assert results[0].audit_failed is False
        assert auditor.calls == ["q"]
        assert [c[0] for c in search.calls] == ["q"]

    def test_stops_when_iteration_produces_no_new_urls(self):
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q2"]),
                _verdict(sufficient=False, recommended_queries=["q3"]),
            ]
        )
        search = FakeSearchAndExtract({"q": ["u1"], "q2": []})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                max_iterations=5,
            )
        )

        assert len(results) == 2
        assert [r.query_used for r in results] == ["q", "q2"]
        assert [r.new_urls for r in results] == [["u1"], []]
        assert [c[0] for c in search.calls] == ["q", "q2"]

    def test_audit_failure_yields_audit_failed_then_stops(self):
        auditor = FakeAuditor([RuntimeError("model unreachable")])
        search = FakeSearchAndExtract({"q": ["u1"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                max_iterations=3,
            )
        )

        assert len(results) == 1
        assert results[0].new_urls == ["u1"]
        assert results[0].verdict is None
        assert results[0].audit_failed is True
        assert auditor.calls == ["q"]
        assert [c[0] for c in search.calls] == ["q"]

    def test_queries_per_iteration_uses_first_recommended(self):
        auditor = FakeAuditor(
            [
                _verdict(
                    sufficient=False,
                    recommended_queries=["q_a", "q_b"],
                ),
                _verdict(sufficient=True),
            ]
        )
        search = FakeSearchAndExtract({"q": ["u1"], "q_a": ["u2"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                queries_per_iteration=1,
                max_iterations=5,
            )
        )

        assert len(results) == 2
        assert [r.query_used for r in results] == ["q", "q_a"]
        assert results[1].verdict is not None
        assert results[1].verdict.sufficient is True

    def test_no_audit_runs_single_iteration(self):
        search = FakeSearchAndExtract({"q": ["u1"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=None,
                max_iterations=5,
            )
        )

        assert len(results) == 1
        assert results[0].query_used == "q"
        assert results[0].new_urls == ["u1"]
        assert results[0].verdict is None
        assert results[0].audit_failed is False
        assert [c[0] for c in search.calls] == ["q"]


class TestResearchTopic:
    def test_collects_all_iterations_into_result(self):
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q2"]),
                _verdict(sufficient=True),
            ]
        )
        search = FakeSearchAndExtract({"q": ["u1"], "q2": ["u2"]})

        result = research_topic(
            "q",
            search_and_extract=search,
            auditor=auditor,
            max_iterations=3,
        )

        assert isinstance(result, ResearchResult)
        assert result.original_query == "q"
        assert result.iterations_run == 2
        assert len(result.iterations) == 2
        assert result.final_verdict is not None
        assert result.final_verdict.sufficient is True
        assert result.audit_failed is False
        assert [r.query_used for r in result.iterations] == ["q", "q2"]
        assert [r.new_urls for r in result.iterations] == [["u1"], ["u2"]]
