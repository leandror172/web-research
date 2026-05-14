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

## Phase 2B Decisions (2026-04-06)

All five gaps closed. Key design choices:

| Gap | Solution | Rationale |
|---|---|---|
| Content guard | `ThinContentError(ValueError)` raised in `extract_single_url` | Typed exception lets callers handle thin vs other errors differently |
| `--top N` semantics | Loop with `usable_count`, iterate all results | Can't use slice — stopping condition depends on runtime outcomes |
| FirecrawlFetcher | `firecrawl scrape <url> --format html --json` subprocess | Fits `Fetcher` Protocol; rendered HTML flows unchanged into cleaner |
| 404 detection | `status_code >= 400` check before cleaning | httpx doesn't raise on 4xx; error page HTML would silently pollute extraction |
| Domain blacklist | `search/domain_blacklist.json` + `filters.py` loader | Data/code boundary — agents edit JSON, not Python; `lru_cache` on load |

`FirecrawlFetcher` JSON output has a `Scrape ID: ...` prefix before the JSON payload — use `stdout.find("{")` to locate the JSON start.

## Auditor Design (Phase 3.4, 2026-04-13)

Two-stage cascade: heuristic gate → model checker. Heuristic gates `insufficient` only
(not enough entries / zero confidence signals) — it cannot judge content quality.
Model checker uses qwen3:14b with YAML renderer (production default).

**YAML vs Prose renderer A/B (4 queries, temperature=0):** Prose is systematically more
optimistic — calls `sufficient/high` where YAML calls `insufficient/medium` on identical
corpora. YAML conservatism is the right property for a research tool (over-stopping is
the failure mode, not under-stopping).

**Prompt template:** external `.md` file (`auditor/prompts/sufficiency.md`), loaded at
runtime. Iterate wording without touching code. Literal JSON braces in format strings
must be `{{ }}` escaped.

## Conductor Design (Phase 3.6, 2026-04-29)

`iterate()` is a generator yielding `IterationResult` per round. Stopping conditions:
audit failed, max iterations reached, verdict sufficient, no recommended queries, no
new URLs. `research_topic()` drains it into a `ResearchResult`.

**Iterator pattern rationale:** the CLI can consume results one at a time and print
progress between yields; the MCP server calls `research_topic()` and gets the full
result at once. Same core logic, two consumption patterns.

## Progress Logging Architecture (2026-05-07)

**CLI progress:** `iterate()` exposes `on_iteration_start(iteration, max, query)` and
`on_pre_audit(query)` optional callbacks. CLI wires print lambdas; MCP passes `None`.
Callbacks, not prints in conductor, because MCP uses stdio — any `print()` in library
code corrupts the JSON-RPC framing.

**MCP logging:** `logging.FileHandler` writing to `output/mcp-server-{pid}.log`. Per-PID
file (not rotating) — `RotatingFileHandler` is not multi-process safe; concurrent
Claude Code sessions would corrupt each other's log on rotation. `WR_LOG_LEVEL` env
var (set in `.mcp.json`), `WR_LOG_FILE` for custom path.

**CLI logging:** `--log-level` flag on each subparser (not root parser) — argparse
requires root-level flags before the subcommand; per-subparser flag works in any
position. `logging.basicConfig` in `main()` activates the root logger.

**Dev convenience:** `Makefile` at repo root — `make logs` (`tail -F output/mcp-server-*.log`),
`make test`. `-F` not `-f` — follows by name so it survives log rotation.
