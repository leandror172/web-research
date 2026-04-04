# tools/web-research/ — Knowledge (Semantic Memory)

*Accumulated decisions and findings for this tool. Read on demand.*

## Architecture Decisions

### Protocol Boundaries
Each pipeline step implements a Protocol (Fetcher, Cleaner, Extractor, OutputWriter, SearchEngine).
Independently callable, implementations swappable via parameters. Same pattern as spike.

### Search Provider Strategy
- Firecrawl CLI (subprocess) for now — authenticated, free tier (500 credits)
- SearXNG planned as local-first replacement — Docker setup deferred
- `FirecrawlSearchEngine` returns `list[SearchResult]` (url, title, description, position)

### Package Structure
`web_research/extraction/` — promoted from spike (all imports updated)
`web_research/search/` — new in Phase 2A
`web_research/cli.py` — argparse, `extract` + `search` subcommands
`scripts/` — diagnostic scripts (compare_cleaners, inspect_chunks, smoke_test)
`docs/` — capabilities.md (living capability map)

## Ollama Codegen Patterns (Phase 2A lessons)

From generating 10 files with my-python-q25c14:

| Pattern | Verdict | Fix |
|---|---|---|
| Simple promotion (update imports only) | ACCEPTED | None needed |
| Promotion with caller not in context | REJECTED | Include callers as context_files — model changed API |
| New file from spec | IMPROVED | Hallucinated non-existent functions; unsafe JSON parsing used |
| File with many helpers | IMPROVED | Added unused imports; truncated on long files |
| Concurrent Ollama calls (3 at once) | WARN | Serialize — concurrent calls cause cold-start contention |

**Key rule:** When promoting code that's called by other code, include the callers as `context_files`.

## Phase 2B Gaps (to address next)

1. **Content guard** — skip URLs with <N chars after cleaning, try next result
2. **`--top N` semantics** — should mean N usable results, not N attempts
3. **FirecrawlFetcher** — use Firecrawl's scrape for JS-rendered sites (optional Fetcher impl)
4. **404 detection** — check `status_code` before cleaning
5. **Search result filtering** — domain blacklist or content-type hints to skip YouTube/Reddit
