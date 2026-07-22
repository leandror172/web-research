# web-research/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand by agents and chatbot.*

## Tool Isolation (2026-03-26)

Each tool is self-contained: own package, own pyproject.toml, own dependencies.
Tools communicate through defined interfaces (CLI, HTTP, or MCP) — never shared
Python imports. Inspired by Domain-Driven Design bounded contexts: each tool is a
black box that owns its data and logic.

**Rationale:** Allows polyglot tools (different languages per tool), independent
deployment, and clean boundaries. A search tool shouldn't break because the
extraction tool changed an internal function.

**Implication:** No shared `libs/` package exists preemptively. The trigger for
creating one is: two or more tools duplicating non-trivial logic not covered by
the MCP bridge.

## Search Provider Strategy (2026-03-26)

Protocol-based: a `SearchEngine` interface with swappable implementations.
Firecrawl (cloud API) was the first provider — used to validate the pipeline with
a working search backend before investing in local infrastructure. SearXNG
(self-hosted, Docker) is the planned local-first replacement.

**Rationale:** Validate the pipeline architecture with an available provider first.
Building a local search backend before proving the pipeline works wastes effort.

**Implication:** Adding a new search provider means implementing one Protocol — no
changes to the rest of the pipeline.

## Folder Convention (2026-03-26)

- `engine/` — *placeholder for* the orchestration layer (Dispatcher, Lens). **Still empty.**
  Conductor and Auditor were built inside `tools/web-research/` instead; whether to migrate
  them here or abandon this folder is undecided.
- `tools/<name>/` — self-contained capabilities. Each has own package structure.
- `docs/research/` — design decisions, benchmarks, architecture rationale.
- `<folder>/.memories/` — per-folder context files modeled on cognitive memory types.

## Phase Plan

| Phase | Scope | Status |
|-------|-------|--------|
| 1 — Spike | Extraction pipeline + model benchmarks | Complete (2026-03-26) |
| 2A — Search | Search integration (Firecrawl + existing pipeline) | Complete (2026-03-27) |
| 2B — Content quality | Content guard, result filtering, JS-rendered sites | Complete (2026-04-06) |
| 3 — Research loop | Knowledge store, Auditor, MCP server, Conductor, queue, event log | Complete (2026-07-02) — except 3.1 CLI batch (optional, open) |
| Orchestration layer | `engine/`: Dispatcher + Lens agents, config-driven orchestration | **Not started** |

**Naming caveat — do not "restore" the old label.** This table used to read
`2B — Orchestrator | Simple orchestrator (proto-Conductor, config-driven)`. A doc-refresh
commit (`7a1cace`, 2026-04-02) kept the *label* but swapped the *scope* to the content-quality
work, leaving a row whose name and contents described different things. The orchestrator work
was never delivered as 2B: the Conductor arrived later as 3.6, and Dispatcher/Lens plus
config-driven orchestration still do not exist. Marking that row "Complete" under the old
label would assert a four-agent orchestration layer this repo does not have.

## Memory Architecture (2026-03-26)

Per-folder `.memories/` with two files, modeled on cognitive psychology:
- **QUICK.md** = working memory + prospective memory (current state, what's next)
- **KNOWLEDGE.md** = semantic memory + consolidated episodic memory (decisions, findings)

Episodic memory (session logs) consolidates into KNOWLEDGE.md over time —
analogous to memory consolidation during sleep. Procedural memory lives at
repo level (CLAUDE.md, scripts).

**Rationale:** Agents need folder-specific context, but full project context is too
expensive to inject everywhere. Two files per folder is the minimum viable unit.

**Implication:** Any folder with its own distinct domain gets its own `.memories/`.

<!-- ref:function-decomposition -->
## Function Decomposition Pattern (2026-07-03)

How to judge when a function is too big and how to split it — established while
refactoring `conductor.iterate()` (110 → 55 lines, PR #12).

**When to split — count decisions, not lines.** A long function with one linear
path (e.g. `JsonlEventLog.emit`) is fine. Split when multiple *decision* steps
interleave with boilerplate: `iterate()` had ~10 branch points and 4 exit paths
mixed with event-emission ceremony.

**How to split:**
- **Helper names narrate algorithm steps** (`_run_search_step`, `_run_audit_step`,
  `_enqueue_recommended_queries`) — not implementation ("init state") or a list of
  cases. If the name doesn't describe a step of the domain algorithm, don't extract.
- **Kill repeated `if x is not None` guards with a null-object** (`NullEventLog`),
  not by copying the guard into every helper.
- **Extract decisions as pure functions** returning a value (`_stop_reason_after_audit`
  → `str | None`, None = continue) — unit-testable without the surrounding machinery.
- **Make hidden state explicit parameters** for testability: pass `sys.exc_info()`
  into the helper instead of calling it inside (caller reads it in the right frame).
- **In generators, keep `yield`/`return`/`try-finally` in the generator itself** —
  moving them changes semantics; only decisions and side-effects move out.
- **Don't extract low-value units:** a helper returning 4 unrelated locals as a
  tuple, or one smaller than its call site, makes the code worse.

**Refactoring trap:** "limit N candidates examined" ≠ "limit N successes" — a plain
`islice`/slice over candidates silently drops slots when the skip branch fires.
Filter first, then slice (same lesson as `--top N`, see tools/web-research KNOWLEDGE).

**Process:** tests first — pin the subtle behavior with a regression test (RED),
add unit tests for each extracted pure helper, then refactor (GREEN).
<!-- /ref:function-decomposition -->

## Cross-Repo Connections (2026-04-02)

This project is part of a three-repo engineering portfolio:

1. **web-research** (this repo) — local-model web research tool
2. **LLM platform** (`/mnt/i/workspaces/llm`) — Ollama infrastructure, model personas,
   MCP bridge, Claude Code configuration. Provides the foundation this project runs on:
   model config, ollama-bridge MCP server, overlay system for Claude Code guidance.
3. **Expense classifier** — ML classification project (separate domain)

**How they connect:** The LLM repo's ollama-bridge MCP server is the integration
layer between Claude Code and Ollama. Web-research uses it for model warm-up and
can use it for extraction. Research docs in the LLM repo informed this project's
design (DDD patterns, memory architecture). The memory architecture pattern
(per-folder `.memories/`) originated here and is being adopted across repos.

**Chatbot context:** These memories also feed a Gradio-based portfolio chatbot on
Hugging Face Spaces, which discusses engineering profile and project decisions with
visitors.
