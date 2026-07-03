<!-- ref:user-prefs -->
## User Preferences

- Explanatory output style (educational insights with task completion)
- Interactive pacing — pause after phases for user input
- Build config files incrementally, not all at once
- Shell script invocation: always use `./script.sh` not `bash script.sh`
- Local model first for boilerplate Python; evaluate with ACCEPTED/IMPROVED/REJECTED
<!-- /ref:user-prefs -->

<!-- ref:current-status -->
- **Active branch:** `feat/jsonl-event-log` — PR #12 open (JSONL event log, Phase 3.2); `master` has triage commits (gitattributes, run-server PATH fix) pushed
- **Completed:** Phase 3 fully done — 3.2 (JSONL event log) was the last non-optional item; PR #11 (store/extractor logging + queue_width) merged earlier
- **Event log:** `events.py` — EventLog Protocol + JsonlEventLog + `default_event_log`; Conductor emits 6 lifecycle event types; `session_end` guaranteed via finally; stop reasons: sufficient / audit_failed / queue_exhausted / max_iterations / single_pass / abandoned / error; files at `output/events/events-{session_id}.jsonl`
- **Conductor:** `iterate()` deque queue, `queue_width=2`, `seen` dedup; accepts `events` sink
- **Tests:** 159 pytest tests passing (TDD: taxonomy spec lives as `STOP_*` constants in test_conductor.py)
- **MCP server:** live; per-PID logs + per-call event logs under `output/`; `WR_LOG_LEVEL` in `.mcp.json`; `make logs`
- **Auditor:** heuristic gate → model checker (qwen3:14b, YAML renderer)
- **Codegen model priority:** q3c30 > g3-12b > q25c14 > dsc16; context files lift both top models by ≥1 tier
- **Next:** Merge PR #12; then Phase 4.1 (`/research` skill) or 3.1 (CLI batch)
<!-- /ref:current-status -->

<!-- ref:resume-steps -->
## Resuming Work

**On session start:** run `.claude/tools/resume.sh` — outputs current status, next task, recent commits in ~40 lines.
For deeper context: `ref-lookup.sh current-status` | `ref-lookup.sh active-decisions` | `ref-lookup.sh vision`
**Research docs (design decisions, architecture, DDD patterns):** `/mnt/i/workspaces/llm/docs/research/`
**Quick memory (current status of web-research design):** `/mnt/i/workspaces/llm/docs/research/QUICK-MEMORY.md`
<!-- /ref:resume-steps -->

<!-- ref:active-decisions -->
## Active Decisions

- **Build new** (not fork Local Deep Research) — LDR patterns worth borrowing, not the code
- **Language: Python** — confirmed for MVP, uv as dependency manager
- **Local-model-first** — Ollama 7-14B for extraction; frontier (Claude) optional
- **Python codegen priority:** q3c30 > g3-12b > q25c14 > dsc16; always pass context_files for framework tasks (§ python-codegen-model-benchmark.md)
- **Extraction priority:** qwen3:14b > qwen3:8b > q25c14 > dsc16 (§ extraction-model-benchmark.md) [ref:extraction-model-priority]
- **Task-aware model selection** — different tasks need different models; Dispatcher should select per-task
- **Toolkit pattern** — each pipeline step independently callable, Protocol-based boundaries
- **Chunking strategy:** chunk + merge with model-aware limits; Ollama API → JSON override → hardcoded fallback
- **Data vs code boundary:** model config in JSON (not Python dicts) — agents edit data files safely
- **Repo name:** `web-research` — placeholder, rename when better name emerges; `tools/<name>/` structure correct (polyglot intent)
- **MCP server:** built as 3.5, live + smoke-tested; Option B (re-query store after CLI call); `focus` auto-derives `prompt_type`
- **session-handoff skill:** installed at user level (`~/.claude/skills/`) not per-repo
- **Auditor: heuristic gates insufficient only** — heuristic can't judge content; asymmetric risk means "sufficient" is model-only. Heuristic's job is enriching model context with pre-computed signals.
- **Auditor: prompt template is a `.md` file** (`auditor/prompts/sufficiency.md`) — iterate wording independent of code; use `.format()` so literal JSON braces must be `{{ }}` escaped.
- **SignalsRenderer abstraction (YAML vs prose)** — A/B confirmed: YAML is production default. Prose available but systematically over-optimistic (narrative coherence masks coverage gaps).
- **Local-model boundary for codegen** — repetitive boilerplate & straightforward impl: offload. Fixture architecture with stateful mocks: hand-write (both q3c30 and g3-12b produced broken `test_model_checker.py`/`test_auditor.py` on this type of task).
- **Conductor queue model (3.7)** — `iterate()` uses `deque`; `queries_per_iteration=2` default enqueues Q1+Q2 from each verdict; `not new_urls` hard-stop removed; `max_iterations` is the sole budget cap. Chose queue over confidence-threshold (Idea 1) and iteration-aware prompt (Idea 2) because real logs showed a resilience gap, not a calibration problem.
<!-- /ref:active-decisions -->

<!-- ref:vision -->
## Vision (summary)

Local-model-powered web research workbench. Fetches, extracts, and accumulates knowledge
from the web using Ollama (7-14B models). Progressively autonomous: starts supervised,
delegates more over time. Knowledge compounds across sessions.

**Agent architecture (DDD bounded contexts):**
- **Conductor** — orchestration, manages research lifecycle, saves state
- **Dispatcher** — tool execution, knows how to call tools and build pipelines
- **Auditor** — sufficiency review, decides if more research is needed
- **Lens** — context proxy, sifts results without polluting Conductor's context

**MVP path:** spike (extraction quality) → search → pipeline → knowledge → CLI → MCP

Full design: `/mnt/i/workspaces/llm/docs/research/web-research-tool-vision.md`
Spike plan: `/mnt/i/workspaces/llm/docs/research/mvp-spike-plan.md`
<!-- /ref:vision -->

<!-- ref:session-reading-guide -->
## Pre-Session Reading Guide

*What to read before each pending work item.*

| Task | Read first | Notes |
|------|-----------|-------|
| 4.1 `/research` MCP skill | `tools/web-research/web_research/mcp/server.py`; tool QUICK.md | Wrap existing 3 MCP tools into a workflow skill |
| (T-05) Event-log replay tooling | KNOWLEDGE.md § "Event Log Design"; `web_research/events.py` | Schema + stop-reason taxonomy are the contract |
<!-- /ref:session-reading-guide -->
