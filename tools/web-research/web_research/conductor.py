"""Conductor — iterative research loop driven by Auditor verdicts.

Sits above the search/extract pipeline. Runs one round of search+extract,
asks the Auditor whether knowledge is sufficient, and (if not) takes the
Auditor's first recommended follow-up query for the next round.
"""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterator
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


def _should_stop(
    iteration: int,
    max_iterations: int,
    verdict: SufficiencyVerdict | None,
    audit_failed: bool,
    new_urls: list[str],
) -> bool:
    if audit_failed:
        return True
    if iteration >= max_iterations - 1:
        return True
    if verdict is not None and verdict.sufficient:
        return True
    if verdict is not None and not verdict.recommended_queries:
        return True
    if not new_urls:
        return True
    return False


def _next_query(
    verdict: SufficiencyVerdict | None,
    queries_per_iteration: int,
) -> str | None:
    if verdict is None or not verdict.recommended_queries:
        return None
    candidates = verdict.recommended_queries[:queries_per_iteration]
    return candidates[0] if candidates else None


def iterate(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queries_per_iteration: int = 1,
    **search_kwargs: Any,
) -> Iterator[IterationResult]:
    """Yield one IterationResult per round; stop per the documented conditions."""
    iteration = 0
    current_query = query

    while True:
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

        verdict, audit_failed = _audit(current_query, auditor)
        yield IterationResult(
            iteration=iteration,
            query_used=current_query,
            new_urls=new_urls,
            verdict=verdict,
            audit_failed=audit_failed,
        )

        if _should_stop(iteration, max_iterations, verdict, audit_failed, new_urls):
            return

        next_q = _next_query(verdict, queries_per_iteration)
        if next_q is None:
            return
        current_query = next_q
        iteration += 1


def research_topic(
    query: str,
    *,
    search_and_extract,
    auditor,
    max_iterations: int = 3,
    queries_per_iteration: int = 1,
    **search_kwargs: Any,
) -> ResearchResult:
    """Drain iterate() into a ResearchResult."""
    iterations = list(
        iterate(
            query,
            search_and_extract=search_and_extract,
            auditor=auditor,
            max_iterations=max_iterations,
            queries_per_iteration=queries_per_iteration,
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
