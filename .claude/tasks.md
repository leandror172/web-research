# Tasks

## Phase 0: Setup

- [x] Initialize repository
- [x] Install overlays (ref-indexing, ollama-scaffolding, session-tracking)
- [x] Populate session-context.md and tasks.md
- [x] Copy research docs to docs/research/
- [x] Create spike/ directory skeleton

## Phase 1: MVP Spike — Extraction Quality

Goal: validate that a local 14B model can reliably extract structured, useful
information from web pages. Single script, no agents, no search.

- [x] 1.0 — Protocol definitions (Fetcher, Cleaner, Extractor, OutputWriter) + pyproject.toml
- [x] 1.0a — Python codegen model benchmark (8 personas, priority: q3c30 > q25c14 > dsc16)
- [ ] 1.1 — OllamaExtractor + JsonOutputWriter + `spike/extract.py` main script
- [ ] 1.2 — `spike/prompts.py`: open extraction prompt + focus-directed prompt + JSON schema
- [ ] 1.3 — Run against 5 test URLs with `qwen3.5:9b` + `qwen2.5-coder:14b`
- [ ] 1.4 — Run same URLs with additional models for comparison
- [ ] 1.5 — Evaluate: accurate? useful? links correct? focus-directive works?
- [ ] 1.6 — Write `spike/README.md` with findings and verdict

## Phase 2: Search Integration (pending spike verdict)

- [ ] 2.1 — SearXNG Docker setup and test
- [ ] 2.2 — query → search → URL list → extract pipeline
- [ ] 2.3 — Batch processing: list of URLs → parallel extraction → comparison output

## Phase 3: MVP Core (pending language decision)

- [ ] 3.1 — CLI wrapper (query / url / batch subcommands)
- [ ] 3.2 — JSONL event log (audit trail, replay)
- [ ] 3.3 — SQLite knowledge store (structured facts, basic querying)
- [ ] 3.4 — Sufficiency check (Auditor) — LLM prompt + iteration logic

## Phase 4: Claude Code Integration

- [ ] 4.1 — MCP tools: `research_url`, `search_topic`, `query_knowledge`
- [ ] 4.2 — Skill: `/research <url>` for high-level workflow
