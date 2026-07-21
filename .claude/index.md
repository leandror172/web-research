# Knowledge Index

**Purpose:** Map of where all project information lives. Read this to find anything.

<!-- ref:indexing-convention -->
### Indexing Conventions (Two-Tier System)

| Tier | Notation | When to Use | Lookup Method |
|------|----------|-------------|---------------|
| **Active reference** | `<!-- ref:KEY -->` + `[ref:KEY]` | Agent needs this during work; CLAUDE.md rules point here | `.claude/tools/ref-lookup.sh KEY` (machine-lookupable) |
| **Navigation pointer** | `§ "Heading"` | Index/docs pointing to sections for background reading | Open file, find heading (human/agent reads) |

**Active refs** are for high-frequency, runtime lookups.
**§ pointers** are for low-frequency, "read when needed" navigation.

**Single-responsibility rule:** One ref block per concept — don't wrap an entire file in one block.
Keep blocks narrow enough that `ref-lookup.sh KEY` returns only what's needed for the task.

#### "Orphaned block" warnings are NOT a delete list

`check-ref-integrity.py` reports a block as orphaned when no `[ref:KEY]` tag points at it, and
suggests removing it. **Do not act on that mechanically** — most orphans here are consumed in
ways the checker cannot see. Verified classification (2026-07-21, 18 orphans):

| Category | Blocks | Action |
|---|---|---|
| **Consumed by role**, via `.claude/handoff/registry.yaml` + `.claude/resume.yaml` | `user-prefs`, `session-reading-guide`, `deferred` | **Keep** — deleting breaks `resume.sh` at session start |
| **Invoked by name** from CLAUDE.md (`ref-lookup.sh <key>`) or read by path | `local-model-conventions`, `indexing-convention` | **Keep** |
| **Background / rationale** — research docs nothing needs at runtime | 8 `ddd-*`, `agent-naming-convention`, `mvp-spike-plan`, `quick-memory-web-research`, `vision-web-research`, `extraction-pipeline-issues` | **Keep content.** By this file's own two-tier rule these are `§`-pointer material, not `ref:` blocks — demoting them is an editorial decision, not cleanup |

A block is only genuinely dead if it fails all three tests: no `[ref:KEY]` tag, no role in the
register, and no `ref-lookup.sh <key>` call in CLAUDE.md or a skill.
<!-- /ref:indexing-convention -->

---

## Quick Pointers

| What | Where |
|------|-------|
| Project rules & constraints | `CLAUDE.md` (repo root) |
| Project overview & usage | `README.md` (repo root) |

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview — architecture, usage, status |
| `docs/research/INDEX.md` | Catalogue of the research docs in this folder, with ref keys |
| `docs/research/web-research-tool-vision.md` | Full vision — architecture, four-agent design, progressive autonomy |
| `docs/research/mvp-spike-plan.md` | MVP spike plan — how Phase 1 was scoped |
| `docs/research/QUICK-MEMORY.md` | Design-side quick memory — build-vs-fork decision, work-size estimate |
| `docs/research/ddd-agent-modeling.md` | DDD as agent/model modeling — strategic/tactical patterns, anti-patterns |
| `docs/research/ddd-agent-decisions.md` | DDD agent decisions — split/merge and worked examples |
| `docs/research/agent-naming-convention.md` | Naming convention for agents (Conductor, Dispatcher, Auditor, Lens) |
| `docs/research/python-codegen-model-benchmark.md` | Benchmark of 8 Ollama personas for Python code gen — model priority list |
| `docs/research/extraction-model-benchmark.md` | Benchmark of 7 models for web extraction — model priority list |
| `docs/research/auditor-renderer-ab-benchmark.md` | YAML vs Prose renderer A/B — why YAML is the production default |
| `docs/research/memory-layer-design.md` | Multi-tier memory system design (QUICK-MEMORY → session → ref → user) |
| `docs/research/memory-architecture-design.md` | Per-folder agent memory architecture — types, levels, knowledge base vs repo |
| `docs/research/truncation-design-notes.md` | Truncation problem analysis, strategy comparison, decision log |
| `.memories/QUICK.md` | Repo-root working memory — current phase, structure, key rules |
| `.memories/KNOWLEDGE.md` | Repo-root semantic memory — structural decisions, phase plan |
| `engine/.memories/QUICK.md` | Engine working memory — placeholder, DDD architecture overview |
| `engine/.memories/KNOWLEDGE.md` | Engine semantic memory — tool integration patterns, libs/ trigger |
| `tools/web-research/.memories/QUICK.md` | Tool working memory — current status, pipeline overview |
| `tools/web-research/.memories/KNOWLEDGE.md` | Tool semantic memory — architecture, codegen patterns, decisions |
| `tools/web-research/docs/capabilities.md` | Capability map — content types × fetch/clean/extract quality, tested configs |
| `tools/web-research/docs/auditor-iteration-control-ideas.md` | `[ref:auditor-iteration-control-ideas]` — parked ideas for Auditor loop termination |
| `tools/web-research/web_research/extraction/protocols.py` | Protocol definitions and dataclasses for extraction pipeline |
| `tools/web-research/web_research/extraction/models.py` | Model context-window lookup — Ollama API + JSON override + fallback |
| `tools/web-research/web_research/extraction/models.json` | Model context-window config (data/code boundary — agents edit JSON) |
| `tools/web-research/web_research/extraction/fetcher.py` | `HttpxFetcher` — default fetcher; returns html + status_code |
| `tools/web-research/web_research/extraction/firecrawl_fetcher.py` | `FirecrawlFetcher` — opt-in JS-rendering fetcher (`--fetcher firecrawl`) |
| `tools/web-research/web_research/extraction/cleaners.py` | HTML → text cleaners (trafilatura, html2text) |
| `tools/web-research/web_research/extraction/chunker.py` | `chunk_text` — byte-overlap chunking with model-aware max_chars |
| `tools/web-research/web_research/extraction/extractor.py` | `OllamaExtractor` — structured extraction via Ollama |
| `tools/web-research/web_research/extraction/merger.py` | Merge multi-chunk extraction results |
| `tools/web-research/web_research/extraction/prompts.py` | Open + focused extraction prompts and JSON schema |
| `tools/web-research/web_research/extraction/output.py` | `JsonOutputWriter` — per-URL JSON files under `output/` |
| `tools/web-research/web_research/search/protocols.py` | `SearchEngine` protocol + `SearchResult` |
| `tools/web-research/web_research/search/firecrawl.py` | `FirecrawlSearchEngine` — CLI subprocess, the only search provider |
| `tools/web-research/web_research/search/filters.py` | Domain blacklist loader + `is_blacklisted` (`lru_cache`) |
| `tools/web-research/web_research/search/domain_blacklist.json` | Blacklisted domains (data/code boundary) |
| `tools/web-research/web_research/knowledge/store.py` | SQLite knowledge store — save/query/has_url across sessions |
| `tools/web-research/web_research/conductor.py` | **Conductor** — `iterate()` deque loop + `research_topic()` + `build_default_auditor()` |
| `tools/web-research/web_research/auditor/auditor.py` | **Auditor** orchestrator — heuristic gate cascading to model checker |
| `tools/web-research/web_research/auditor/signals.py` | `AuditSignals` + `HeuristicChecker` — gates `insufficient` only [see (T-07)] |
| `tools/web-research/web_research/auditor/model_checker.py` | `ModelChecker` + `SufficiencyVerdict` — qwen3:14b, JSON-Schema constrained |
| `tools/web-research/web_research/auditor/renderers.py` | `SignalsRenderer` protocol — YAML (production) vs Prose |
| `tools/web-research/web_research/auditor/prompts/sufficiency.md` | Auditor prompt template (external `.md`, `{{ }}`-escaped braces) |
| `tools/web-research/web_research/events.py` | JSONL event log — EventLog protocol, JsonlEventLog, default_event_log factory |
| `tools/web-research/web_research/cli.py` | argparse CLI — `extract` + `search` subcommands, content guard, 404 check |
| `tools/web-research/web_research/mcp/server.py` | FastMCP server — research_url, search_topic, query_knowledge tools |
| `tools/web-research/run-server.sh` | MCP server entry point — stdio transport, cd to project dir before uv run |
| `.mcp.json` | Repo-level MCP registration for Claude Code |
| `tools/web-research/pyproject.toml` | Tool package config — uv, dependencies, CLI entry point, dev deps (pytest) |
| `tools/web-research/tests/conftest.py` | Shared pytest fixtures — sample_clean, sample_extraction, tmp_db |
| `tools/web-research/tests/auditor/` | Unit tests: auditor, model_checker, renderers, signals (**37 tests** — hand-written; local models produced broken fixtures here) |
| `tools/web-research/tests/extraction/` | Unit tests: chunker, cleaners, merger, models, output |
| `tools/web-research/tests/search/` | Unit tests: filters |
| `tools/web-research/tests/knowledge/` | Unit tests: store (Phase 3.3 coverage) |
| `tools/web-research/tests/test_conductor.py` | Unit tests: Conductor loop + step helpers; **stop-reason taxonomy spec lives here as `STOP_*` constants** |
| `tools/web-research/tests/test_events.py` | Unit tests: JsonlEventLog + default_event_log factory |
| `tools/web-research/tests/test_cli_events.py` | Unit tests: CLI search-loop event-log wiring |
| `tools/web-research/scripts/compare_cleaners.py` | Diagnostic — compare trafilatura vs html2text on a URL |
| `tools/web-research/scripts/inspect_chunks.py` | Diagnostic — show how a document chunks for a given model |
| `tools/web-research/scripts/smoke_test.py` | Diagnostic — end-to-end pipeline smoke test |
| `tools/web-research/benchmarks/auditor_ab.py` | A/B benchmark: YAML vs Prose renderer — pins signals+entries, calls ModelChecker directly, `temperature=0`+seed for determinism |

---

## Dev Commands

| Command | Purpose |
|---------|---------|
| `make help` | List available make targets |
| `make logs` | `tail -F` all MCP server session logs (`output/mcp-server-*.log`) |
| `make test` | Run the full pytest suite |

## Scripts & Tools

| Script | Purpose |
|--------|---------|
| `.claude/tools/ref-lookup.sh KEY` | Print a `[ref:KEY]` block by key (no args = list all keys) |
| `.claude/tools/check-ref-integrity.py` | Find broken ref tags and malformed blocks |
| `.claude/tools/resume.sh` | **Run at session start** — prints status, last Next, reading guide, decisions, commits |
| `.claude/tools/rotate-session-log.sh` | Rotate the current session log into `.claude/archive/` |
| `.claude/tools/handoff-harvest.sh` | Harvest session content for the handoff pipeline |
| `.claude/tools/handoff/run-handoff.sh` | Handoff pipeline entry point (session-tracking overlay) |
| `.claude/resume.yaml` | **Config** for `resume.sh` — ordered step list; edit to reorder/retitle/filter sections |
| `.claude/handoff/registry.yaml` | Register mapping roles → (file, ref key); renaming a ref updates read + write in one edit |
| `Makefile` | Dev convenience commands — `make logs`, `make test`, `make help` (**repo root only**) |

## Archives

| File | Period |
|------|--------|
| `.claude/archive/session-log-2026-03-18-to-2026-03-18.md` | 2026-03-18 (archived 2026-03-27) |
| `.claude/archive/session-log-2026-03-20-to-2026-03-20.md` | 2026-03-20 (archived 2026-04-06) |
| `.claude/archive/session-log-2026-03-21-to-2026-03-21.md` | 2026-03-21 (archived 2026-04-07) |
| `.claude/archive/session-log-2026-03-24-to-2026-03-24.md` | 2026-03-24 (archived 2026-04-13) |
| `.claude/archive/session-log-2026-03-27-to-2026-03-27.md` | 2026-03-27 (archived 2026-04-23) |
| `.claude/archive/session-log-2026-04-06-to-2026-04-06.md` | 2026-04-06 (archived 2026-04-23) |
| `.claude/archive/session-log-2026-04-07-to-2026-04-07.md` | 2026-04-07 (archived 2026-04-28) |
| `.claude/archive/session-log-2026-04-13-to-2026-04-13.md` | 2026-04-13 (archived 2026-04-28) |
| `.claude/archive/session-log-2026-04-23-to-2026-04-28.md` | Sessions 10–12 (2026-04-23 → 2026-04-28) |
| `.claude/archive/session-log-2026-04-28-to-2026-04-28.md` | Session 12 overflow (2026-04-28) |
| `.claude/archive/session-log-2026-04-29-s13-a-b-benchmark-confirmation-renderer-deci.md` | Session 13 — A/B benchmark, renderer decision |
| `.claude/archive/session-log-2026-05-07-s14-progress-logging-mcp-log-file-makefile.md` | Session 14 — progress logging, MCP log file, Makefile |
| `.claude/archive/session-log-2026-05-12-s15-mcp-log-path-bug-fix-task-hygiene.md` | Session 15 — MCP log path bug fix, task hygiene |
| `.claude/archive/session-log-2026-05-20-s16-phase-3-7-queue-based-conductor-audit-lo.md` | Session 16 — Phase 3.7 queue-based Conductor |
| `.claude/archive/session-log-2026-06-22-s17-phase-3-7-follow-ups-store-extractor-log.md` | Session 17 — 3.7 follow-ups, store/extractor logging |
| `.claude/archive/session-log-2026-07-03-s18-phase-3-2-jsonl-event-log-events-py-cond.md` | Session 18 — Phase 3.2 JSONL event log |
| `.claude/archive/2026-05-07-180511-logging.txt` | Terminal capture — 2026-05-07 logging session |
