# engine/ — Knowledge (Semantic Memory)

*Accumulated decisions and patterns for the engine layer. Read on demand.*

## DDD Bounded Contexts (from vision, 2026-03)

The four engine agents map to Domain-Driven Design bounded contexts. Each agent owns
a single responsibility and communicates with others through defined interfaces — not
shared internal state.

| Agent | Role | What It Owns |
|-------|------|--------------|
| Conductor | Orchestration — manages research lifecycle, saves state | Research session, accumulated knowledge |
| Dispatcher | Tool execution — calls tools, builds pipelines, selects models | Tool registry, model-task mapping |
| Auditor | Sufficiency review — decides if more research is needed | Quality criteria, confidence thresholds |
| Lens | Context proxy — sifts/summarizes results for Conductor | Summarization rules, context budget |

**Rationale:** Each agent can evolve independently. The Dispatcher can learn new tools
without changing the Conductor. The Auditor can adopt new quality criteria without
affecting tool execution. This mirrors how DDD bounded contexts protect domain logic
from cross-cutting changes.

**Implication:** When building the engine, resist the urge to merge agents "for
simplicity." The boundaries are the architecture.

## Tool Integration Pattern (2026-03-26)

Tools are self-contained packages. The engine dispatches to them through:
1. **MCP calls** — preferred; ollama-bridge already demonstrates this pattern
2. **CLI subprocess** — for tools exposing a command-line interface
3. **HTTP** — for tools running as services

No shared Python imports between tools. If two Python tools need the same utility
(e.g., Ollama client), they use the MCP bridge — not a shared library.

**Rationale:** Keeps tools deployable and testable independently. A bug in one tool
cannot cascade through shared imports.

## When to Create libs/ (2026-03-26)

**Trigger:** two or more tools duplicating non-trivial logic NOT covered by MCP bridge.

Examples that would trigger: shared config parsing, common data format definitions,
protocol types used across tools.

Examples that would NOT: Ollama calls (use MCP), HTTP fetching (each tool has
different needs), CLI argument parsing (too tool-specific).

**Rationale:** Premature shared libraries create coupling. Wait for duplication to
prove a shared abstraction is needed.

## Task-Aware Model Selection (2026-03-26)

Discovered during spike: extraction and code generation need different models.
Code-specialized models (qwen2.5-coder) dominate codegen; general-purpose models
(qwen3:14b) dominate extraction. The Dispatcher should maintain a model-task mapping
rather than using one model for everything.

**Rationale:** Empirical finding from benchmarking 7 models across 2 task types.
A single "best model" doesn't exist — it depends on the task.

**Implication:** Model selection is a Dispatcher responsibility, not a global config.
