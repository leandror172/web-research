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
Search (Firecrawl) → Fetch (httpx) → Clean (trafilatura) → Chunk → Extract (Ollama) → JSON
```

Every pipeline step implements a **Python Protocol** — independently callable,
implementations swappable. Adding a new search provider or fetcher means implementing
one interface; nothing else changes.

```
web-research/
├── engine/              # orchestration layer (planned — Conductor, Dispatcher, Auditor, Lens)
├── tools/
│   └── web-research/    # search + extraction + knowledge pipeline
│       └── web_research/
│           ├── extraction/   # fetch, clean, chunk, extract, merge
│           ├── search/       # search engine protocol + Firecrawl impl
│           ├── knowledge/    # SQLite knowledge store (persists across sessions)
│           └── cli.py        # CLI entry point
└── docs/research/       # design decisions, benchmarks, architecture
```

### Bounded-context design

Tools are self-contained packages (own `pyproject.toml`, own dependencies). They
communicate through defined interfaces — CLI, HTTP, or MCP — never shared Python
imports. This allows polyglot tools and independent deployment.

The planned orchestration layer (`engine/`) has four agents modeled as DDD bounded
contexts:

| Agent | Responsibility |
|-------|---------------|
| **Conductor** | Manages research lifecycle — what to research, when to stop, state persistence |
| **Dispatcher** | Tool execution — calls tools, builds pipelines, selects models per task |
| **Auditor** | Sufficiency gate — reviews results, decides if more research is needed |
| **Lens** | Context proxy — summarizes results so the Conductor's context stays clean |

## Usage

Requires [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) with
`qwen3:14b` pulled, and [Firecrawl CLI](https://docs.firecrawl.dev/) for search.

```bash
cd tools/web-research

# Install
uv sync

# Extract structured data from a single URL
uv run web-research extract https://docs.crawl4ai.com

# Search the web and extract from top results
uv run web-research search "python asyncio best practices" --top 3

# Focused extraction — extract only what's relevant to a specific question
uv run web-research extract https://example.com --prompt-type focused --focus "installation steps"

# Use a different model
uv run web-research extract https://example.com --model qwen3:8b
```

Output is saved as JSON files in `output/`, one per URL.

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `qwen3:14b` | Ollama model for extraction |
| `--prompt-type` | `open` | `open` (general) or `focused` (targeted) |
| `--focus` | — | Focus question (required when `--prompt-type focused`) |
| `--cleaner` | `trafilatura` | HTML cleaner (`trafilatura` or `html2text`) |
| `--top` | `3` | Number of search results to extract (search only) |
| `--limit` | `5` | Number of search results to fetch (search only) |
| `--output-dir` | `output` | Directory for JSON output |

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
| 3 — Knowledge | SQLite store, JSONL log, Auditor, batch CLI | In progress |
| 4 — MCP | Claude Code integration (`research_url`, `search_topic`, `query_knowledge`) | Planned |

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
