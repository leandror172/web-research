# Session Log

**Current Session:** 2026-04-13 | **Phase:** Phase 3 in progress — 3.5 done, Auditor next
**Previous logs:** `.claude/archive/session-log-2026-03-18-to-2026-03-18.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-21-to-2026-03-21.md`, `.claude/archive/session-log-2026-03-24-to-2026-03-24.md`

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

## 2026-04-07 — Session 7: Phase 3.3 + Test Suite + Repo Housekeeping

### Context

Resumed from Phase 2B (PR merged to master). Goal was Phase 3 — started with 3.3 (knowledge store) as highest-value entry point, then discovered and resolved structural questions about the repo layout, then established a full test suite.

### What Was Done

- **Phase 3.3 — SQLite knowledge store:** `web_research/knowledge/store.py` + `__init__.py`. Supports `save`, `has_url`, `query(topic)`, `recent(n)`, context manager. Stdlib only (sqlite3).
- **cli.py wired to store:** both subcommands now persist to `output/knowledge.db` by default; `search` skips already-known URLs (`has_url` gate); `--db` / `--no-db` flags added.
- **Repo structure investigation:** confirmed `tools/<name>/` nesting is correct — polyglot monorepo intent, repo name is a placeholder (will rename). `tools/web-research/` nesting looks odd only because it shares the placeholder repo name.
- **spike/ retired:** code fully promoted to `tools/web-research/` in Phase 2A. Deleted spike/ and orphaned root `pyproject.toml` / `uv.lock`. `.memories/` files retain historical context.
- **Docs/tracking cleanup:** `index.md`, `README.md`, `session-context.md`, `tasks.md` updated; spike benchmark findings and TOML migration task restored after over-aggressive cleanup.
- **pytest suite — 85 tests, 7 modules:**
  - `tests/extraction/`: chunker, cleaners, merger, models, output
  - `tests/search/`: filters
  - `tests/knowledge/`: store (full 3.3 coverage)
  - `conftest.py` with shared fixtures; autouse lru_cache clearing; monkeypatch over patch.object

### Decisions Made

- **MCP server insert as 3.5** — after 3.3, before Auditor (3.4); building after MCP exposure surfaces what Auditor interface needs. `has_url` / `query_knowledge` make it worth having.
- **tools/ structure confirmed** — polyglot intent; not a bug; repo rename pending.
- **spike/ deletion safe** — all code promoted, benchmarks preserved in docs.
- **.memories/ retain history** — keep spike references in memory files even when filesystem is gone; they serve agents, not as filesystem pointers.
- **TDD baseline established** — `uv run --group dev pytest`; new modules get matching test file; integration tests (fetcher, extractor, search engine) intentionally skipped.
- **Codegen verdicts (my-python-q3c30, 7 calls):** 1 ACCEPTED, 6 IMPROVED — recurring defect: `model_copy()` (Pydantic method on plain dataclass), wrong cache clearing, wrong exception types in mocks.

### Next

- [ ] **3.5 — MCP server** — `web_research/mcp/server.py` + `run-server.sh` + `.mcp.json`; tools: `research_url`, `search_topic`, `query_knowledge`
- [ ] **3.4 — Auditor** — sufficiency check; build after MCP to validate interface
- [ ] 3.1 — CLI batch mode (optional, not blocking)
- [ ] 3.2 — JSONL event log (optional, feeds Auditor)
- [ ] Deferred: SearXNG Docker setup

---

## 2026-04-06 — Session 6: Phase 2B — Content Quality Guards

### Context

Resumed from Phase 2A. Five known gaps in the search+extract pipeline were on the backlog. All five were closed in this session.

### What Was Done

- **404 detection:** `raise ValueError(f"HTTP {status_code}")` before cleaning; search loop already had a try/except that catches and continues
- **Content guard + `--top N` semantics:** `ThinContentError(ValueError)` raised in `extract_single_url` when cleaned text < `--min-chars` (default 200); `search_and_extract` loop now tracks `usable_count` and iterates all results until N usable ones are found
- **Domain blacklist:** extracted to `web_research/search/domain_blacklist.json`; `filters.py` owns the loader (`lru_cache`, graceful fallback) and `is_blacklisted()` with parent-domain walking; `cli.py` imports from there — mirrors `models.py` pattern exactly
- **FirecrawlFetcher:** new `web_research/extraction/firecrawl_fetcher.py` — runs `firecrawl scrape <url> --format html --json` as subprocess, strips `Scrape ID: ...` prefix with `stdout.find("{")`, returns `FetchResult` with rendered HTML; exposed via `--fetcher {httpx,firecrawl}` on both CLI subcommands
- All five gaps tested (real HTTP calls + mocks); branch `feature/phase-2b-content-quality` committed and pushed

### Decisions Made

- **`ThinContentError` as typed exception** — lets callers distinguish thin content from other errors without return-value gymnastics
- **Domain blacklist as JSON data file** — agents can edit without touching Python; co-located with `search/` module that owns it
- **`FirecrawlFetcher` returns rendered `html`** (not markdown) — fits existing `Cleaner` chain unchanged; Firecrawl's `Scrape ID:` stdout prefix handled by `find("{")` not line-splitting
- **Codegen verdict (my-python-q3c30, 3 calls):** 1 ACCEPTED, 2 IMPROVED (unused imports added — `from pathlib import Path`, `from typing import cast`)

### Next

- [ ] Phase 3.1 — CLI wrapper improvements (batch mode, structured output)
- [ ] Phase 3.2 — JSONL event log (audit trail, replay)
- [ ] Phase 3.3 — SQLite knowledge store — structured facts that persist and compound across sessions
- [ ] Phase 3.4 — Sufficiency check (Auditor agent) — first DDD agent boundary
- [ ] Deferred: SearXNG Docker setup (local-first search to replace Firecrawl credits)
- [ ] Merge PR for `feature/phase-2b-content-quality`

---

## 2026-03-27 — Session 5: Memory Architecture + Phase 2A (Search Integration)

### Context

PR from feature/memory-architecture merged to main. Session recontextualized from that point, then tackled two parallel tracks: (1) memory architecture design and (2) Phase 2A implementation.

### What Was Done

**Memory architecture:**
- Designed per-folder `.memories/` system (QUICK.md + KNOWLEDGE.md) modeled on human cognitive memory types (working, semantic, episodic, procedural, structural, prospective)
- Created `.memories/` at repo root, `spike/.memories/`, `engine/.memories/`, `tools/web-research/.memories/`
- QUICK.md has structural index into KNOWLEDGE.md sections (agents can decide whether to drill in)
- Wrote `docs/research/memory-architecture-design.md` — full design doc (repo vs knowledge base, dream mode/consolidation, open questions)
- Updated LLM repo QUICK-MEMORY.md + added overlay guidance task to tasks.md
- Moved old `spike/QUICK-MEMORY.md` into `spike/.memories/QUICK.md`

**Repo structure decisions:**
- `engine/` — future orchestration layer (Conductor, Dispatcher, Auditor, Lens)
- `tools/<name>/` — self-contained capabilities (own pyproject.toml, no shared imports)
- Engine dispatches via MCP/CLI/HTTP — not Python imports between tools
- `libs/` trigger defined: two+ tools duplicating non-trivial non-MCP logic

**Phase 2A — search integration:**
- Scaffolded `tools/web-research/` as proper Python package
- Promoted spike extraction code into `web_research/extraction/` (updated imports)
- Added `web_research/search/` — SearchEngine protocol + FirecrawlSearchEngine (CLI subprocess)
- Wired CLI: `web-research extract <url>` + `web-research search <query> --top N`
- Installed Firecrawl CLI and authenticated
- Ran full end-to-end test: search "crawl4ai" → extract → JSON output working
- Added `scripts/` — compare_cleaners.py, inspect_chunks.py, smoke_test.py
- Added `tools/web-research/docs/capabilities.md` — living capability map

**Ollama codegen (my-python-q25c14, 10 files):** 5 ACCEPTED, 4 IMPROVED, 1 REJECTED
- REJECTED: chunker signature changed because callers weren't in context_files
- Key lesson: always include caller files as context when promoting called code

### Decisions Made

- **Per-folder .memories/** — QUICK.md (working, ~30 lines, always injected) + KNOWLEDGE.md (semantic, read on demand)
- **Structural indexing in QUICK:** "Deeper Memory → KNOWLEDGE.md" section lists what's inside so agents can decide whether to read it
- **Episodic + procedural stay at repo level** — they don't have meaningful per-folder existence
- **Tool isolation confirmed:** no shared Python imports; MCP bridge is integration layer
- **Firecrawl for search (Phase 2A), SearXNG deferred** — Docker setup not blocking
- **Firecrawl extraction available as optional Extractor** — not default, but possible
- **capabilities.md** — living capability map by content type (not tasks, not architecture — operational evidence)
- **Serialize Ollama generate_code calls** — concurrent calls cause cold-start contention

### Next

- [ ] **Phase 2B gap 1:** Content guard — skip URLs with <N chars after cleaning, try next result
- [ ] **Phase 2B gap 2:** `--top N` should mean N usable results, not N attempts
- [ ] **Phase 2B gap 3:** FirecrawlFetcher — optional Fetcher impl for JS-rendered sites
- [ ] **Phase 2B gap 4:** 404 detection — check status_code before cleaning
- [ ] **Phase 2B gap 5:** Search result filtering — domain blacklist or char-count threshold before extraction
- [ ] Merge PR #2 (feature/memory-architecture) — all commits pushed, ready to review
- [ ] Update LLM repo QUICK-MEMORY.md (Phase 2 now complete, not "next")
- [ ] (LLM repo) Add overlay guidance for repo-file-as-context pattern in ollama-scaffolding

---

