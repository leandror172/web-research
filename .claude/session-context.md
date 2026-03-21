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

- **Active phase:** Phase 1 — MVP Spike (extraction benchmark complete)
- **Next:** Fix pipeline gaps (truncation, User-Agent, cleaner comparison), then test across more URLs
- **Language:** Python confirmed for MVP (uv + pyproject.toml)
- **Completed:** Full spike pipeline (fetch→clean→extract→save), codegen benchmark (8 models), extraction benchmark (7 models × 5 URLs)
- **Key finding:** Extraction and codegen need different models — task-aware model selection validated
- **Pipeline gaps:** content truncation, Wikipedia 403, link URL extraction inconsistency
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
- **Python codegen priority:** q3c30 > q25c14 > dsc16 (§ python-codegen-model-benchmark.md)
- **Extraction priority:** qwen3:14b > qwen3:8b > q25c14 > dsc16 (§ extraction-model-benchmark.md) [ref:extraction-model-priority]
- **Task-aware model selection** — different tasks need different models; Dispatcher should select per-task
- **Toolkit pattern** — each pipeline step independently callable, Protocol-based boundaries
- **Repo name:** `web-research` — placeholder, rename when better name emerges
- **session-handoff skill:** installed at user level (`~/.claude/skills/`) not per-repo
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
