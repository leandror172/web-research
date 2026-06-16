## 2026-04-29 — Session 13: A/B benchmark confirmation + renderer decision

### Context

Resumed on `phase-3.6-conductor`. PR #7 open (user handling merge). Previous session's A/B benchmark ran on only 2 queries and was inconclusive. Advisor (Opus) from the prior session flagged: verify `seed=42` determinism before trusting results.

### What Was Done

**Seed determinism check (Opus advisor concern)**
- `seed=42` + `temperature=0` stabilises binary verdict and confidence tier — both match across two runs
- Free-text fields (reasoning, missing_topics, rec_queries) vary — non-deterministic
- Implication: verdict/confidence comparisons in the A/B are reliable; text field comparisons are not

**A/B benchmark re-run (4 queries, richer data)**
- Populated store with 4 new searches (`qwen3:8b` for speed); landed 3 entries each for `httpx python async http client` and `python dataclasses guide`
- Ran `uv run python benchmarks/auditor_ab.py --top 5` — 4 queries evaluated (1 skipped by heuristic gate)

### Findings

| Query | Entries | YAML | Prose | Verdict agree? |
|---|---|---|---|---|
| httpx python async http client | 3 | False/medium | True/high | ✗ |
| python dataclasses guide | 3 | False/medium | False/medium | ✓ |
| sqlite full text search python | 2 | False/medium | False/medium | ✓ |
| proxify.ai (1 source) | 2 | False/low | False/medium | ✓ |

- Verdict agreement: 3/4 — Confidence agreement: 2/4
- **Pattern:** Prose is systematically more optimistic. Narrative coherence masks coverage gaps — the `httpx` case is canonical: 3 entries covering httpx breadth-first reads as "comprehensive" in prose but YAML exposes each feature is lightly covered.
- **YAML's conservatism is the right property** — for a research tool, over-stopping is the failure mode; the Conductor should run more iterations, not fewer.

### Decision

**YAML renderer is the production default.** Already wired into `build_default_auditor()` in `conductor.py`. Prose stays available via `ProseRenderer()` for throughput-optimised use cases (e.g. shallow scans where a quick answer beats depth).

### Next

- [ ] Phase 3.1 — CLI batch mode (deferred)
- [ ] Phase 3.2 — JSONL event log (deferred)
- [ ] Tune heuristic thresholds after more live testing

---

