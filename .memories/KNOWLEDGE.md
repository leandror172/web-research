# web-research/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand.*

## Repo Structure Decisions

### Tool Isolation (2026-03-26)

Each tool is self-contained: own package, own pyproject.toml, own dependencies.
Tools communicate through MCP, CLI subprocess, or HTTP — never shared Python imports.

**Rationale:** DDD bounded contexts communicate through defined interfaces. Tools are
black boxes to the engine. This allows polyglot tools (different languages per tool)
and independent deployment.

**libs/ creation trigger:** Two or more tools duplicating non-trivial logic NOT covered
by MCP bridge. Don't create preemptively.

### Folder Convention (2026-03-26)

- `spike/` — frozen proof-of-concepts. Reference only, not imported by production code.
- `engine/` — orchestration layer (Conductor, Dispatcher, Auditor, Lens). Sits above tools.
- `tools/<name>/` — self-contained capabilities. Each has own package structure.
- `docs/research/` — design decisions, benchmarks, architecture docs.
- `<folder>/.memories/` — per-folder QUICK.md + KNOWLEDGE.md for agent context injection.

### Search Provider Strategy (2026-03-26)

Protocol-based: `SearchEngine` interface, multiple implementations.
- **Firecrawl** — first provider (already available via MCP skill), used to validate pipeline
- **SearXNG** — target local-first provider (Docker, future)
- Firecrawl extraction available as optional `Extractor` alongside `OllamaExtractor`

### Phase Plan

| Phase | Scope | Status |
|-------|-------|--------|
| 1 — Spike | Extraction pipeline + model benchmarks | Complete |
| 2A | Search integration (Firecrawl → existing pipeline) | Next |
| 2B | Simple orchestrator (proto-Conductor, config-driven) | After 2A |
| 3+ | Full agent architecture, knowledge store, CLI, MCP | Future |
