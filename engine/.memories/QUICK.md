# engine/ — Quick Memory

*Working memory for this folder. Injected into agents operating here. Keep under 30 lines.*

## Status

Empty — placeholder created 2026-03-26. Engine code arrives in Phase 2B (orchestrator).

## Purpose

Orchestration layer: Conductor, Dispatcher, Auditor, Lens (DDD bounded contexts).
Dispatches to tools through defined interfaces (CLI, MCP, Protocol) — does NOT import
tool code directly.

## Architecture Rules

- Engine sits above tools — tools don't know about each other
- Tools are black boxes to the engine — only contracts matter
- Communication: MCP calls, CLI subprocess, or HTTP — not Python imports
- No shared Python libraries between tools (MCP bridge is the integration layer)

## Deeper Memory → KNOWLEDGE.md

- **DDD Bounded Contexts** — Conductor, Dispatcher, Auditor, Lens roles and boundaries
- **Tool Integration Pattern** — MCP/CLI/HTTP dispatch, no shared imports
- **When to Create libs/** — trigger conditions, examples that qualify vs don't

Also: `../../spike/.memories/` (extraction findings), `../../docs/research/memory-architecture-design.md` (memory system)
