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
- [x] 1.1 — OllamaExtractor + JsonOutputWriter + `spike/extract.py` main script
- [x] 1.2 — `spike/prompts.py`: open extraction prompt + focus-directed prompt + JSON schema
- [x] 1.3 — Run against 5 test URLs with multiple models (7 models × 5 URLs × 2 tasks)
- [x] 1.4 — Extraction model benchmark — priority: qwen3:14b > qwen3:8b > q25c14 > dsc16
- [x] 1.5 — Fix pipeline gaps: content truncation (6K char cap), browser User-Agent
- [x] 1.6 — Re-test: MCP now correctly extracts "Model Context Protocol" with truncation; swapped Wikipedia (403 — TLS fingerprinting) for Arch Wiki
- [x] 1.7 — Write `spike/README.md` with findings and verdict

### Deferred

- [ ] Split benchmark tables into separate files, reference via § (saves ~3K tokens on doc load)
- [ ] Migrate `tools/web-research/web_research/extraction/models.json` to TOML when Python ≥3.11 is the minimum — use `tomllib` (stdlib), drop JSON loader
- [ ] Relevance-based truncation — select document sections by focus directive before extraction. Needs Dispatcher task-level strategy selection. See § "Deferred: Relevance-based selection" in `docs/research/truncation-design-notes.md`
- [ ] (T-01) **Add overlay guidance: Ollama code gen with repo context** — when generating code via Ollama, include existing repo files as few-shot context (protocols, implementations, data files). More effective than prose style instructions. Update in the ollama-scaffolding overlay source.

## Phase 2: Search Integration

- [x] 2.0 — SearchEngine protocol + FirecrawlSearchEngine (CLI subprocess)
- [x] 2.1 — Promote spike extraction code to tools/web-research/web_research/extraction/
- [x] 2.2 — query → search → URL list → extract pipeline (CLI: `search <query> --top N`)
- [x] 2.3 — Diagnostic scripts: compare_cleaners, inspect_chunks, smoke_test
- [x] 2.4 — Capability map: tools/web-research/docs/capabilities.md

### Phase 2B — Content Quality (complete 2026-04-06)

- [x] 2B.1 — Content guard: skip URLs with <N chars after cleaning, try next result
- [x] 2B.2 — `--top N` semantics: N usable results, not N attempts
- [x] 2B.3 — FirecrawlFetcher: optional Fetcher impl for JS-rendered sites (YouTube, Reddit, SPAs)
- [x] 2B.4 — 404 detection: check status_code before cleaning
- [x] 2B.5 — Search result filtering: domain blacklist or char-count threshold before extraction

### Deferred

- [ ] SearXNG Docker setup — local-first search provider to replace Firecrawl

## Phase 3: MVP Core

- [ ] 3.1 — CLI wrapper (query / url / batch subcommands) — optional, not blocking
- [x] 3.2 — JSONL event log (audit trail, replay) — `events.py` + Conductor wiring + CLI/MCP integration; stop-reason taxonomy incl. `abandoned`/`error` via finally — complete 2026-07-02
- [x] 3.3 — SQLite knowledge store (structured facts, basic querying) — complete 2026-04-07
- [x] 3.5 — MCP server — `web_research/mcp/server.py` + `run-server.sh` + `.mcp.json`; tools: `research_url`, `search_topic`, `query_knowledge`
- [x] 3.4 — Sufficiency check (Auditor) — heuristic gate → model checker (qwen3:14b, YAML renderer)
- [x] 3.6 — Conductor — `iterate()` generator + `research_topic()` + progress callbacks
- [x] 3.7 — Auditor loop tuning — replaced scalar loop with deque queue; `queries_per_iteration` default 1→2; Q2 fallback verified in real run

### Also completed this phase
- [x] Pytest suite — 172 tests, 14 modules (`uv run --group dev pytest`); 37 of them cover `auditor/`
- [x] Progress logging — `on_iteration_start`/`on_pre_audit` callbacks; `WR_LOG_LEVEL`; per-PID MCP log file; `Makefile`
- [x] Audit logging — INFO-level verdict + stop-reason logs in auditor.py and conductor.py; `WR_LOG_LEVEL` bumped to INFO

### Deferred / follow-on
- [x] (T-02) **Add store/extractor logging** — `logger.debug()`/`logger.info()` to `store.py` and extractor pipeline; auditor/conductor now covered, store/extractor still dark under `--log-level DEBUG`
- [x] (T-03) **Rename `queries_per_iteration` → `queue_width`** — current name implies parallelism; deferred until more callers exist

## Phase 4: Claude Code Integration

- [ ] 4.1 — MCP skill: `/research <url>` for high-level workflow
- [ ] 4.2 — Full agent loop (Conductor + Auditor iteration)

<!-- ref:deferred -->
## Deferred / Backlog

- [ ] (T-04) **Per-URL pipeline events** — extend event granularity into `search_and_extract` (fetch/clean/extract per page); deferred from 3.2 scope decision
- [ ] (T-05) **Event-log replay tooling** — reader/CLI over `output/events/*.jsonl`; groups sessions by stop_reason, excludes error/audit_failed from sufficiency tuning; feeds Auditor
- [ ] (T-06) **Add a `ref:quick-pointers` block to `.claude/session-context.md`.** Session 111 migrated `resume.sh` to a config-driven step list (`.claude/resume.yaml`, session-tracking overlay v11). Its "Key files" step resolves the `quick-pointers` role, now present in `.claude/handoff/registry.yaml` pointing at `.claude/session-context.md`. **This repo has no such block**, so the step prints its fallback `(no ref:quick-pointers block found)` — exactly what the old bash printed, so nothing regressed. But the section is worth having: it is the 6-row table telling an agent where `tasks.md`, `session-log.md`, `session-context.md`, `CLAUDE.md`, and the cross-session memory live, injected at every session start. Wrap it in the standard open/close ref comment markers for key `quick-pointers` (see the indexing convention in `.claude/index.md`); the step then picks it up with no config change. **Note:** this task description must NOT contain those markers literally — doing so created a phantom block here that made `ref-lookup.sh quick-pointers` return this task text instead of reporting the key as missing. Alternatively, delete the step from `.claude/resume.yaml` and the `quick-pointers` role from the register. See llm repo `docs/plans/resume-config-steps.md`.
- [ ] (T-07) **Auditor heuristic gate must emit a recovery action, not just a judgment.** Real-run logs (10 sessions, 2026-07-11) show 6/10 runs ending `queue_exhausted` at iteration 1: `HeuristicChecker.obviously_insufficient` returns `recommended_queries=[]`, which empties the queue and terminates the loop *before* the model checker runs. Two harms: a badly-phrased query is indistinguishable from a topic with no coverage, and the run is logged `queue_exhausted` ("Auditor out of ideas") when the Auditor was never consulted — corrupting the one distinction the stop-reason taxonomy exists to preserve. Fix options: fall through to the model checker instead of returning early, or attach a cheap deterministic rephrasing. **Supersedes Ideas 1–2** (they target the opposite failure mode). Evidence: tool `KNOWLEDGE.md` § "Heuristic Gate Short-Circuits the Loop"; § "ANSWERED" in `tools/web-research/docs/auditor-iteration-control-ideas.md`. [ref:auditor-iteration-control-ideas]
- [ ] (T-08) **Record verdict source in `audit_verdict` events** — add `source: "heuristic" | "model"`. Diagnosing T-07 required *inferring* which stage produced a verdict from its signature (`sufficient=False` + `confidence=high` + empty `recommended_queries` is the heuristic's only possible return). Blocks clean replay analysis (T-05).
<!-- /ref:deferred -->
