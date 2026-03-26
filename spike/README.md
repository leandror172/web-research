# Extraction Spike — Findings & Verdict

*Phase 1 of web-research. Validates that local 7-14B models can reliably extract structured information from web pages.*

## Verdict

**Local extraction works.** A 14B model (qwen3:14b) running on an RTX 3060 12GB can extract structured, useful information from web pages with sufficient quality to build a research pipeline on top of.

Proceed to Phase 2 (search integration).

## Pipeline

```
URL → HttpxFetcher → TrafilaturaCleaner → Chunker → OllamaExtractor (per chunk) → Merger → JsonOutputWriter
```

Each step is a Protocol — independently callable, implementations swappable via parameters.

### Key Components

| File | Role |
|------|------|
| `protocols.py` | Protocol definitions + dataclasses (FetchResult, CleanResult, ExtractionConfig, ExtractionResult) |
| `fetcher.py` | HTTP fetcher (httpx, browser User-Agent) |
| `cleaners.py` | HTML→text (trafilatura primary, html2text fallback) |
| `chunker.py` | Paragraph-boundary chunking with configurable overlap |
| `models.py` | Model context-window lookup (Ollama API → JSON override → fallback) |
| `merger.py` | Combines N ExtractionResults (dedup lists, merge dicts, aggregate assessments) |
| `extractor.py` | Ollama `/api/chat` with JSON schema enforcement |
| `prompts.py` | Open + focused extraction prompts |
| `extract.py` | CLI entrypoint |

## Model Benchmarks

### Extraction (7 models × 5 URLs × 2 tasks)

| Priority | Model | Notes |
|----------|-------|-------|
| 1 | qwen3:14b | Best quality, only model to identify top-level topic on huge docs |
| 2 | qwen3:8b | Best speed/quality ratio, smallest footprint |
| 3 | qwen2.5-coder:14b | Reliable, no hallucination on empty input |
| 4 | deepseek-coder-v2:16b | Fastest, but consistently shallower |

**Excluded:** deepseek-r1:14b (hallucinated on empty input), qwen3:30b-a3b (2-3x slower, no quality gain), qwen3.5:9b (returned placeholders/timed out).

### Code Generation (8 personas × 2 tasks × 3 runs)

| Priority | Persona | Base Model |
|----------|---------|------------|
| 1 | my-python-q3c30 | qwen3-coder:30b |
| 2 | my-python-q25c14 | qwen2.5-coder:14b |
| 3 | my-python-dsc16 | deepseek-coder-v2:16b |

**Key insight:** Extraction and codegen need different models. Code-specialized models dominate codegen; general-purpose models dominate extraction. The Dispatcher should select models per-task.

Full results: `docs/research/extraction-model-benchmark.md`, `docs/research/python-codegen-model-benchmark.md`

## Pipeline Issues & Fixes

| Issue | Status | Fix |
|-------|--------|-----|
| Wikipedia 403 | Open | Needs real browser fetcher (Crawl4AI/Firecrawl) — TLS fingerprinting |
| Naive 6K truncation | Fixed | Model-aware chunking + merge (queries Ollama for context window) |
| Cold-start timeouts | Mitigated | Use `warm_model` before first call |
| Browser User-Agent | Fixed | Switched to browser-like UA string |

## Known Limitations

- **Deduplication is exact-match only** — "Supports X" vs "X support" treated as different items
- **Link URL extraction is model-dependent** — some models return full URLs, others return descriptions
- **Merge takes name/summary from first chunk** — may miss better descriptions in later chunks
- **Single-threaded extraction** — chunks processed sequentially (could parallelize)

## Running

```bash
# Single URL
uv run python -m spike.extract https://crawl4ai.com --model qwen3:14b

# Multiple URLs from file
uv run python -m spike.extract --urls-file spike/urls.txt --model qwen3:14b

# Focused extraction
uv run python -m spike.extract https://example.com --prompt-type focused --focus "installation steps"
```

Output goes to `spike/output/` as JSON files.
