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

- `spike/` — frozen proof-of-concepts. Reference only, not imported by production code.
- `engine/` — orchestration layer (Conductor, Dispatcher, Auditor, Lens). Sits above tools.
- `tools/<name>/` — self-contained capabilities. Each has own package structure.
- `docs/research/` — design decisions, benchmarks, architecture rationale.
- `<folder>/.memories/` — per-folder context files modeled on cognitive memory types.

## Phase Plan

| Phase | Scope | Status |
|-------|-------|--------|
| 1 — Spike | Extraction pipeline + model benchmarks | Complete (2026-03-26) |
| 2A — Search | Search integration (Firecrawl + existing pipeline) | Complete (2026-03-27) |
| 2B — Orchestrator | Content guard, result filtering, JS-rendered sites | Next |
| 3+ — Agents | Full agent architecture, knowledge store, CLI, MCP server | Future |

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
