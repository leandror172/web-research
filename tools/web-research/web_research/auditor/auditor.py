"""Auditor orchestrator: heuristic gate cascading to model-based sufficiency check."""

from __future__ import annotations

from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict
from web_research.auditor.signals import HeuristicChecker


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
            return SufficiencyVerdict(
                sufficient=False,
                confidence="high",
                reasoning=f"Only {signals.result_count} results found; below threshold.",
                missing_topics=[],
                recommended_queries=[],
            )

        return self._model.check(signals, entries)
