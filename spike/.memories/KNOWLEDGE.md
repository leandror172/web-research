# spike/ — Knowledge (Semantic Memory)

*Accumulated findings from spike development. Stable facts — not tied to a specific session.*

## Model Rankings (2026-03-26)

### Extraction (7 models × 5 URLs × 2 task types)

| Rank | Model | Strengths | Weaknesses |
|------|-------|-----------|------------|
| 1 | qwen3:14b | Best quality; only model to identify top-level topic on huge docs | Slowest (~40s per chunk) |
| 2 | qwen3:8b | Best speed/quality ratio, smallest VRAM footprint | Less depth on large documents |
| 3 | qwen2.5-coder:14b | Reliable, no hallucination on empty input | Code-oriented, less natural language insight |
| 4 | deepseek-coder-v2:16b | Fastest inference | Consistently shallower extraction |

**Excluded models and why:**
- deepseek-r1:14b — hallucinated content when given empty input (dangerous for unsupervised use)
- qwen3:30b-a3b — 2-3x slower than dense 14b with no quality gain (MoE routing overhead on RTX 3060 12GB)
- qwen3.5:9b — returned placeholder text `"..."` or timed out on all test cases

### Code Generation (8 Ollama personas × 2 tasks × 3 runs)

| Rank | Persona | Base Model | Notes |
|------|---------|------------|-------|
| 1 | my-python-q3c30 | qwen3-coder:30b | Highest quality but needs RAM offloading (timeout=300) |
| 2 | my-python-q25c14 | qwen2.5-coder:14b | Best VRAM-only option, fast and consistent |
| 3 | my-python-dsc16 | deepseek-coder-v2:16b | Solid alternative |

**Key insight:** Extraction and codegen need different models. Code-specialized models
dominate codegen; general-purpose models dominate extraction. This validated the need
for task-aware model selection in the Dispatcher.

## Architecture Decisions (2026-03-26)

- **Protocol-based boundaries** — each pipeline step (Fetcher, Cleaner, Extractor,
  OutputWriter) implements a Python Protocol. Components are independently callable
  and swappable without changing the pipeline.
- **Toolkit pattern** — not a framework with a main loop, but a bag of composable
  tools. Any step can be called standalone or composed into different pipelines.
- **Data vs code boundary** — model configuration lives in JSON (`models.json`),
  not Python dicts. This lets AI agents safely edit model config without touching code.
- **Chunking strategy** — paragraph-boundary splitting with configurable overlap.
  Context window discovered dynamically: Ollama API → JSON override → hardcoded fallback.

## Pipeline Evolution

1. **v1 (session 2-3):** fetch → clean → extract → save. Naive — sent full HTML to model, truncated at model context limit.
2. **v2 (session 3):** Added trafilatura for HTML-to-text cleaning, but still truncated at 6K chars arbitrarily.
3. **v3 (session 4):** Model-aware chunking + merge. Queries Ollama API for actual context window size. Splits at paragraph/sentence boundaries. Merges per-chunk results with deduplication.

**What drove each change:** v1→v2: models choked on raw HTML tags. v2→v3: 6K truncation
lost most of the content on long pages; needed the model's actual context limit.

## Failure Modes Discovered

### Wikipedia 403
Not just a User-Agent issue — TLS fingerprinting. httpx's TLS fingerprint differs from
real browsers. Workaround: use a browser-based fetcher (Crawl4AI, Playwright, or Firecrawl).

### Cold-Start Timeouts
First Ollama call after model load takes 10-30s extra (loading weights into VRAM).
Mitigated with `warm_model` MCP tool call before starting extraction.

### Empty Input Hallucination
deepseek-r1:14b generates plausible-looking but completely fabricated content when given
empty or minimal input. This is a critical safety issue for unsupervised pipelines —
the model confidently returns structured data that looks real but has no source material.

### MoE on Limited VRAM
qwen3:30b-a3b (Mixture of Experts, 3B active parameters) was slower than the dense 14B
model on RTX 3060 12GB. Active params fit in VRAM, but expert routing overhead dominated.
MoE architectures may need more memory bandwidth than a 12GB consumer GPU provides.
