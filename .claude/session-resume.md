# Session Resume — Phase 3.6 Complete

**Last session:** 2026-04-28 (Session 12)  
**Current branch:** `phase-3.6-conductor` (PR #7 open)  
**Status:** Phase 3 fully complete — Conductor wired into MCP, live-tested, PR open

---

## What Changed This Session

### Phase 3.6 — MCP Wiring (complete)

- **`mcp/server.py`** updated: `search_topic` now calls `research_topic()` (Conductor loop) instead of a single `search_and_extract()` pass
- **Return shape:** `{query, results, iterations_run, verdict, audit_failed}`
- **Two-pass results collection:** LIKE on original query (catches cached iteration-1 hits) + per-URL lookup for follow-up iteration URLs
- **Live test passed:** `search "sqlite full text search python" --max-iterations 2` — cascade ran correctly; stopped on `new_urls=[]`
- **Bug found + fixed during live test:** cached-URL sessions were returning `results=[]` (cached URLs don't appear in `new_urls`)

### A/B Benchmark (complete)

- **`benchmarks/auditor_ab.py`** (194 lines): pins signals+entries per query, calls `ModelChecker.check()` directly per renderer, `temperature=0` + `seed=42`
- Run with: `uv run python benchmarks/auditor_ab.py --top 5` or `--queries "topic1" "topic2"`
- **Finding (confirmed, 4 queries):** Prose is systematically more optimistic — verdict disagreement 1/4, confidence 2/4; canonical case: `httpx` (3 entries) → YAML `insufficient/medium`, Prose `sufficient/high`. **Decision: YAML is production default.** Prose available but narrative coherence masks coverage gaps.

### Key commits this session

- `7c8bb4e` feat: Phase 3.6 — Wire Conductor into MCP search_topic
- `fb6ef76` fix: MCP search_topic — include cached entries in results
- `57de0ac` feat: auditor A/B benchmark — YAML vs Prose renderer

---

## To-Do List

### Immediate
- [ ] **Merge PR #7** — all 130 tests passing, live-verified, ready

### Short-term (post-merge)
- [x] ~~Re-run A/B benchmark with richer data~~ — done (Session 13, 4 queries, confirmed)
- [x] ~~Confirm A/B finding~~ — YAML conservatism confirmed; decision made: YAML is production renderer

### Optional (deferred)
- [ ] Phase 3.1 — CLI batch mode
- [ ] Phase 3.2 — JSONL event log
- [ ] Tune heuristic thresholds after more live testing

---

## Architecture at a Glance

```
search_topic(query)                         ← MCP tool
  └─ research_topic(query, ...)             ← conductor.py
       └─ iterate() — yields IterationResult per round
            ├─ search_and_extract(query) → new_urls (list[str])
            ├─ auditor.check(query) → SufficiencyVerdict
            └─ stop if: sufficient | max_iter | no recs | no new_urls | audit error

_result_to_dict(ResearchResult) → dict
  ├─ pass 1: store.query(original_query)     — catches cached iteration-1 entries
  └─ pass 2: store.query(url) per new_url   — catches follow-up iteration entries
```

**Stop conditions (in order):**
1. `audit_failed` — fail open, return what we have
2. `iteration >= max_iterations - 1` — hard cap
3. `verdict.sufficient == True` — goal reached
4. `verdict.recommended_queries == []` — model has no follow-ups
5. `new_urls == []` — no new content this round

---

## Reference Files

- `[ref:current-status]` — Latest phase, what's done, test count
- `[ref:active-decisions]` — Design decisions
- `[ref:vision]` — High-level architecture
- `tools/web-research/web_research/mcp/server.py` — MCP server (3 tools)
- `tools/web-research/web_research/conductor.py` — Conductor (iterate + research_topic)
- `tools/web-research/benchmarks/auditor_ab.py` — Renderer A/B benchmark
