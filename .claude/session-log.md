# Session Log

**Current Session:** 2026-04-28 | **Phase:** Phase 3 in progress — 3.4 done, 3.6 Conductor wired
**Previous logs:** `.claude/archive/session-log-2026-03-18-to-2026-03-18.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-21-to-2026-03-21.md`, `.claude/archive/session-log-2026-03-24-to-2026-03-24.md`, `.claude/archive/session-log-2026-03-27-to-2026-03-27.md`, `.claude/archive/session-log-2026-04-06-to-2026-04-06.md`, `.claude/archive/session-log-2026-04-07-to-2026-04-07.md`

---

## 2026-04-28 — Session 11: Phase 3.6 — Conductor execution

### Context

Resumed on tip of master (Phase 3.4 Auditor PR merged). User asked to review prior session reasoning, then commit + handoff. Session focused on executing Phase 3.6 from the plan written in Session 10.

### What Was Done

- **Built Conductor** (`web_research/conductor.py` — 174 lines): `IterationResult`, `ResearchResult` dataclasses; `iterate()` generator for CLI; `research_topic()` wrapper for MCP/programmatic; `build_default_auditor()` factory wired to qwen3:14b + YAML renderer
- **Wired CLI** (`cli.py` — modified 102 lines): `search_and_extract()` now returns `list[str]` (freshly extracted URLs); `_run_search()` invokes Conductor for audit-driven loop
- **Tests** (`test_conductor.py` — 245 lines): iteration mechanics, audit failure handling, early-exit on `sufficient=True`
- **Updated CLAUDE.md** — registered Phase 3.6 details
- **Commit 663127b** — Phase 3.6 foundation complete

Conductor is not yet the default CLI behavior; still integrating and testing against live Ollama.

### Decisions Made

- **Executed per Phase 3.6 plan** from Session 10 — all 11 design decisions + 10 implementation steps followed
- **YAML renderer chosen** (not prose) — simpler for model, matches CLAUDE.md example
- **Fail-open on Auditor error** — if Auditor crashes, return what we have rather than blocking research

### Incomplete

**MPC `search_topic` tool NOT YET WIRED** — still returns raw results. Needs:
- Import Conductor + build_default_auditor
- Change return shape to `{query, results, iterations_run, verdict, audit_failed}`
- Call `research_topic()` instead of single `search_and_extract()` pass

### Next

- [ ] **Wire Conductor into MPC `search_topic`** (Phase 3.6 incomplete)
- [ ] **Test Conductor end-to-end** — verify cascade works with live queries
- [ ] **A/B benchmark renderers** (optional research track, post-merge)
- [ ] **Open PR for phase-3.6-conductor** (after MPC wiring done)

---

## 2026-04-23 — Session 10: Phase 3.6 design — Conductor wire-up plan

### Context

Resumed on `phase-3.4-auditor` branch (Auditor core built but unwired). User asked to plan wiring the Auditor; explicitly wanted the plan to be runnable from a clean context. Design-discussion session — no code shipped, plan written.

### What Was Done

- **Entry-point analysis:** confirmed MCP is not the sole entry point — CLI `search`, MCP `search_topic`, and programmatic callers all route through `cli.py`'s `search_and_extract`. Auditor belongs in a shared layer above them (Conductor), not in the MCP adapter.
- **Design decisions locked** (11 items, see plan): take `recommended_queries[0]` per iteration, default `max_iterations=3`, fail-open on Auditor error, break MCP return shape to include verdict, factory-built Auditor, two-layer interface (generator + wrapper), always-search on iteration 0, no event-log scaffolding yet.
- **Parked ideas stashed:** confidence threshold + iteration-aware Auditor prompt — new doc `tools/web-research/docs/auditor-iteration-control-ideas.md` with `[ref:auditor-iteration-control-ideas]`, revisit criteria documented.
- **Plan written:** `.claude/plan-phase-3.6-conductor-wireup.md` — 11 decisions + 10 implementation steps + file change list + do-not-do list.
- **Tracking updates:** QUICK.md (parked-ideas section), index.md (new doc registered).

### Decisions Made

- **Conductor as new module** (`web_research/conductor.py`) — not a package; promote later if it grows.
- **Two-layer interface:** `iterate()` generator for CLI progress + future event-log hooks; `research_topic()` wrapper for MCP and simple callers.
- **MCP return shape breaking change accepted** — 3.5 just shipped, right moment; verdict-less MCP response would defeat the wire-up.
- **Code style:** single-purpose methods; large methods compose smaller ones (user preference recorded in plan).
- **Scope defense via do-not-do list** in the plan — explicitly excludes confidence threshold, prompt changes, event log, link-following, `research_url` audit.

### Next

- [ ] Execute Phase 3.6 in a clean context from `.claude/plan-phase-3.6-conductor-wireup.md`
- [ ] Open PR for `phase-3.4-auditor` → master (independent of 3.6; still pending from session 9)
- [ ] Pre-existing `cli.py` default-model change (`qwen3:14b` → `gemma3:12b`) still uncommitted — decide to commit or discard

---

## 2026-04-23 — Session 9: Phase 3.4 — Auditor (cascade) TDD build

### Context

Resumed after Phase 3.5 MCP merge. User wanted to design + build Auditor interactively, pausing after design discussion. Effort set to medium, TDD required, local-model-first codegen with context files.

### What Was Done

- **Design discussion:** settled on **cascade** — heuristic gate for "obviously insufficient" only (never "obviously sufficient", since content-less verdicts are unsafe). Model does all "sufficient" determinations. Heuristic computes structured signals that enrich the model's prompt.
- **Format design:** YAML for the signals block (structured pre-computed context), prose/markdown for entries. Renderer abstraction makes signals format A/B-testable.
- **Template as file:** `prompts/sufficiency.md` lives separate from code, tracked for independent iteration. Deliberate departure from `prompts.py` convention (extraction prompts are Python constants).
- **Branch:** `phase-3.4-auditor` created off master, 2 commits.
- **Built (TDD, all tests first):**
  - `auditor/signals.py` — `AuditSignals` frozen dataclass + `HeuristicChecker` (12 tests)
  - `auditor/renderers.py` — `SignalsRenderer` Protocol + `YAMLRenderer` + `ProseRenderer` (11 tests)
  - `auditor/prompts/sufficiency.md` — template with `{query}/{signals}/{entries}` slots
  - `auditor/model_checker.py` — `SufficiencyVerdict` + `ModelChecker` (Ollama JSON-schema structured output, 10 tests)
  - `auditor/auditor.py` — cascade orchestrator (4 tests)
- **Added pyyaml dependency.** 37 new tests; full suite 122 passing.

### Decisions Made

- **Heuristic gates insufficient only, never sufficient** — content-less "sufficient" verdicts are asymmetrically risky (false-sufficient stops research early). Heuristic's real role is enriching model context with pre-computed signals, not deciding sufficiency.
- **Prompt template as `.md` file** (not Python constant) — user wants template iteration separate from code changes. Diffs cleanly, supports A/B variants.
- **Brace escaping in template** — literal `{{ }}` around the JSON example block because `.format()` is used for slot-filling.
- **Protocol compliance tests dropped as tautological** — static typing concern, not runtime; other tests already fail if `.render()` is missing.
- **Handwritten > local-model for fixture architecture** — both q3c30 and g3-12b produced broken tests for the `test_model_checker.py` and `test_auditor.py` files due to interacting pytest-mock/fixture-scope/stub-state constraints. Local models win on repetitive boilerplate; they struggle on stateful-mock scaffolding.

### Next

- [ ] **Wire Auditor into MCP `search_topic`** — the build is done but not yet plugged in; natural follow-up so `search_topic` can iterate on verdicts.
- [ ] Open PR for `phase-3.4-auditor` → master
- [ ] A/B benchmark harness comparing YAMLRenderer vs ProseRenderer on real queries (research tool, post-merge)
- [ ] Pre-existing `cli.py` default-model change (`qwen3:14b` → `gemma3:12b`) — still uncommitted on master, decide to commit or discard
- [ ] 3.1 CLI batch mode, 3.2 JSONL event log (both optional)

---

## 2026-04-13 — Session 8: Phase 3.5 — MCP Server + Model Benchmarking

### Context

Resumed from Session 7 (Phase 3.3 SQLite store done, 85 tests passing). Goal: Phase 3.5 MCP server, then housekeeping + model benchmarking.

### What Was Done

- **Phase 3.5 — MCP server:** `web_research/mcp/server.py` using FastMCP, three tools: `research_url`, `search_topic`, `query_knowledge`. Option B (re-query store after CLI call, no changes to cli.py). `focus` auto-derives `prompt_type`.
- **`run-server.sh`:** bash entry point, `cd`s to project dir before `uv run python -m web_research.mcp.server`; stdio transport.
- **`.mcp.json`:** registered at repo root and also added to `/home/leandror/workspaces/llm/.mcp.json` (LLM repo now has access too).
- **`pyproject.toml`:** added `mcp[cli]>=1.0` dependency; `uv sync` confirmed clean install.
- **`.gitignore`:** added `tools/web-research/output/` and `*.txt` (session handoff scratch files).
- **CLAUDE.md codegen priority updated:** gemma3:12b (`my-python-g3-12b`) added at #2; context-files rule documented.
- **Model benchmark (with context files):** `my-python-q3c30` → ACCEPTED; `my-python-g3-12b` → IMPROVED. Without context: both REJECTED. Context files lift both models by at least one tier.
- **MCP smoke-tested live:** all three tools loaded in session, `query_knowledge` + `research_url` cache-hit path verified working.
- **Branch hygiene:** committed on master by mistake → created `phase-3.5-mcp-server` branch, cherry-picked, reset master to `de717a0`.

### Decisions Made

- **Option B for MCP return values** — wrap CLI calls, re-query store after; no changes to existing `cli.py` functions (preserves 85 tests).
- **`focus` auto-derives `prompt_type`** — MCP callers pass `focus` only; server derives `"focused"` vs `"open"` automatically.
- **`my-python-g3-12b` at priority #2** — real contender with context files; q3c30 still edges it on cleanliness (no stray typing imports, no hallucinated model names).
- **Context files rule codified** — always pass framework examples when calling `generate_code` for SDK-specific tasks.

### Next

- [ ] **3.4 — Auditor** — sufficiency check agent; plugs into MCP as `search_topic` consumer; build now that MCP interface is real
- [ ] Merge PR `phase-3.5-mcp-server` → master
- [ ] 3.1 — CLI batch mode (optional)
- [ ] 3.2 — JSONL event log (optional, feeds Auditor)
- [ ] Deferred: SearXNG Docker setup

---

