"""A/B benchmark: YAML renderer vs Prose renderer for Auditor sufficiency verdicts.

Runs both renderers against the same pinned (signals, entries) snapshot per query,
so the only variable is the renderer. Uses temperature=0 + seed for determinism.

Usage:
    uv run python benchmarks/auditor_ab.py
    uv run python benchmarks/auditor_ab.py --queries "sqlite fts" "python async"
    uv run python benchmarks/auditor_ab.py --top 5
"""

from __future__ import annotations

import argparse
import json
import pathlib
import textwrap
from dataclasses import dataclass

import httpx

from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict, SUFFICIENCY_SCHEMA
from web_research.auditor.renderers import ProseRenderer, YAMLRenderer
from web_research.auditor.signals import AuditSignals, HeuristicChecker
from web_research.knowledge.store import KnowledgeStore

MODEL = "qwen3:14b"
SEED = 42
TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / "web_research" / "auditor" / "prompts" / "sufficiency.md"


class DeterministicModelChecker(ModelChecker):
    """ModelChecker with temperature=0 and fixed seed for reproducible benchmarks."""

    def check(self, signals: AuditSignals, entries: list[dict]) -> SufficiencyVerdict:
        template = self._template_path.read_text()
        rendered_signals = self._renderer.render(signals)
        rendered_entries = "\n".join(
            f"- {entry['url']}\n  {json.dumps(entry.get('data', entry))}"
            for entry in entries
        )
        filled_prompt = template.format(
            query=signals.query,
            signals=rendered_signals,
            entries=rendered_entries,
        )
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": filled_prompt}],
            "format": SUFFICIENCY_SCHEMA,
            "stream": False,
            "options": {"temperature": 0, "seed": SEED},
        }
        response = httpx.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        data = json.loads(response.json()["message"]["content"])
        return SufficiencyVerdict(
            sufficient=data["sufficient"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            missing_topics=data["missing_topics"],
            recommended_queries=data["recommended_queries"],
        )


@dataclass
class RendererResult:
    renderer_name: str
    verdict: SufficiencyVerdict


@dataclass
class QueryResult:
    query: str
    entry_count: int
    yaml_result: RendererResult
    prose_result: RendererResult

    @property
    def agree_on_sufficient(self) -> bool:
        return self.yaml_result.verdict.sufficient == self.prose_result.verdict.sufficient

    @property
    def agree_on_confidence(self) -> bool:
        return self.yaml_result.verdict.confidence == self.prose_result.verdict.confidence


def _print_verdict(label: str, v: SufficiencyVerdict) -> None:
    print(f"  [{label}]")
    print(f"    sufficient:   {v.sufficient}")
    print(f"    confidence:   {v.confidence}")
    print(f"    reasoning:    {textwrap.shorten(v.reasoning, 100)}")
    print(f"    missing ({len(v.missing_topics)}): {v.missing_topics[:3]}")
    print(f"    rec queries:  {v.recommended_queries[:2]}")


def run_benchmark(queries: list[str], store: KnowledgeStore) -> list[QueryResult]:
    heuristic = HeuristicChecker()
    yaml_checker = DeterministicModelChecker(MODEL, TEMPLATE_PATH, YAMLRenderer())
    prose_checker = DeterministicModelChecker(MODEL, TEMPLATE_PATH, ProseRenderer())

    results = []
    for query in queries:
        entries = store.query(query)
        if not entries:
            print(f"\n[SKIP] '{query}' — no entries in store")
            continue

        signals = heuristic.compute(query, entries)

        if heuristic.obviously_insufficient(signals):
            print(f"\n[SKIP] '{query}' — heuristic gates as obviously_insufficient ({signals.result_count} entries); model would not be called in production")
            continue

        print(f"\n{'='*60}")
        print(f"Query: {query!r}  ({len(entries)} entries)")
        print(f"Signals: {signals.result_count} results, {len(signals.sources)} sources")

        yaml_verdict = yaml_checker.check(signals, entries)
        prose_verdict = prose_checker.check(signals, entries)

        _print_verdict("YAML ", yaml_verdict)
        _print_verdict("PROSE", prose_verdict)

        agree_s = "✓" if yaml_verdict.sufficient == prose_verdict.sufficient else "✗"
        agree_c = "✓" if yaml_verdict.confidence == prose_verdict.confidence else "✗"
        print(f"  Agreement — sufficient: {agree_s}  confidence: {agree_c}")

        results.append(QueryResult(
            query=query,
            entry_count=len(entries),
            yaml_result=RendererResult("yaml", yaml_verdict),
            prose_result=RendererResult("prose", prose_verdict),
        ))

    return results


def _print_summary(results: list[QueryResult]) -> None:
    if not results:
        print("\nNo results to summarize.")
        return

    total = len(results)
    agree_s = sum(1 for r in results if r.agree_on_sufficient)
    agree_c = sum(1 for r in results if r.agree_on_confidence)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"  Queries run:         {total}")
    print(f"  Agree on sufficient: {agree_s}/{total}")
    print(f"  Agree on confidence: {agree_c}/{total}")

    print("\n  Per-query breakdown:")
    print(f"  {'Query':<40} {'Entries':>7}  {'YAML':>10}  {'Prose':>10}  {'Agree':>5}")
    print(f"  {'-'*40} {'-'*7}  {'-'*10}  {'-'*10}  {'-'*5}")
    for r in results:
        yv = r.yaml_result.verdict
        pv = r.prose_result.verdict
        agree = "✓" if r.agree_on_sufficient else "✗"
        print(f"  {r.query[:40]:<40} {r.entry_count:>7}  {str(yv.sufficient)+'/'+yv.confidence:>10}  {str(pv.sufficient)+'/'+pv.confidence:>10}  {agree:>5}")


def _default_queries(store: KnowledgeStore, top: int) -> list[str]:
    """Pick the top-N queries by entry count from the store."""
    from collections import Counter
    recent = store.recent(200)
    counts = Counter(r.get("query") for r in recent if r.get("query"))
    return [q for q, _ in counts.most_common(top)]


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B benchmark: YAML vs Prose renderer")
    parser.add_argument("--queries", nargs="+", help="Queries to benchmark (default: top N from store)")
    parser.add_argument("--top", type=int, default=5, help="Use top N queries from store (default: 5)")
    args = parser.parse_args()

    store = KnowledgeStore()
    queries = args.queries if args.queries else _default_queries(store, args.top)

    if not queries:
        print("No queries found in store. Run some searches first.")
        return

    print(f"Benchmarking {len(queries)} queries — model: {MODEL}, seed: {SEED}, temperature: 0")
    results = run_benchmark(queries, store)
    _print_summary(results)


if __name__ == "__main__":
    main()
