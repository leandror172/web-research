# web-research/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 2A complete (2026-03-27). Search + extraction pipeline working end-to-end.
Phase 2B next — content quality guard, smarter result filtering, JS-rendered site support.

## What This Project Is

A local-model-powered web research tool. It searches the web, fetches pages, and uses
7-14B parameter LLMs (running locally via Ollama on an RTX 3060 12GB) to extract
structured information. Designed to progressively become more autonomous — starts
supervised, delegates more over time. Knowledge compounds across research sessions.

## Repo Structure

```
web-research/
  spike/          # frozen — Phase 1 extraction proof-of-concept (model benchmarks, pipeline design)
  engine/         # placeholder — Phase 2B orchestration (Conductor, Dispatcher, Auditor, Lens)
  tools/          # self-contained tools (polyglot, own dependencies each)
    web-research/ # Phase 2A — search + extraction pipeline (Python, uv)
  docs/research/  # design decisions, benchmarks, architecture docs
```

## Key Rules

- **Tools don't import each other** — engine dispatches via protocol-based interfaces (CLI/HTTP/MCP)
- **Per-folder .memories/** — QUICK.md (always loaded) + KNOWLEDGE.md (on demand)
- **Local models first** — Ollama for extraction/codegen; frontier models (Claude) optional

## Deeper Memory → KNOWLEDGE.md

- **Tool Isolation** — bounded-context architecture, no shared imports
- **Search Provider Strategy** — Protocol-based, Firecrawl first, local SearXNG planned
- **Phase Plan** — 1 (spike) → 2A (search, done) → 2B (orchestrator) → 3+ (agents)
- **Cross-Repo Connections** — ties to LLM platform and expense classifier projects
