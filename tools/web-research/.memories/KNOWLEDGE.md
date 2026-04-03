# tools/web-research/ — Knowledge (Semantic Memory)

*Accumulated decisions and findings for this tool. Read on demand.*

## Protocol Boundaries (2026-03-27)

Each pipeline step implements a Protocol: Fetcher, Cleaner, Extractor, OutputWriter,
SearchEngine. Implementations are swappable via parameters — same pattern established
in the spike, carried forward here.

**Rationale:** The spike proved that Protocol-based boundaries make the pipeline
composable. Adding a new fetcher (e.g., FirecrawlFetcher for JS sites) means
implementing one interface — nothing else changes.

**Implication:** New capabilities are additive, not disruptive. The search provider
can change from Firecrawl to SearXNG without touching extraction code.

## Search Provider Strategy (2026-03-27)

Firecrawl search is the first implementation. It runs via CLI subprocess (`npx
firecrawl`), returning JSON with url, title, description, and position fields.
Firecrawl's free tier provides 500 credits for validation.

SearXNG (self-hosted via Docker) is the planned local-first replacement — aligns
with the project's goal of running entirely on local infrastructure.

**Rationale:** Get the pipeline working with an available search backend before
investing in Docker infrastructure for SearXNG.

## Ollama Codegen Patterns (Phase 2A lessons, 2026-03-27)

This package was partially generated using local Ollama models (my-python-q25c14).
Each generated file was evaluated with a verdict (ACCEPTED/IMPROVED/REJECTED):

| Pattern | Verdict | Lesson |
|---|---|---|
| Simple code promotion (update imports only) | ACCEPTED | Works well for mechanical changes |
| Promotion with callers not in context | REJECTED | Model changed the API it couldn't see — always include callers as context_files |
| New file from specification | IMPROVED | Hallucinated non-existent functions; used unsafe JSON parsing |
| File with many helper functions | IMPROVED | Added unused imports; truncated output on long files |

**Key rule:** When using a local model to promote/refactor code that's called by other
code, include the calling files as `context_files` in the generate_code prompt.

## Content Type Quality Matrix (2026-03-27)

Detailed in `docs/capabilities.md`. Summary of what works and what doesn't:

| Content Type | Fetch+Clean | Extract | Notes |
|---|---|---|---|
| Static HTML docs | Good | Good | Primary use case, reliable |
| Wiki pages (non-Wikipedia) | Good | Good | Rich content, handles large pages via chunking |
| Discourse forums | Good | Medium | trafilatura strips noise well |
| JS-rendered (SPAs) | Poor | N/A | httpx gets thin content; needs browser-based fetcher |
| Paywalled sites | Failed | N/A | No mitigation — filter by domain or char count |

## Phase 2B Gaps (2026-03-27)

1. **Content guard** — skip URLs with <N chars after cleaning, try next search result
2. **`--top N` semantics** — should mean N usable results, not N attempts
3. **FirecrawlFetcher** — optional Fetcher implementation using Firecrawl's scrape API for JS-rendered sites
4. **404 detection** — check HTTP status_code before cleaning
5. **Search result filtering** — domain blacklist or content-type hints to avoid YouTube/Reddit/paywall URLs
