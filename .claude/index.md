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
| `docs/research/python-codegen-model-benchmark.md` | Benchmark of 8 Ollama personas for Python code gen — model priority list |
| `docs/research/extraction-model-benchmark.md` | Benchmark of 7 models for web extraction — model priority list |
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
| `tools/web-research/web_research/knowledge/store.py` | SQLite knowledge store — save/query/has_url across sessions |
| `tools/web-research/web_research/events.py` | JSONL event log — EventLog protocol, JsonlEventLog, default_event_log factory |
| `tools/web-research/web_research/mcp/server.py` | FastMCP server — research_url, search_topic, query_knowledge tools |
| `tools/web-research/run-server.sh` | MCP server entry point — stdio transport, cd to project dir before uv run |
| `.mcp.json` | Repo-level MCP registration for Claude Code |
| `tools/web-research/pyproject.toml` | Tool package config — uv, dependencies, CLI entry point, dev deps (pytest) |
| `tools/web-research/tests/conftest.py` | Shared pytest fixtures — sample_clean, sample_extraction, tmp_db |
| `tools/web-research/tests/extraction/` | Unit tests: chunker, cleaners, merger, models, output |
| `tools/web-research/tests/search/` | Unit tests: filters |
| `tools/web-research/tests/knowledge/` | Unit tests: store (Phase 3.3 coverage) |
| `tools/web-research/tests/test_events.py` | Unit tests: JsonlEventLog + default_event_log factory |
| `tools/web-research/tests/test_cli_events.py` | Unit tests: CLI search-loop event-log wiring |
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
| `.claude/tools/ref-lookup.sh KEY` | Print a `[ref:KEY]` block by key |
| `.claude/tools/check-ref-integrity.sh` | Find broken ref tags and malformed blocks |
| `Makefile` | Dev convenience commands — `make logs`, `make test`, `make help` |

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
| `.claude/archive/2026-05-07-180511-logging.txt` | Terminal capture — 2026-05-07 logging session |
