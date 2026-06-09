# tools/web-research/ — Quick Memory

*Working memory for this tool. Injected into agents operating here. Keep under 40 lines.*

## Status

Phase 3 complete (2026-05-07). Conductor + Auditor + MCP server all live.
CLI: `web-research extract <url>` and `web-research search <query>`.

## Pipeline

```
Search (Firecrawl) → [domain filter] → Fetch (httpx|firecrawl) → [404 check]
  → Clean → [content guard] → Chunk → Extract (Ollama) → Knowledge store (SQLite)
                                              ↑
                          Conductor loop — iterates until Auditor says sufficient
```

- **Conductor:** `conductor.py` — `iterate()` yields `IterationResult` per round; callbacks `on_iteration_start` / `on_pre_audit` for CLI progress output (MCP passes None — stdout is protocol channel)
- **Auditor:** `auditor/` — heuristic gate (signals) → model checker (qwen3:14b, YAML renderer); gates `insufficient` only
- **MCP server:** `mcp/server.py` — FastMCP stdio; logs to `output/mcp-server-{pid}.log`; `WR_LOG_LEVEL` env var
- **Domain filter:** `filters.py` — blacklist from `search/domain_blacklist.json`
- **`--top N`:** N *usable* results per iteration — loops past thin/errored pages

## Package Structure

```
web_research/
  extraction/   # fetcher, firecrawl_fetcher, cleaner, chunker, extractor, merger
  search/       # firecrawl.py, filters.py, domain_blacklist.json, protocols.py
  knowledge/    # store.py — SQLite, save/query/has_url/recent
  auditor/      # signals.py, renderers.py, model_checker.py, auditor.py, prompts/sufficiency.md
  mcp/          # server.py — research_url, search_topic, query_knowledge
  conductor.py  # iterate() + research_topic() + build_default_auditor()
  cli.py        # argparse — extract + search subcommands; --log-level per subcommand
```

## Dev Commands

```bash
make test    # uv run --group dev pytest (132 tests)
make logs    # tail -F output/mcp-server-*.log
```

## Parked / Revisit

- **Auditor loop tuning** — confidence threshold (Idea 1) vs iteration-aware prompt (Idea 2); 3.6 is shipped, revisit with real-run log data. Task 3.7 in `.claude/tasks.md`. [ref:auditor-iteration-control-ideas]

## Deeper Memory → KNOWLEDGE.md

- Protocol Boundaries, Ollama Codegen Patterns, Phase 2B Decisions
- Auditor design (cascade, YAML renderer, heuristic asymmetry)
- Conductor design (iterator pattern, callback hooks, MCP stdout constraint)
- Progress logging architecture
