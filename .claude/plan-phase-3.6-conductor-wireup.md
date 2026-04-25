# Phase 3.6 — Conductor Wire-Up (Auditor into the research loop)

**Status:** planned. Written 2026-04-23 for execution in a clean context session.
**Branch:** continue on `phase-3.4-auditor`, or cut `phase-3.6-conductor` from it.
**Depends on:** Phase 3.4 (Auditor core, done) + 3.5 (MCP server, done).

---

## Why this phase exists

The Auditor is built and tested in isolation (37 tests, Phase 3.4) but nothing calls it.
Today's entry points — CLI `search`, MCP `search_topic`, programmatic `search_and_extract`
— run one round of search+extract and stop. No iteration, no sufficiency check.

The vision (`/mnt/i/workspaces/llm/docs/research/web-research-tool-vision.md`, the
Conductor layer) puts audit-driven iteration *above* the Dispatcher layer, so it must be
shared by **all three** entry points — not bolted into one of them. Putting the loop in
`mcp/server.py` would leak a domain concern into an adapter and skip the Auditor for CLI
and programmatic callers.

**Solution:** extract a `conductor.py` module that owns the search→audit→iterate loop.
CLI, MCP, and programmatic callers all go through it.

## What ships in this phase

1. New `web_research/conductor.py` module with an iterative research loop
2. CLI `search` subcommand calls it (adds `--max-iterations`, `--no-audit`)
3. MCP `search_topic` calls it; return shape changes to include verdict
4. Tests covering loop termination paths
5. Minimal doc updates (QUICK.md, index.md)

`research_url` (single URL) is **unchanged** — nothing to audit in a one-shot extraction.

---

## Design decisions (locked in during design session)

See session-log for full discussion. Summary:

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Refinement strategy:** take `recommended_queries[0]` per iteration; configurable via `queries_per_iteration` (default 1) | Honors Auditor's prioritization; keeps per-round cost predictable; the next Auditor call re-evaluates against the growing entry pool so unimportant gaps deprioritize naturally |
| 2 | **Termination:** stop on any `sufficient=True` OR `max_iterations` hit (default 3, param) OR no `recommended_queries` OR no new URLs extracted this round | Any sufficient verdict respects the Auditor's call — confidence thresholding is parked (see below) |
| 3 | **Decreasing 'more' signal:** hard cap only for MVP | Adding iteration-awareness to the Auditor prompt is a separate, invasive change — see `[ref:auditor-iteration-control-ideas]` |
| 4 | **Auditor failure mode:** fail-open — log warning, mark `audit_failed=True`, return partial results | Users prefer partial results over errors for research tasks |
| 5 | **MCP return shape:** breaking change — now `{query, results, iterations_run, verdict, audit_failed}` instead of `list[dict]` | The whole point of wiring the Auditor is that Claude Code can use the verdict; dropping it defeats the purpose. 3.5 just shipped, this is the right moment |
| 6 | **Auditor construction:** `build_default_auditor(store)` factory + optional `auditor=` override on the loop | Terse callsite, but tests can inject fakes |
| 7 | **First iteration:** always search unconditionally, even if store already has entries | Simpler; cache-hit logic in `extract_single_url` already dedups |
| 8 | **Two-layer interface:** `iterate(...)` generator + `research_topic(...)` convenience wrapper | Generator for CLI progress; wrapper for MCP. Both are thin. |
| 9 | **Event log hooks:** NOT scaffolded | YAGNI — Phase 3.2 will know the right shape |
| 10 | **Module shape:** single file `conductor.py` for MVP, promote to package later if it grows | |
| 11 | **Code style:** single-purpose methods; large methods are composed of smaller method calls, not inline blocks | User preference — keeps each function focused |

### Parked for follow-up (do NOT do in this phase)

- Confidence threshold param (`stop_on_confidence`) — `[ref:auditor-iteration-control-ideas]` Idea 1
- Iteration-aware Auditor prompt — `[ref:auditor-iteration-control-ideas]` Idea 2
- Link-following ("which links to follow" — vision line 28)
- Widening original search (more results, higher `top`) as a fallback strategy
- JSONL event log (Phase 3.2)
- `research_url` audit (never — single URL has nothing to iterate)

---

## Implementation steps

Before writing anything, run `.claude/tools/resume.sh` and read this plan end-to-end.

### Step 1 — Scaffold `conductor.py`

Create `tools/web-research/web_research/conductor.py`. Keep methods small and
composable; no method should do multiple things. Target shape:

```python
from dataclasses import dataclass
from typing import Iterator
from web_research.auditor.auditor import Auditor
from web_research.auditor.model_checker import SufficiencyVerdict

@dataclass(frozen=True)
class IterationResult:
    iteration: int            # 0-based
    query_used: str           # actual query run (may differ from original on later rounds)
    new_urls: list[str]       # URLs extracted THIS iteration (for progress display)
    verdict: SufficiencyVerdict | None  # None if audit disabled/failed
    audit_failed: bool

@dataclass(frozen=True)
class ResearchResult:
    original_query: str
    iterations: list[IterationResult]
    final_verdict: SufficiencyVerdict | None
    audit_failed: bool

    @property
    def iterations_run(self) -> int: ...
```

### Step 2 — Write `iterate()` generator

Loop pseudocode (each bullet is a small helper method, not inline):

- `_run_one_round(query, ...)` — calls existing `search_and_extract(...)`; returns the
  list of URLs extracted (diff against the store before/after, or capture via a passed-in
  callback — pick whichever is cleaner)
- `_audit(query)` — calls `auditor.check(query)`; on exception, log + return
  `(None, audit_failed=True)`
- `_should_stop(verdict, audit_failed, iteration, max_iterations, new_urls)` —
  returns `(stop: bool, reason: str)`; encodes termination logic in one place
- `_next_query(verdict, queries_per_iteration)` — returns next query or `None`

The generator yields one `IterationResult` per round, stopping when `_should_stop` fires.

### Step 3 — Write `research_topic()` convenience wrapper

Thin wrapper — consumes `iterate()`, collects results, returns `ResearchResult`.

### Step 4 — Add `build_default_auditor(store)` factory

Lives in `conductor.py` (or `auditor/factory.py` — check which feels right at
implementation time; the factory is small enough for either). Builds the default
`HeuristicChecker` + `ModelChecker` (with the existing prompt template path and renderer
choice) + `Auditor`.

Default renderer: whichever the existing Auditor tests use as the default — **do not**
introduce a new default in this phase.

### Step 5 — Wire CLI

In `cli.py`:
- Add `--max-iterations N` (default 3) and `--no-audit` flags to the `search` subparser
- In `search_and_extract`-calling branch, route through `conductor.iterate(...)` instead;
  consume the generator and print a verdict summary per iteration:
  ```
  [iteration 1/3] query: "…" → 3 new URLs
    Auditor: insufficient (medium) — missing: rate-limit caveats
    Next query: "firecrawl rate limiting 2025"
  ```
- At end: print final verdict block and total iterations run.
- `--no-audit` short-circuits to the existing one-round behavior (or equivalently, calls
  `iterate()` with `max_iterations=1, auditor=None` — pick the simpler implementation).

### Step 6 — Wire MCP

In `mcp/server.py`:
- `search_topic` calls `conductor.research_topic(...)` instead of `search_and_extract`.
- New return shape (document in the tool docstring — Claude Code sees the docstring):
  ```python
  {
      "query": "...",
      "results": [...],
      "iterations_run": 2,
      "verdict": {
          "sufficient": bool,
          "confidence": "low|medium|high",
          "reasoning": "...",
          "missing_topics": [...],
          "recommended_queries": [...],
      } | None,
      "audit_failed": False,
  }
  ```
- Add a `max_iterations: int = 3` arg to the MCP tool signature.

### Step 7 — Tests

New file: `tools/web-research/tests/test_conductor.py`.

Fakes to build:
- `FakeAuditor` accepting a scripted list of verdicts: `FakeAuditor([insufficient(["q1"]), insufficient(["q2"]), sufficient()])`
- `FakeSearchAndExtract` — recorded calls, scripted URL lists per query

Cases (each one is a small, focused test):

1. Stops on first `sufficient=True` — one round only.
2. Iterates up to `max_iterations` when Auditor never says sufficient.
3. Stops early when Auditor returns empty `recommended_queries`.
4. Stops early when an iteration produces zero new URLs.
5. `audit_failed=True` when Auditor raises; loop stops; partial results returned.
6. `queries_per_iteration=1` takes `recommended_queries[0]`.
7. `research_topic()` collects all iterations into `ResearchResult`.
8. `--no-audit` path equivalent (max_iterations=1, auditor=None) — same as
   old single-round behavior; no Auditor called.

Update existing tests only if MCP return shape change breaks them — `search_topic`
smoke test likely needs updating.

### Step 8 — Smoke test (manual, user-run)

After tests pass:
- CLI: `uv run web-research search "some topic" --max-iterations 2` — observe per-iteration
  verdict printing and termination.
- MCP: restart server, call `search_topic` from Claude Code, confirm new return shape.

### Step 9 — Doc updates

- `tools/web-research/.memories/QUICK.md` — update Status to "Phase 3.6 complete",
  briefly mention the Conductor loop. Keep under 30 lines.
- `.claude/index.md` — add `conductor.py` row under Files.
- `.claude/tasks.md` — add Phase 3.6 section with checkboxes.
- Consider a short entry in `tools/web-research/.memories/KNOWLEDGE.md` if any
  non-obvious decision surfaced during implementation.

### Step 10 — Commit + handoff

Conventional commit message: `feat: Phase 3.6 — Conductor wires Auditor into search loop`.
Update `.claude/session-log.md` and `.claude/session-context.md` via the
`session-handoff` skill.

---

## Files expected to change

| File | Change |
|------|--------|
| `tools/web-research/web_research/conductor.py` | **new** |
| `tools/web-research/web_research/cli.py` | `search` command routes through Conductor; 2 new flags |
| `tools/web-research/web_research/mcp/server.py` | `search_topic` uses Conductor; new return shape + docstring |
| `tools/web-research/tests/test_conductor.py` | **new** |
| `tools/web-research/tests/mcp/` (if exists) | update search_topic return-shape assertions |
| `tools/web-research/.memories/QUICK.md` | status bump |
| `.claude/index.md` | register conductor.py |
| `.claude/tasks.md` | Phase 3.6 checkboxes |
| `.claude/session-log.md`, `.claude/session-context.md` | handoff |

## Verification

- `uv run --group dev pytest` from `tools/web-research/` — all existing + new tests pass
- Smoke test (Step 8)
- No new dependencies added (the whole stack already exists)

## Context pointers for the executing session

- Vision: `/mnt/i/workspaces/llm/docs/research/web-research-tool-vision.md`
- Auditor core: `tools/web-research/web_research/auditor/` (auditor.py, model_checker.py, signals.py, renderers.py, prompts/)
- Current entry points:
  - CLI: `tools/web-research/web_research/cli.py` — `search_and_extract()`, `extract_single_url()`
  - MCP: `tools/web-research/web_research/mcp/server.py` — 3 tools
- Parked ideas: `tools/web-research/docs/auditor-iteration-control-ideas.md` — `[ref:auditor-iteration-control-ideas]`
- Active rules: `ref-lookup.sh current-status` | `ref-lookup.sh active-decisions`

## Do-not-do list (avoid scope creep)

- No confidence-threshold param (parked)
- No changes to the Auditor prompt template (parked)
- No event-log hooks
- No changes to `research_url`
- No refactor of `search_and_extract` beyond what the wire-up requires
- No new default renderer or prompt
- No link-following
