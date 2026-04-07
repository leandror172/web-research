# Session Log

**Current Session:** 2026-04-06 | **Phase:** 2B complete, Phase 3 next
**Previous logs:** `.claude/archive/session-log-2026-03-18-to-2026-03-18.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`

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

## 2026-03-21 — Session 3: Extraction Spike + Extraction Model Benchmark

### Context

Resumed from Session 2 (codegen benchmark). Implemented remaining spike files, ran full extraction benchmark (7 models × 5 URLs × 2 tasks), discovered pipeline issues, fixed them.

### What Was Done

- Implemented full spike pipeline: `prompts.py`, `extractor.py`, `output.py`, `extract.py` (main CLI)
- Used `my-python-q3c30` to generate implementations via Ollama, verdicted each (all IMPROVED — consistent defect patterns: inherits from Protocol, unused imports, async instead of sync)
- Ran extraction benchmark: 7 models × 5 URLs (crawl4ai, huggingface, Wikipedia, htmx, MCP llms-full.txt) × 2 tasks (open + focused)
- Discovered 3 pipeline issues: Wikipedia 403 (TLS fingerprinting), no content truncation (1MB sent to 8K-context models), cold-start timeouts on model switching
- Fixed: content truncation (6K char cap), browser User-Agent
- Re-tested: MCP now correctly extracts "Model Context Protocol" (was extracting random SEP fragments); swapped Wikipedia for Arch Wiki
- Created `docs/research/extraction-model-benchmark.md` with full results and priority list
- Created `spike/QUICK-MEMORY.md` — per-folder quick memory (Tier 0 of memory layer design)
- Created `docs/research/memory-layer-design.md` — multi-tier memory architecture design
- Saved user memories: memory layer architecture interest, Ollama for code generation feedback

### Decisions Made

- **Extraction model priority:** qwen3:14b > qwen3:8b > qwen2.5-coder:14b > dsc16 (different from codegen!)
- **deepseek-r1:14b excluded** from extraction — hallucinated "PyTorch" from empty input
- **qwen3:30b-a3b not worth it** for extraction — 2-3x slower, no quality gain over 14b
- **Task-aware model selection validated** — different tasks need different models; Dispatcher should maintain separate priority lists
- **Multi-model extraction** worth exploring — fastest model for quick pass, best for depth, merge results
- **Wikipedia needs a real browser fetcher** (Crawl4AI/Firecrawl) — not fixable with UA alone
- **QUICK-MEMORY.md per folder** adopted as Tier 0 of progressive memory injection

### Next

- [ ] 1.7 — Write `spike/README.md` with findings and verdict
- [ ] Split benchmark tables into separate files (deferred — saves ~3K tokens)
- [ ] html2text comparison on pages where trafilatura fails
- [ ] Chunking strategy for pages >6K (currently just truncates)
- [ ] Consider: model-selects-model for the Dispatcher (classifier picks best extractor per content type)

---

