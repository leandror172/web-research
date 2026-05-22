"""Auditor orchestrator: heuristic gate cascading to model-based sufficiency check."""

from __future__ import annotations

import logging

from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict
from web_research.auditor.signals import HeuristicChecker

logger = logging.getLogger(__name__)


class Auditor:
    def __init__(
        self,
        heuristic: HeuristicChecker,
        model: ModelChecker,
        store,
    ) -> None:
        self._heuristic = heuristic
        self._model = model
        self._store = store

    def check(self, query: str) -> SufficiencyVerdict:
        entries = self._store.query(query)
        signals = self._heuristic.compute(query, entries)

        if self._heuristic.obviously_insufficient(signals):
            logger.info(
                "heuristic gate: insufficient — %d results for '%s'",
                signals.result_count,
                query,
            )
            return SufficiencyVerdict(
                sufficient=False,
                confidence="high",
                reasoning=f"Only {signals.result_count} results found; below threshold.",
                missing_topics=[],
                recommended_queries=[],
            )

        verdict = self._model.check(signals, entries)
        logger.info(
            "model verdict: sufficient=%s confidence=%s — %s",
            verdict.sufficient,
            verdict.confidence,
            verdict.reasoning,
        )
        if verdict.recommended_queries:
            logger.info("recommended_queries: %s", verdict.recommended_queries)
        return verdict
