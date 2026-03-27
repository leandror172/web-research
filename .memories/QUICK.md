# web-research/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents. Keep under 30 lines.*

## Status

Phase 2A complete (2026-03-27). Search + extraction pipeline working in tools/web-research/.
Phase 2B next — content guard, usable-result filtering, FirecrawlFetcher for JS sites.

## Repo Structure

```
web-research/
  spike/          # frozen — Phase 1 extraction proof-of-concept
  engine/         # future Phase 2B — Conductor, Dispatcher, Auditor, Lens
  tools/          # self-contained tools (polyglot, own deps each)
    web-research/ # Phase 2A — search + extraction pipeline (Python)
  docs/
```

## Key Rules

- **Tools don't import each other** — engine dispatches via MCP/CLI/HTTP
- **No shared Python libs** preemptively — MCP bridge is the integration layer
- **Watch for libs/ trigger:** two+ tools duplicating non-trivial non-MCP logic
- **Per-folder .memories/** — QUICK.md (working) + KNOWLEDGE.md (semantic)

## Deeper Memory → KNOWLEDGE.md

- **Tool Isolation** — no shared imports, MCP is integration layer, libs/ trigger
- **Folder Convention** — spike/, engine/, tools/, docs/, .memories/
- **Search Provider Strategy** — Protocol-based, Firecrawl first, SearXNG later
- **Phase Plan** — 1 (done) → 2A (search) → 2B (orchestrator) → 3+ (agents)

Also: `engine/.memories/` (orchestration architecture), `spike/.memories/` (extraction findings),
`docs/research/memory-architecture-design.md` (memory system design)
