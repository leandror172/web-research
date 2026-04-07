# Session Log

**Current Session:** 2026-04-07 | **Phase:** Phase 3 in progress — 3.3 done, MCP next
**Previous logs:** `.claude/archive/session-log-2026-03-18-to-2026-03-18.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-21-to-2026-03-21.md`

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

## 2026-03-24 — Session 4: Chunking + Merge Pipeline

### Context

Resumed from Session 3 to address truncation (naive 6K char cap). Read `docs/research/truncation-design-notes.md` from previous session, then designed and implemented chunking + merge strategy with model-aware context limits.

### What Was Done

- Reviewed and discussed 6 truncation strategies, chose **chunking + merge with model-aware limits**
- Documented decision in `docs/research/truncation-design-notes.md` § "Decision Log"
- Implemented `spike/models.py` — queries Ollama `/api/show` at runtime for context length, JSON override layer, hardcoded fallback
- Implemented `spike/models.json` — override/fallback config (separate data from code)
- Implemented `spike/chunker.py` — paragraph-boundary chunking with configurable overlap, sentence-level fallback
- Implemented `spike/merger.py` — combines N ExtractionResults (open: union+dedup lists, merge dicts; focused: highest assessment wins)
- Updated `spike/extract.py` — pipeline now: fetch → clean → chunk → extract per chunk → merge → save
- Tested live: Arch Wiki (43K chars) now fits in 1 chunk (was truncated to 6K/14%)
- Created GitHub repo (`leandror172/web-research`, public, SSH) and pushed all history
- Used Ollama (`my-python-q3c30`) to generate boilerplate for models.py, chunker.py, merger.py — all verdicted IMPROVED with fixes applied

### Decisions Made

- **Chunking + merge** chosen over smart truncation, two-pass, or relevance-based (local models = N× calls cost time not money)
- **Relevance-based truncation deferred** — needs Dispatcher task-level strategy selection
- **Not using LangChain/LlamaIndex** — overhead > value for one backend + custom architecture
- **Model context data: Ollama API first, JSON override second** — JSON caps override Ollama (intentional human decisions like "model degrades past 32K")
- **JSON over TOML for now** — Python 3.10 lacks tomllib; deferred to TOML migration when ≥3.11
- **Existing code as Ollama context** — feed repo files as few-shot examples to code generation (feedback saved to memory)
- **Public repo** — user chose public visibility for web-research

### Next

- [ ] 1.7 — Write `spike/README.md` with findings and verdict
- [ ] Update spike/QUICK-MEMORY.md with chunking findings
- [ ] (LLM repo) Add overlay guidance for repo-file-as-context pattern in ollama-scaffolding
- [ ] Consider: test chunking with a truly massive document (1M+ chars) to exercise multi-chunk merge path

---

