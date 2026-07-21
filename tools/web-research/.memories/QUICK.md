# tools/web-research/ — Quick Memory

*Working memory for this tool. Injected into agents operating here. Keep under 40 lines.*

## Status

Phase 3 complete incl. 3.2 event log (2026-07-02). Conductor + Auditor + MCP server live.
CLI: `web-research extract <url>` and `web-research search <query>`.
Research sessions write JSONL audit trails to `output/events/events-{session_id}.jsonl`.

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
  events.py     # EventLog protocol, JsonlEventLog, default_event_log factory
  cli.py        # argparse — extract + search subcommands; --log-level per subcommand
```

## Dev Commands

```bash
# NOTE: the Makefile lives at the REPO ROOT — run these from there,
# not from tools/web-research/ (which has no Makefile).
make test    # uv run --group dev pytest (172 tests, 14 modules)
make logs    # tail -F output/mcp-server-*.log
```

## Parked / Revisit

- **Auditor loop tuning** — unblocked: real-run data arrived (10 sessions, 2026-07-11).
  The heuristic gate short-circuits the loop in 6/10 runs; Ideas 1–2 target the *opposite*
  failure mode and are no longer the priority. → KNOWLEDGE.md § "Heuristic Gate
  Short-Circuits the Loop"; task (T-07). [ref:auditor-iteration-control-ideas]

## Deeper Memory → KNOWLEDGE.md

- Protocol Boundaries, Ollama Codegen Patterns, Phase 2B Decisions
- Auditor design (cascade, YAML renderer, heuristic asymmetry)
- Conductor design (iterator pattern, callback hooks, MCP stdout constraint)
- Progress logging architecture
- Event log design (finally guarantee, stop-reason taxonomy, session scoping)
