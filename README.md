# web-research

A local-model-powered web research tool. Searches the web, fetches pages, and extracts
structured information using 7–14B parameter LLMs running locally via
[Ollama](https://ollama.com) on consumer hardware (RTX 3060 12 GB).

Built to progressively become more autonomous — starts supervised, delegates more over
time. Knowledge compounds across research sessions.

## Why local models?

Running extraction locally means no API costs, no rate limits, no data leaving the
machine. The constraint is VRAM — 12 GB limits model size to ~14B parameters (dense)
or ~30B with RAM offloading. Phase 1 benchmarks proved this is enough for reliable
structured extraction from web pages.

## Architecture

```
Search (Firecrawl) → Fetch (httpx) → Clean (trafilatura) → Chunk → Extract (Ollama) → Knowledge store
                                                                              ↑
                                                          Conductor loop driven by Auditor verdicts
```

Every pipeline step implements a **Python Protocol** — independently callable,
implementations swappable. Adding a new search provider or fetcher means implementing
one interface; nothing else changes.

```
web-research/
├── engine/              # orchestration layer (planned — Dispatcher, Lens)
├── tools/
│   └── web-research/    # search + extraction + knowledge pipeline
│       └── web_research/
│           ├── extraction/   # fetch, clean, chunk, extract, merge
│           ├── search/       # search engine protocol + Firecrawl impl
│           ├── knowledge/    # SQLite knowledge store (persists across sessions)
│           ├── auditor/      # sufficiency review — heuristic gate + model checker
│           ├── conductor.py  # iterative research loop driven by Auditor verdicts
│           ├── mcp/          # FastMCP server — research_url, search_topic, query_knowledge
│           └── cli.py        # CLI entry point
└── docs/research/       # design decisions, benchmarks, architecture
```

### Bounded-context design

Tools are self-contained packages (own `pyproject.toml`, own dependencies). They
communicate through defined interfaces — CLI, HTTP, or MCP — never shared Python
imports. This allows polyglot tools and independent deployment.

The orchestration layer has four agents modeled as DDD bounded contexts:

| Agent | Responsibility | Status |
|-------|---------------|--------|
| **Conductor** | Manages research lifecycle — iterates until Auditor says sufficient | Live |
| **Auditor** | Sufficiency gate — heuristic pre-filter + local model verdict | Live |
| **Dispatcher** | Tool execution — calls tools, builds pipelines, selects models per task | Planned |
| **Lens** | Context proxy — summarizes results so the Conductor's context stays clean | Planned |

## Usage

Requires [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) with
`qwen3:14b` pulled, and [Firecrawl CLI](https://docs.firecrawl.dev/) for search.

```bash
cd tools/web-research

# Install
uv sync

# Extract structured data from a single URL
uv run web-research extract https://docs.crawl4ai.com

# Search the web and extract from top results (single round)
uv run web-research search "python asyncio best practices" --top 3 --no-audit

# Iterative research — Conductor loop, stops when Auditor says sufficient
uv run web-research search "python asyncio best practices" --max-iterations 3

# Focused extraction — extract only what's relevant to a specific question
uv run web-research extract https://example.com --prompt-type focused --focus "installation steps"

# Verbose logging
uv run web-research search "httpx" --log-level INFO
```

Output is saved as JSON files in `output/`, one per URL, and persisted to the SQLite
knowledge store (`output/knowledge.db`) for reuse across sessions.

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `qwen3:14b` | Ollama model for extraction |
| `--prompt-type` | `open` | `open` (general) or `focused` (targeted) |
| `--focus` | — | Focus question (required when `--prompt-type focused`) |
| `--cleaner` | `trafilatura` | HTML cleaner (`trafilatura` or `html2text`) |
| `--top` | `3` | Number of search results to extract per iteration (search only) |
| `--limit` | `5` | Number of search results to fetch (search only) |
| `--max-iterations` | `3` | Max Conductor iterations before stopping (search only) |
| `--no-audit` | off | Skip Auditor; run a single search+extract round (search only) |
| `--output-dir` | `output` | Directory for JSON output |
| `--log-level` | `WARNING` | Logging verbosity: `DEBUG` / `INFO` / `WARNING` / `ERROR` |

### Dev commands

```bash
make test    # run the full pytest suite
make logs    # tail -F all MCP server session logs
```

### MCP server

The tool exposes three MCP tools to Claude Code:

| Tool | Description |
|------|-------------|
| `research_url` | Fetch and extract a URL; returns cached result if already known |
| `search_topic` | Iterative research loop — same Conductor logic as the CLI |
| `query_knowledge` | Query the local SQLite knowledge store |

The server runs via stdio transport, launched automatically by Claude Code. Logs are
written to `output/mcp-server-{pid}.log` (one file per session). Set `WR_LOG_LEVEL`
in `.mcp.json` to `DEBUG` or `INFO` to increase verbosity.

## Model benchmarks

Phase 1 benchmarked 7 extraction models and 8 code generation personas. Full results:
`docs/research/extraction-model-benchmark.md` and `docs/research/python-codegen-model-benchmark.md`.

**Extraction models** (ranked by quality on RTX 3060 12 GB):

| Rank | Model | Why |
|------|-------|-----|
| 1 | qwen3:14b | Best quality — only model to identify top-level topics across chunked documents |
| 2 | qwen3:8b | Best speed/quality ratio, smallest VRAM footprint |
| 3 | qwen2.5-coder:14b | Reliable, no hallucination on empty input |
| 4 | deepseek-coder-v2:16b | Fastest, but consistently shallower extraction |

Three models were excluded: deepseek-r1:14b (hallucinated content from empty input —
a safety risk for unsupervised pipelines), qwen3:30b-a3b (MoE routing overhead made
it slower than dense 14B on 12 GB VRAM), and qwen3.5:9b (returned placeholder text
on all tasks).

**Critical insight:** Extraction and code generation need different models.
Code-specialized models dominate codegen; general-purpose models dominate extraction.
A single "best model" doesn't exist — it depends on the task.

## What works and what doesn't

| Content type | Status | Notes |
|---|---|---|
| Static HTML docs | Works well | Primary use case — reliable fetch, clean, and extract |
| Wiki pages | Works well | Handles large pages via chunking + merge |
| Discourse forums | Works | trafilatura strips noise effectively |
| JS-rendered (SPAs) | Poor | httpx gets thin content — needs browser-based fetcher |
| Paywalled sites | Fails | No mitigation beyond domain filtering |

## Project status

| Phase | Scope | Status |
|-------|-------|--------|
| 1 — Spike | Extraction pipeline + model benchmarks | Complete |
| 2A — Search | Search integration + CLI | Complete |
| 2B — Content quality | Content guard, domain filtering, JS-rendered site support | Complete |
| 3.3 — Knowledge store | SQLite knowledge store, persists across sessions | Complete |
| 3.4 — Auditor | Sufficiency review — heuristic gate + model checker (qwen3:14b) | Complete |
| 3.5 — MCP server | Claude Code integration (`research_url`, `search_topic`, `query_knowledge`) | Complete |
| 3.6 — Conductor | Iterative research loop driven by Auditor verdicts | Complete |
| Next | CLI batch mode, JSONL event log, heuristic threshold tuning | Planned |

## Design documents

Architecture decisions, benchmarks, and design rationale are in `docs/research/`.
Each folder also has a `.memories/` directory with `QUICK.md` (current status) and
`KNOWLEDGE.md` (accumulated decisions) — a per-folder context system modeled on
cognitive memory types.

## Related projects

This is part of a three-project portfolio:

- **web-research** (this repo) — local-model web research tool
- **LLM platform** — Ollama infrastructure, model personas, MCP bridge, Claude Code
  configuration. Provides the foundation this project runs on.
- **Expense classifier** — ML classification project (separate domain)

## License

Not yet specified.
