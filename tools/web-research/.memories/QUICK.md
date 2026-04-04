# tools/web-research/ — Quick Memory

*Working memory for this tool. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 2A complete (2026-03-27). Search + extraction pipeline working end-to-end.
CLI: `web-research extract <url>` and `web-research search <query>`.

## Pipeline

```
Search (Firecrawl) → Fetch (httpx) → Clean (trafilatura) → Chunk → Extract (Ollama) → JSON
```

- **Search:** `FirecrawlSearchEngine` — calls Firecrawl CLI as subprocess, parses JSON output
- **Fetch:** `HttpxFetcher` — browser User-Agent, but no JS rendering
- **Clean:** trafilatura (primary), html2text (fallback for comparison)
- **Extract:** `OllamaExtractor` → qwen3:14b default, structured JSON output
- **Output:** one JSON file per URL in `output/` directory

## Package Structure

```
web_research/
  extraction/   # promoted from spike — fetcher, cleaner, chunker, extractor, merger
  search/       # Firecrawl search engine, SearchEngine protocol
  cli.py        # argparse entrypoint with extract + search subcommands
```

## Known Gaps (Phase 2B)

- No content guard — extracts even empty pages (wastes model time)
- JS-rendered sites (YouTube, Reddit, SPAs) return thin/empty content via httpx
- `--top N` extracts first N results, not N *usable* results
- 404 pages not detected before extraction

## Deeper Memory → KNOWLEDGE.md

- **Protocol Boundaries** — swappable components, same pattern as spike
- **Ollama Codegen Patterns** — verdicts from generating this package with local models
- **Phase 2B Gaps** — detailed gap list with planned mitigations
