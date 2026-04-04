# spike/ — Knowledge (Semantic Memory)

*Accumulated findings from spike development. Stable facts — not tied to a specific session.
Read on demand, not injected into agents.*

## Model Rankings

### Extraction (7 models × 5 URLs × 2 tasks)

| Rank | Model | Strengths | Weaknesses |
|------|-------|-----------|------------|
| 1 | qwen3:14b | Best quality, only model to identify top-level topic on huge docs | Slowest |
| 2 | qwen3:8b | Best speed/quality ratio, smallest footprint | Less depth on large docs |
| 3 | qwen2.5-coder:14b | Reliable, no hallucination on empty input | Code-oriented, less natural language insight |
| 4 | deepseek-coder-v2:16b | Fastest | Consistently shallower extraction |

**Excluded models and why:**
- deepseek-r1:14b — hallucinated content when given empty input (dangerous for unsupervised use)
- qwen3:30b-a3b — 2-3x slower than 14b with no quality gain (MoE overhead on RTX 3060)
- qwen3.5:9b — returned placeholder text `"..."` or timed out on all tasks

### Code Generation (8 personas × 2 tasks × 3 runs)

| Rank | Persona | Base Model |
|------|---------|------------|
| 1 | my-python-q3c30 | qwen3-coder:30b (needs RAM offloading, timeout=300) |
| 2 | my-python-q25c14 | qwen2.5-coder:14b (VRAM-only, fast) |
| 3 | my-python-dsc16 | deepseek-coder-v2:16b |

## Architecture Decisions

- **Protocol-based boundaries** — each pipeline step implements a Protocol, independently callable
- **Toolkit pattern** — not a framework, a bag of composable tools
- **Data vs code boundary** — model config in JSON (`models.json`), not Python dicts
- **Chunking strategy** — paragraph-boundary splitting with configurable overlap; context window discovered via Ollama API → JSON override → hardcoded fallback

## Pipeline Evolution

1. **v1 (session 2-3):** fetch → clean → extract → save. Naive — sent full HTML to model.
2. **v2 (session 3):** Added trafilatura cleaning, but still truncated at 6K chars.
3. **v3 (session 4):** Model-aware chunking + merge. Queries Ollama for context window. Chunks at paragraph/sentence boundaries. Merges per-chunk results (dedup lists, merge dicts).

## Failure Modes Discovered

- **Wikipedia 403:** Not just User-Agent — TLS fingerprinting. httpx fingerprint differs from browsers. Needs Crawl4AI, Playwright, or Firecrawl.
- **Cold-start timeouts:** First Ollama call after model load takes 10-30s extra. Mitigated with `warm_model` MCP tool.
- **Empty input hallucination:** deepseek-r1:14b generates plausible-looking but fabricated content when given empty/minimal input. Critical safety issue for unsupervised pipelines.
- **MoE on limited VRAM:** qwen3:30b-a3b (MoE, 3B active) was slower than dense 14B on RTX 3060 12GB. Active params fit VRAM but expert routing overhead dominates.
