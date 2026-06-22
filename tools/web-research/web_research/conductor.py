"""Conductor — iterative research loop driven by Auditor verdicts.

Sits above the search/extract pipeline. Runs one round of search+extract,
asks the Auditor whether knowledge is sufficient, and (if not) takes the
Auditor's first recommended follow-up query for the next round.
"""

from __future__ import annotations

import logging
import pathlib
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from web_research.auditor.auditor import Auditor
from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict
from web_research.auditor.renderers import YAMLRenderer
from web_research.auditor.signals import HeuristicChecker

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


def iterate(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queue_width: int = 2,
    on_iteration_start: Callable[[int, int, str], None] | None = None,
    on_pre_audit: Callable[[str], None] | None = None,
    **search_kwargs: Any,
) -> Iterator[IterationResult]:
    """Yield one IterationResult per round.

    Each verdict's recommended_queries (up to queue_width) are
    enqueued for future rounds; duplicate queries are skipped. Stops on a
    sufficient verdict, audit failure, exhausted queue, or max_iterations.
    """
    pending: deque[str] = deque([query])
    seen: set[str] = {query}
    iteration = 0

    while pending and iteration < max_iterations:
        current_query = pending.popleft()

        if on_iteration_start is not None:
            on_iteration_start(iteration, max_iterations, current_query)

        new_urls = search_and_extract(current_query, **search_kwargs)

        if auditor is None:
            yield IterationResult(
                iteration=iteration,
                query_used=current_query,
                new_urls=new_urls,
                verdict=None,
                audit_failed=False,
            )
            return

        if on_pre_audit is not None:
            on_pre_audit(current_query)
        verdict, audit_failed = _audit(current_query, auditor)
        yield IterationResult(
            iteration=iteration,
            query_used=current_query,
            new_urls=new_urls,
            verdict=verdict,
            audit_failed=audit_failed,
        )

        if audit_failed:
            logger.info("stop[%d]: audit failed", iteration)
            return

        if verdict is not None and verdict.sufficient:
            logger.info("stop[%d]: sufficient=True confidence=%s", iteration, verdict.confidence)
            return

        if verdict is not None:
            enqueued = 0
            for q in verdict.recommended_queries:
                if enqueued >= queue_width:
                    break
                if q not in seen:
                    pending.append(q)
                    seen.add(q)
                    logger.info("queued[%d]: '%s'", iteration, q)
                    enqueued += 1

        iteration += 1

    if not pending:
        logger.info("stop[%d]: queue exhausted", iteration)
    else:
        logger.info("stop[%d]: max_iterations reached (%d)", iteration, max_iterations)


def research_topic(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queue_width: int = 2,
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
