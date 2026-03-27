# tools/web-research/ — Quick Memory

*Working memory for this tool. Injected into agents. Keep under 30 lines.*

## Status

Phase 2A complete (2026-03-27). Search + extraction pipeline working.
CLI: `extract <url>` and `search <query>` subcommands. Package: `web_research`.

## Key Facts

- **Search:** FirecrawlSearchEngine (CLI subprocess, JSON output)
- **Fetch:** HttpxFetcher (browser UA) — JS-rendered sites get thin content
- **Clean:** trafilatura (primary), html2text (fallback/comparison)
- **Extract:** OllamaExtractor → qwen3:14b (default)
- **Output:** JSON per URL to output/ dir

## Known Gaps (see docs/capabilities.md)

- No content guard — extracts even 0-char pages (wasteful)
- JS-rendered sites (YouTube, Reddit, SPAs) — trafilatura gets near-nothing
- `--top N` extracts first N results, not N usable results
- 404 pages not detected before extraction

## Deeper Memory → KNOWLEDGE.md

- **Architecture Decisions** — Protocol boundaries, search provider strategy
- **Ollama Codegen Patterns** — verdicts from code generation, lessons learned

Also: `docs/capabilities.md` (content type × quality matrix, tested configs, known gaps)
