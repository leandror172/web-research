# engine/ — Quick Memory

*Working memory for this folder. Injected into agents operating here. Keep under 30 lines.*

## Status

Empty — placeholder created 2026-03-26. Engine code arrives in Phase 2B (orchestrator).

## Purpose

Orchestration layer for the web-research pipeline. Four agents modeled as DDD bounded
contexts, each owning a distinct responsibility:

- **Conductor** — manages a research session lifecycle: what to research, when to stop, saving state
- **Dispatcher** — knows how to call tools and compose pipelines; selects models per-task
- **Auditor** — sufficiency gate: reviews accumulated results, decides if more research is needed
- **Lens** — context proxy: summarizes/filters results so the Conductor's context stays clean

## Architecture Rules

- Engine sits above tools — tools don't know about each other or the engine
- Tools are black boxes — only their Protocol contracts matter
- Communication: MCP calls, CLI subprocess, or HTTP — never Python imports across boundaries

## Deeper Memory → KNOWLEDGE.md

- **DDD Bounded Contexts** — agent roles, responsibilities, interaction patterns
- **Tool Integration Pattern** — how engine dispatches to tools
- **When to Create libs/** — trigger conditions for shared code extraction
