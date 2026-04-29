<!-- ref:user-prefs -->
## User Preferences

- Explanatory output style (educational insights with task completion)
- Interactive pacing — pause after phases for user input
- Build config files incrementally, not all at once
- Shell script invocation: always use `./script.sh` not `bash script.sh`
- Local model first for boilerplate Python; evaluate with ACCEPTED/IMPROVED/REJECTED
<!-- /ref:user-prefs -->

<!-- ref:current-status -->
## Current Status

- **Active phase:** Phase 3 complete — 3.4 + 3.6 fully wired; **PR #7 open** (`phase-3.6-conductor` → master)
- **Completed:** Phase 3.6 (Conductor) — `conductor.py` (174 lines); CLI + MCP wired; return shape `{query, results, iterations_run, verdict, audit_failed}`; live-tested; 130 tests passing
- **Completed:** Phase 3.4 (Auditor core) — signals + heuristic + renderers (YAML/prose) + model checker + orchestrator + external prompt template; 37 tests
- **Completed:** Phase 3.5 (MCP server) — research_url/search_topic/query_knowledge, FastMCP, stdio transport
- **Completed:** Phase 3.3 (SQLite knowledge store) — save/has_url/query/recent, wired into CLI
- **Completed:** Phase 2B (content quality) — 404 detection, content guard, ThinContentError, --top N usable, domain blacklist, FirecrawlFetcher
- **Branch:** `phase-3.6-conductor` — PR #7 open, all tests passing, ready to merge
- **Language:** Python confirmed for MVP (uv + pyproject.toml)
- **Memory structure:** Per-folder `.memories/` (QUICK.md + KNOWLEDGE.md) — at root, engine/, tools/web-research/
- **Tests:** 130 pytest tests passing — `uv run --group dev pytest` from `tools/web-research/`
- **Key finding:** Extraction and codegen need different models — task-aware model selection validated
- **Codegen model priority:** q3c30 > g3-12b > q25c14 > dsc16; context files lift both top models by ≥1 tier
- **Capability map:** `tools/web-research/docs/capabilities.md` — content types × quality matrix, tested configs, known gaps
- **MCP server:** live + smoke-tested; `query_knowledge` + `research_url` cache-hit path confirmed; `search_topic` now runs Conductor loop
- **Auditor cascade:** heuristic gate → model checker; heuristic gates *insufficient only*; YAML vs prose renderer A/B benchmarked (`benchmarks/auditor_ab.py`)
- **A/B finding (confirmed, 4 queries):** Prose is systematically more optimistic — verdict disagreement 1/4, confidence disagreement 2/4; `httpx` case shows Prose calling `sufficient/high` while YAML calls `insufficient/medium` on identical 3-entry corpus. YAML's conservatism is the right property for a research tool (over-stopping is the failure mode).
- **Renderer decision: YAML** — production default; Prose available for throughput-optimized use cases
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
