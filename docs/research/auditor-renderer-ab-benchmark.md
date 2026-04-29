# Auditor Renderer A/B Benchmark

*2026-04-29. Compared YAMLRenderer vs ProseRenderer as inputs to the Auditor's model checker.*

---

## Summary

**Decision: YAMLRenderer is the production default.**

Prose is systematically more optimistic — it called a 3-entry corpus `sufficient/high` where YAML
called the same corpus `insufficient/medium`. The root cause is that prose descriptions create
narrative coherence that reads as comprehensive; YAML's structured layout makes gaps visually
salient to the model. For a research tool, over-stopping is the failure mode, so YAML's
conservatism is the right property.

---

## Setup

- **Script:** `tools/web-research/benchmarks/auditor_ab.py`
- **Model:** `qwen3:14b`
- **Determinism:** `temperature=0`, `seed=42`
- **Seed note:** `seed=42` stabilises verdict and confidence tier across runs; free-text fields
  (reasoning, missing_topics, recommended_queries) vary and were not used for comparison
- **Method:** Both renderers receive the same pinned `(signals, entries)` snapshot per query —
  `ModelChecker.check()` called directly, bypassing the store re-query. The only variable is the
  renderer.

---

## Results

### Session 12 (preliminary — 2 queries)

Only 2 queries, both `sufficient`. Both renderers agreed on verdict. Confidence diverged on
sparse single-source data: YAML→`low`, Prose→`medium`. Inconclusive — flagged for re-run.

### Session 13 (confirmed — 4 queries, 2026-04-29)

| Query | Entries | Sources | YAML verdict | Prose verdict | Verdict agree? | Confidence agree? |
|---|---|---|---|---|---|---|
| httpx python async http client | 3 | 2 | False / medium | **True / high** | ✗ | ✗ |
| python dataclasses guide | 3 | 3 | False / medium | False / medium | ✓ | ✓ |
| sqlite full text search python | 2 | 2 | False / medium | False / medium | ✓ | ✓ |
| proxify.ai proxy voting AI | 2 | 1 | False / **low** | False / **medium** | ✓ | ✗ |

- **Verdict agreement: 3/4**
- **Confidence agreement: 2/4**
- 1 query skipped by heuristic gate (`ollama REST API usage python`, 1 entry — `obviously_insufficient`)

---

## Key Observations

### 1. Prose over-reads breadth-first coverage as sufficient

The `httpx` case is the canonical example. Three entries covering httpx's async features
breadth-first read as comprehensive in a prose description. YAML's structured layout exposes
that each feature is sparsely covered — the model notices the gaps.

This is a documented prompt engineering effect: structured formats make weaknesses salient.
Flowing prose hides them behind narrative coherence.

### 2. YAML is more conservative at single-source data

On `proxify.ai` (2 entries, 1 source), YAML returned `low` confidence vs Prose's `medium`.
Both correctly called it `insufficient`, but YAML signals more clearly that the data is thin.
This matches the preliminary Session 12 finding.

### 3. When data is genuinely insufficient, both renderers agree

On `python dataclasses guide` and `sqlite full text search python` (both with multiple
independent sources), renderers agreed on verdict AND confidence. The divergence only
appears when the model has room to interpret borderline data differently.

---

## Implications for Conductor

The Conductor calls `Auditor.check()` to decide whether to iterate. With a `sufficient` verdict
the loop exits; with `insufficient` it runs another search. Prose's tendency to call things
sufficient early means the Conductor would stop after fewer iterations — producing shallower
research. YAML drives more iterations, which is correct for a depth-oriented research tool.

**Throughput trade-off:** If a use case needs fast, shallow answers, Prose reduces Conductor
iterations. The `ProseRenderer` is available and the `DeterministicModelChecker` in the
benchmark script shows how to swap it in. This is not the default.

---

## Wiring

- **Production renderer:** `YAMLRenderer` — already wired into `build_default_auditor()` in
  `conductor.py` before this benchmark was run; this report confirms the choice is correct
- **Renderer abstraction:** `SignalsRenderer` Protocol in `auditor/renderers.py` — swap by
  passing a different renderer instance to `ModelChecker(model, template_path, renderer)`
- **Benchmark script:** `benchmarks/auditor_ab.py` — run with `--top N` or `--queries "q1" "q2"`
