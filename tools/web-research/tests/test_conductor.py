"""Tests for web_research.conductor (Phase 3.6)."""

from __future__ import annotations

import pytest

from collections import deque

from web_research.auditor.model_checker import SufficiencyVerdict
from web_research.conductor import (
    IterationResult,
    ResearchResult,
    _emit_session_end,
    _enqueue_recommended_queries,
    _stop_reason_after_audit,
    _stop_reason_at_loop_exit,
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

    def test_queue_exhausts_when_follow_up_finds_nothing_and_no_more_recommendations(self):
        # q2 returns no URLs; its audit has no further recommendations → queue drains naturally
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q2"]),
                _verdict(sufficient=False, recommended_queries=[]),
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

    def test_falls_back_to_second_recommended_when_first_yields_nothing(self):
        # q_fail returns no URLs but q_ok (second recommendation) does — loop should try q_ok
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q_fail", "q_ok"]),
                _verdict(sufficient=False, recommended_queries=[]),
                _verdict(sufficient=True),
            ]
        )
        search = FakeSearchAndExtract({"q": ["u1"], "q_fail": [], "q_ok": ["u3"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                queue_width=2,
                max_iterations=5,
            )
        )

        assert len(results) == 3
        assert [r.query_used for r in results] == ["q", "q_fail", "q_ok"]
        assert results[2].verdict is not None
        assert results[2].verdict.sufficient is True

    def test_max_iterations_caps_growing_queue(self):
        # Each verdict recommends 2 queries; without the cap the queue would keep growing
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q2", "q3"]),
                _verdict(sufficient=False, recommended_queries=["q4", "q5"]),
                _verdict(sufficient=False, recommended_queries=["q6", "q7"]),
            ]
        )
        search = FakeSearchAndExtract(
            {k: [f"u{i}"] for i, k in enumerate(["q", "q2", "q3", "q4", "q5", "q6", "q7"])}
        )

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                queue_width=2,
                max_iterations=3,
            )
        )

        assert len(results) == 3
        assert [r.query_used for r in results] == ["q", "q2", "q3"]

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

    def test_queue_width_uses_first_recommended(self):
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
                queue_width=1,
                max_iterations=5,
            )
        )

        assert len(results) == 2
        assert [r.query_used for r in results] == ["q", "q_a"]
        assert results[1].verdict is not None
        assert results[1].verdict.sufficient is True

    def test_duplicate_recommendation_does_not_consume_queue_slot(self):
        # queue_width caps *enqueued* queries, not candidates examined:
        # "q" (a duplicate) is skipped and q2/q3 both get their slot
        auditor = FakeAuditor(
            [
                _verdict(sufficient=False, recommended_queries=["q", "q2", "q3"]),
                _verdict(sufficient=False, recommended_queries=[]),
                _verdict(sufficient=False, recommended_queries=[]),
            ]
        )
        search = FakeSearchAndExtract({"q": ["u1"], "q2": ["u2"], "q3": ["u3"]})

        results = list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                queue_width=2,
                max_iterations=5,
            )
        )

        assert [r.query_used for r in results] == ["q", "q2", "q3"]

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


class FakeEventLog:
    def __init__(self):
        self.events: list[dict] = []

    def emit(self, event: dict) -> None:
        self.events.append(event)

    def of_type(self, name: str) -> list[dict]:
        return [e for e in self.events if e["event"] == name]


# Stop-reason taxonomy — the session_end vocabulary the event log records.
# Where a string already exists in conductor.py log messages or verdict
# fields, the reason reuses it so both trails tell the same story.
STOP_SUFFICIENT = "sufficient"
STOP_AUDIT_FAILED = "audit_failed"
STOP_QUEUE_EXHAUSTED = "queue_exhausted"
STOP_MAX_ITERATIONS = "max_iterations"
STOP_NO_AUDITOR = "single_pass"
STOP_ABANDONED = "abandoned"
STOP_ERROR = "error"


class TestEventLog:
    def _run(self, auditor, search, events, **kwargs):
        return list(
            iterate(
                "q",
                search_and_extract=search,
                auditor=auditor,
                events=events,
                **kwargs,
            )
        )

    def test_session_start_carries_run_parameters(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([_verdict(sufficient=True)]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
            max_iterations=3,
            queue_width=2,
        )
        (start,) = events.of_type("session_start")
        assert start["query"] == "q"
        assert start["max_iterations"] == 3
        assert start["queue_width"] == 2

    def test_sufficient_run_emits_full_lifecycle_in_order(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([_verdict(sufficient=True, confidence="high")]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
        )
        assert [e["event"] for e in events.events] == [
            "session_start",
            "iteration_start",
            "extract_complete",
            "audit_verdict",
            "session_end",
        ]
        verdict = events.of_type("audit_verdict")[0]
        assert verdict["sufficient"] is True
        assert verdict["confidence"] == "high"
        assert verdict["audit_failed"] is False
        assert events.of_type("extract_complete")[0]["new_urls"] == ["u1"]

    def test_query_enqueued_emitted_per_accepted_recommendation(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor(
                [
                    _verdict(sufficient=False, recommended_queries=["q2", "q3"]),
                    _verdict(sufficient=True),
                ]
            ),
            FakeSearchAndExtract({"q": ["u1"], "q2": ["u2"]}),
            events,
            queue_width=2,
        )
        assert [e["query"] for e in events.of_type("query_enqueued")] == ["q2", "q3"]

    def test_audit_failure_verdict_event_has_null_fields(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([RuntimeError("model unreachable")]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
        )
        verdict = events.of_type("audit_verdict")[0]
        assert verdict["audit_failed"] is True
        assert verdict["sufficient"] is None
        assert verdict["confidence"] is None
        assert verdict["recommended_queries"] == []

    def test_session_end_is_always_last(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([_verdict(sufficient=True)]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
        )
        assert events.events[-1]["event"] == "session_end"
        assert "stop_reason" in events.events[-1]
        assert "iterations_run" in events.events[-1]

    def test_abandoned_generator_still_emits_session_end(self):
        events = FakeEventLog()
        gen = iterate(
            "q",
            search_and_extract=FakeSearchAndExtract({"q": ["u1"]}),
            auditor=FakeAuditor(
                [_verdict(sufficient=False, recommended_queries=["q2"])]
            ),
            events=events,
        )
        next(gen)  # consume one result, then walk away
        gen.close()
        assert events.events[-1]["event"] == "session_end"

    # ---- stop-reason taxonomy (assertions come alive once the TODOs above
    # ---- and the matching sites in conductor.py are filled in)

    def test_stop_reason_sufficient(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([_verdict(sufficient=True)]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
        )
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_SUFFICIENT

    def test_stop_reason_audit_failed(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([RuntimeError("boom")]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
        )
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_AUDIT_FAILED

    def test_stop_reason_queue_exhausted(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor([_verdict(sufficient=False, recommended_queries=[])]),
            FakeSearchAndExtract({"q": ["u1"]}),
            events,
            max_iterations=5,
        )
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_QUEUE_EXHAUSTED

    def test_stop_reason_max_iterations(self):
        events = FakeEventLog()
        self._run(
            FakeAuditor(
                [
                    _verdict(sufficient=False, recommended_queries=["q2"]),
                    _verdict(sufficient=False, recommended_queries=["q3"]),
                ]
            ),
            FakeSearchAndExtract({"q": ["u1"], "q2": ["u2"]}),
            events,
            max_iterations=2,
        )
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_MAX_ITERATIONS

    def test_stop_reason_no_auditor(self):
        events = FakeEventLog()
        self._run(None, FakeSearchAndExtract({"q": ["u1"]}), events)
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_NO_AUDITOR

    def test_stop_reason_abandoned(self):
        events = FakeEventLog()
        gen = iterate(
            "q",
            search_and_extract=FakeSearchAndExtract({"q": ["u1"]}),
            auditor=FakeAuditor(
                [_verdict(sufficient=False, recommended_queries=["q2"])]
            ),
            events=events,
        )
        next(gen)
        gen.close()
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_ABANDONED

    def test_stop_reason_error_when_pipeline_raises(self):
        def exploding_search(query, **kwargs):
            raise RuntimeError("fetch blew up")

        events = FakeEventLog()
        with pytest.raises(RuntimeError):
            list(
                iterate(
                    "q",
                    search_and_extract=exploding_search,
                    auditor=FakeAuditor([_verdict(sufficient=True)]),
                    events=events,
                )
            )
        assert events.of_type("session_end")[0]["stop_reason"] == STOP_ERROR


class TestStopReasonHelpers:
    def test_audit_failed_wins(self):
        assert _stop_reason_after_audit(None, True, 0) == STOP_AUDIT_FAILED

    def test_sufficient_verdict_stops(self):
        assert (
            _stop_reason_after_audit(_verdict(sufficient=True), False, 0)
            == STOP_SUFFICIENT
        )

    def test_insufficient_verdict_continues(self):
        assert _stop_reason_after_audit(_verdict(sufficient=False), False, 0) is None

    def test_empty_queue_is_exhausted(self):
        assert _stop_reason_at_loop_exit(deque(), 2, 5) == STOP_QUEUE_EXHAUSTED

    def test_nonempty_queue_means_max_iterations(self):
        assert _stop_reason_at_loop_exit(deque(["q2"]), 5, 5) == STOP_MAX_ITERATIONS


class TestEnqueueRecommendedQueries:
    def _enqueue(self, recommended, seen, queue_width=2):
        pending: deque[str] = deque()
        events = FakeEventLog()
        _enqueue_recommended_queries(
            _verdict(sufficient=False, recommended_queries=recommended),
            pending,
            seen,
            queue_width,
            events,
            iteration=0,
        )
        return pending, seen, events

    def test_none_verdict_is_noop(self):
        pending: deque[str] = deque()
        _enqueue_recommended_queries(None, pending, {"q"}, 2, FakeEventLog(), 0)
        assert not pending

    def test_caps_enqueued_not_candidates_examined(self):
        # the duplicate must not burn a slot — q2 and q3 both make it in
        pending, seen, events = self._enqueue(["q", "q2", "q3"], {"q"}, queue_width=2)
        assert list(pending) == ["q2", "q3"]
        assert seen == {"q", "q2", "q3"}
        assert [e["query"] for e in events.of_type("query_enqueued")] == ["q2", "q3"]

    def test_respects_queue_width(self):
        pending, _, _ = self._enqueue(["q2", "q3", "q4"], {"q"}, queue_width=2)
        assert list(pending) == ["q2", "q3"]


class TestEmitSessionEnd:
    def test_no_exception_keeps_stop_reason(self):
        events = FakeEventLog()
        _emit_session_end(events, STOP_SUFFICIENT, 1, (None, None, None))
        assert events.events[0]["stop_reason"] == STOP_SUFFICIENT
        assert events.events[0]["iterations_run"] == 1

    def test_generator_exit_stays_abandoned(self):
        events = FakeEventLog()
        _emit_session_end(events, STOP_ABANDONED, 1, (GeneratorExit, GeneratorExit(), None))
        assert events.events[0]["stop_reason"] == STOP_ABANDONED

    def test_other_exception_overrides_to_error(self):
        events = FakeEventLog()
        exc = RuntimeError("boom")
        _emit_session_end(events, STOP_ABANDONED, 1, (RuntimeError, exc, None))
        assert events.events[0]["stop_reason"] == STOP_ERROR


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
