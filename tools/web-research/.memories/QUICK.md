# tools/web-research/ — Quick Memory

*Working memory for this tool. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 2B complete (2026-04-06). All five pipeline gaps closed.
CLI: `web-research extract <url>` and `web-research search <query>`.

## Pipeline

```
Search (Firecrawl) → [domain filter] → Fetch (httpx|firecrawl) → [404 check] → Clean → [content guard] → Chunk → Extract (Ollama) → JSON
```

- **Search:** `FirecrawlSearchEngine` — Firecrawl CLI subprocess
- **Domain filter:** `filters.py` — blacklist loaded from `search/domain_blacklist.json`
- **Fetch:** `HttpxFetcher` (default) or `FirecrawlFetcher` for JS-rendered sites (`--fetcher firecrawl`)
- **404 check:** raises `ValueError` before cleaning if `status_code >= 400`
- **Content guard:** raises `ThinContentError` if cleaned text < `--min-chars` (default 200)
- **Extract:** `OllamaExtractor` → qwen3:14b default, structured JSON output
- **`--top N`:** means N *usable* results — loop continues past thin/errored pages

## Package Structure

```
web_research/
  extraction/   # fetcher, firecrawl_fetcher, cleaner, chunker, extractor, merger
  search/       # firecrawl.py, filters.py, domain_blacklist.json, protocols.py
  cli.py        # argparse entrypoint — extract + search subcommands
```

## Deeper Memory → KNOWLEDGE.md

- **Protocol Boundaries** — swappable components, same pattern as spike
- **Ollama Codegen Patterns** — verdicts from generating this package with local models
- **Phase 2B Decisions** — design rationale for each gap fix

## Parked Ideas

- **Auditor iteration control** — confidence threshold + iteration-aware prompt; revisit
  after 3.6 ships with real-run data. [ref:auditor-iteration-control-ideas] →
  `docs/auditor-iteration-control-ideas.md`
