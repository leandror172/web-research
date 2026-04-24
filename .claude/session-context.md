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

- **Active phase:** Phase 3 — 3.6 Conductor wire-up planned (executable from clean context via `.claude/plan-phase-3.6-conductor-wireup.md`)
- **Completed:** Phase 3.4 (Auditor core) — signals + heuristic + renderers (YAML/prose) + model checker + orchestrator + external prompt template; 37 new tests
- **Planned (not started):** Phase 3.6 — extract `conductor.py` with audit-driven iteration loop; rewire CLI `search` and MCP `search_topic` through it; parked ideas (confidence threshold, iteration-aware prompt) documented at `[ref:auditor-iteration-control-ideas]`
- **Completed:** Phase 3.5 (MCP server) — research_url/search_topic/query_knowledge, FastMCP, stdio transport, registered in web-research + llm repos
- **Completed:** Phase 3.3 (SQLite knowledge store) — save/has_url/query/recent, wired into CLI
- **Completed:** Phase 2B (content quality) — 404 detection, content guard, ThinContentError, --top N usable, domain blacklist, FirecrawlFetcher
- **Branch:** `phase-3.4-auditor` — 2 commits; PR not yet opened
- **Language:** Python confirmed for MVP (uv + pyproject.toml)
- **Memory structure:** Per-folder `.memories/` (QUICK.md + KNOWLEDGE.md) — at root, engine/, tools/web-research/
- **Tests:** 122 pytest tests passing — `uv run --group dev pytest` from `tools/web-research/`
- **Key finding:** Extraction and codegen need different models — task-aware model selection validated
- **Codegen model priority:** q3c30 > g3-12b > q25c14 > dsc16; context files lift both top models by ≥1 tier
- **Capability map:** `tools/web-research/docs/capabilities.md` — content types × quality matrix, tested configs, known gaps
- **MCP server:** live + smoke-tested; `query_knowledge` + `research_url` cache-hit path confirmed
- **Auditor cascade:** heuristic gate → model checker; heuristic gates *insufficient only* (content-less "sufficient" verdicts too risky); YAML vs prose renderer A/B-ready
- **Conductor design (3.6):** new `web_research/conductor.py`; `iterate()` generator + `research_topic()` wrapper; stop on `sufficient=True`, `max_iterations` (default 3), no recommendations, or no-new-URLs; fail-open on Auditor error; MCP return shape changes to `{query, results, iterations_run, verdict, audit_failed}`
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
- **SignalsRenderer abstraction (YAML vs prose)** — makes input-format effect on model verdict A/B-testable.
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
