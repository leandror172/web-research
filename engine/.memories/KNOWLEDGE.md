# engine/ — Knowledge (Semantic Memory)

*Accumulated decisions and patterns for the engine layer. Read on demand.*

## Architecture Decisions

### DDD Bounded Contexts (from vision)

| Agent | Role | Bounded Context |
|-------|------|-----------------|
| Conductor | Orchestration, manages research lifecycle, saves state | Research session |
| Dispatcher | Tool execution, knows how to call tools and build pipelines | Tool routing |
| Auditor | Sufficiency review, decides if more research is needed | Quality gate |
| Lens | Context proxy, sifts results without polluting Conductor's context | Context management |

### Tool Integration Pattern

Tools are self-contained (own package, own deps, own pyproject.toml). Engine dispatches
to them through:
1. **MCP calls** — preferred, ollama-bridge already serves this role for Ollama
2. **CLI subprocess** — for tools that expose a CLI
3. **HTTP** — for tools that run as services

**No shared Python imports between tools.** If two Python tools need the same utility
(e.g., Ollama client), they use MCP bridge — not a shared library. If something truly
generic and non-Ollama-specific emerges, extract a `libs/` package then — not preemptively.

### When to Create libs/

Watch for: two or more tools duplicating non-trivial logic that ISN'T covered by MCP bridge.
Examples that would trigger it: shared config parsing, common data formats, protocol
definitions used across tools. Examples that would NOT: Ollama calls (use MCP), HTTP
fetching (each tool has its own needs), CLI argument parsing.
