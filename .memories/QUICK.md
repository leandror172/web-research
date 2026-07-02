# web-research/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 3.2 complete (2026-07-02). JSONL event log: `events.py`, Conductor emits lifecycle
events, `session_end` guaranteed via finally (stop-reason taxonomy incl. abandoned/error).
Queue-based Conductor (`queue_width=2`), MCP server live, Auditor shipped.
159 pytest tests passing. Next: 3.1 (CLI batch, optional), Phase 4 (Claude Code integration).

## What This Project Is

A local-model-powered web research tool. It searches the web, fetches pages, and uses
7-14B parameter LLMs (running locally via Ollama on an RTX 3060 12GB) to extract
structured information. Designed to progressively become more autonomous — starts
supervised, delegates more over time. Knowledge compounds across research sessions.

## Repo Structure

```
web-research/
  spike/          # frozen — Phase 1 extraction proof-of-concept (model benchmarks, pipeline design)
  engine/         # placeholder — still empty; orchestration (Conductor, Auditor) built inside tools/web-research/
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
- **Phase Plan** — 1 (spike) → 2A (search) → 2B (orchestrator) → 3 (Conductor+Auditor+MCP, done) → 3.7 (queue, done)
- **Cross-Repo Connections** — ties to LLM platform and expense classifier projects
