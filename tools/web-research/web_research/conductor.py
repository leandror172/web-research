"""Conductor — iterative research loop driven by Auditor verdicts.

Sits above the search/extract pipeline. Runs one round of search+extract,
asks the Auditor whether knowledge is sufficient, and (if not) takes the
Auditor's first recommended follow-up query for the next round.
"""

from __future__ import annotations

import itertools
import logging
import pathlib
import sys
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from web_research.auditor.auditor import Auditor
from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict
from web_research.auditor.renderers import YAMLRenderer
from web_research.auditor.signals import HeuristicChecker
from web_research.events import EventLog, NullEventLog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IterationResult:
    iteration: int
    query_used: str
    new_urls: list[str]
    verdict: SufficiencyVerdict | None = None
    audit_failed: bool = False


@dataclass(frozen=True)
class ResearchResult:
    original_query: str
    iterations: tuple[IterationResult, ...] = field(default_factory=tuple)
    final_verdict: SufficiencyVerdict | None = None
    audit_failed: bool = False

    @property
    def iterations_run(self) -> int:
        return len(self.iterations)


def build_default_auditor(store) -> Auditor:
    """Build the standard production Auditor wired to the given store."""
    heuristic = HeuristicChecker()
    template_path = (
        pathlib.Path(__file__).parent / "auditor" / "prompts" / "sufficiency.md"
    )
    model_checker = ModelChecker(
        model="qwen3:14b",
        template_path=template_path,
        renderer=YAMLRenderer(),
    )
    return Auditor(heuristic=heuristic, model=model_checker, store=store)


def _audit(query: str, auditor) -> tuple[SufficiencyVerdict | None, bool]:
    """Returns (verdict, audit_failed). audit_failed=True iff auditor raised."""
    if auditor is None:
        return None, False
    try:
        return auditor.check(query), False
    except Exception as exc:
        logger.warning("Auditor check failed for query '%s': %s", query, exc)
        return None, True


def _emit_session_start(
    events: EventLog, query: str, max_iterations: int, queue_width: int
) -> None:
    events.emit(
        {
            "event": "session_start",
            "query": query,
            "max_iterations": max_iterations,
            "queue_width": queue_width,
        }
    )


def _run_search_step(
    current_query: str, search_and_extract, events: EventLog, iteration: int,
    **search_kwargs: Any,
) -> list[str]:
    events.emit(
        {"event": "iteration_start", "iteration": iteration, "query": current_query}
    )
    new_urls = search_and_extract(current_query, **search_kwargs)
    events.emit(
        {"event": "extract_complete", "iteration": iteration, "new_urls": new_urls}
    )
    return new_urls


def _run_audit_step(
    current_query: str, auditor, events: EventLog, iteration: int,
    on_pre_audit: Callable[[str], None] | None,
) -> tuple[SufficiencyVerdict | None, bool]:
    if on_pre_audit is not None:
        on_pre_audit(current_query)
    verdict, audit_failed = _audit(current_query, auditor)
    events.emit(
        {
            "event": "audit_verdict",
            "iteration": iteration,
            "audit_failed": audit_failed,
            "sufficient": verdict.sufficient if verdict else None,
            "confidence": verdict.confidence if verdict else None,
            "recommended_queries": (
                list(verdict.recommended_queries) if verdict else []
            ),
        }
    )
    return verdict, audit_failed


def _stop_reason_after_audit(
    verdict: SufficiencyVerdict | None, audit_failed: bool, iteration: int
) -> str | None:
    """None means: keep iterating."""
    if audit_failed:
        logger.info("stop[%d]: audit failed", iteration)
        return "audit_failed"
    if verdict is not None and verdict.sufficient:
        logger.info("stop[%d]: sufficient=True confidence=%s", iteration, verdict.confidence)
        return "sufficient"
    return None


def _stop_reason_at_loop_exit(
    pending: deque[str], iteration: int, max_iterations: int
) -> str:
    if not pending:
        logger.info("stop[%d]: queue exhausted", iteration)
        return "queue_exhausted"
    logger.info("stop[%d]: max_iterations reached (%d)", iteration, max_iterations)
    return "max_iterations"


def _enqueue_recommended_queries(
    verdict: SufficiencyVerdict | None, pending: deque[str], seen: set[str],
    queue_width: int, events: EventLog, iteration: int,
) -> None:
    """Enqueue up to queue_width *unseen* recommendations — duplicates
    are skipped without consuming a slot."""
    if verdict is None:
        return
    fresh = (q for q in verdict.recommended_queries if q not in seen)
    for q in itertools.islice(fresh, queue_width):
        pending.append(q)
        seen.add(q)
        logger.info("queued[%d]: '%s'", iteration, q)
        events.emit({"event": "query_enqueued", "iteration": iteration, "query": q})


def _emit_session_end(
    events: EventLog, stop_reason: str, iteration: int, exc_info: tuple
) -> None:
    # GeneratorExit means the consumer closed us — that's abandonment,
    # not a pipeline failure; any other in-flight exception is.
    exc_type = exc_info[0]
    if exc_type is not None and not issubclass(exc_type, GeneratorExit):
        stop_reason = "error"
    events.emit(
        {
            "event": "session_end",
            "stop_reason": stop_reason,
            "iterations_run": iteration,
        }
    )


def iterate(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queue_width: int = 2,
    on_iteration_start: Callable[[int, int, str], None] | None = None,
    on_pre_audit: Callable[[str], None] | None = None,
    events: EventLog | None = None,
    **search_kwargs: Any,
) -> Iterator[IterationResult]:
    """Yield one IterationResult per round.

    Each verdict's recommended_queries (up to queue_width) are
    enqueued for future rounds; duplicate queries are skipped. Stops on a
    sufficient verdict, audit failure, exhausted queue, or max_iterations.

    When `events` is given, each lifecycle point emits a structured event;
    `session_end` is emitted from a finally block, so it fires even when the
    consumer abandons the generator or an exception escapes mid-loop.
    """
    events = events if events is not None else NullEventLog()
    pending: deque[str] = deque([query])
    seen: set[str] = {query}
    iteration = 0

    _emit_session_start(events, query, max_iterations, queue_width)

    # Default when no exit path below runs: the consumer walked away from the
    # generator. An in-flight exception overrides this to "error" in finally.
    stop_reason = "abandoned"

    try:
        while pending and iteration < max_iterations:
            current_query = pending.popleft()

            if on_iteration_start is not None:
                on_iteration_start(iteration, max_iterations, current_query)

            new_urls = _run_search_step(
                current_query, search_and_extract, events, iteration,
                **search_kwargs,
            )

            if auditor is None:
                stop_reason = "single_pass"
                yield IterationResult(
                    iteration=iteration,
                    query_used=current_query,
                    new_urls=new_urls,
                )
                return

            verdict, audit_failed = _run_audit_step(
                current_query, auditor, events, iteration, on_pre_audit
            )
            yield IterationResult(
                iteration=iteration,
                query_used=current_query,
                new_urls=new_urls,
                verdict=verdict,
                audit_failed=audit_failed,
            )

            reason = _stop_reason_after_audit(verdict, audit_failed, iteration)
            if reason is not None:
                stop_reason = reason
                return

            _enqueue_recommended_queries(
                verdict, pending, seen, queue_width, events, iteration
            )
            iteration += 1

        stop_reason = _stop_reason_at_loop_exit(pending, iteration, max_iterations)
    finally:
        # sys.exc_info() must be read here, in the frame where the exception
        # (or GeneratorExit) is in flight.
        _emit_session_end(events, stop_reason, iteration, sys.exc_info())


def research_topic(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queue_width: int = 2,
    events: EventLog | None = None,
    **search_kwargs: Any,
) -> ResearchResult:
    """Drain iterate() into a ResearchResult."""
    iterations = list(
        iterate(
            query,
            search_and_extract=search_and_extract,
            auditor=auditor,
            max_iterations=max_iterations,
            queue_width=queue_width,
            events=events,
            **search_kwargs,
        )
    )

    final_verdict = iterations[-1].verdict if iterations else None
    audit_failed = iterations[-1].audit_failed if iterations else False

    return ResearchResult(
        original_query=query,
        iterations=tuple(iterations),
        final_verdict=final_verdict,
        audit_failed=audit_failed,
    )
