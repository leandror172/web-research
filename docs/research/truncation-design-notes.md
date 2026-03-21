# Truncation Design — Open Questions

*2026-03-21. User flagged questions about the current truncation approach. Discuss next session.*

## Current Implementation

In `spike/extract.py`, line 33-36:

```python
MAX_CHARS = 6000
text = content.text
if len(text) > MAX_CHARS:
    print(f"Truncating {len(text)} → {MAX_CHARS} chars")
    text = text[:MAX_CHARS]
```

### Why 6000 chars?

- Models tested have 8K-32K context windows (varies by model)
- The extraction prompt itself uses ~200-400 tokens (~800-1600 chars)
- 6000 chars ≈ 1500 tokens, leaving ~6500 tokens for the model's response + prompt overhead
- This is a conservative estimate; some models could handle more

### What's wrong with naive truncation

1. **Cuts mid-sentence / mid-section** — the model sees an incomplete thought at the boundary
2. **Positional bias** — only content from the top of the page is seen. For many pages, the most important content is in the middle (after intro/nav)
3. **No awareness of structure** — doesn't respect heading boundaries, paragraph breaks, or semantic units
4. **Fixed limit ignores model capability** — qwen3:14b has 32K context, qwen3:8b has 32K too, but smaller models may use context less effectively. The limit should potentially be model-aware.
5. **Loses content entirely** — for a 43K char page (Arch Wiki), we see only 14% of the content. No mechanism to process the rest.

### Alternatives to explore

| Approach | How it works | Pros | Cons |
|----------|-------------|------|------|
| **Naive truncation** (current) | `text[:6000]` | Simple, predictable | Loses 86%+ of long pages |
| **Smart truncation** | Cut at last complete paragraph/heading before limit | Preserves coherence | Still loses most content |
| **Chunking + merge** | Split into N chunks, extract each, merge results | Sees all content | N× model calls, merge logic needed |
| **Two-pass** | First pass: summarize/outline full doc. Second pass: extract from summary. | Handles any length | 2× latency, summary may lose detail |
| **Relevance-based** | Use focus directive to select relevant sections before extraction | Sees most relevant content | Needs a "section selector" step |
| **Model-aware limits** | Set MAX_CHARS based on model's actual context window | Uses each model's full capacity | Need to maintain a model→context map |

### Where truncation happens in the pipeline

```
Fetcher → Cleaner → [TRUNCATION] → Extractor → OutputWriter
```

Currently truncation is in `extract.py` (the orchestration script), not in a protocol component. This means:
- It's not pluggable — can't swap truncation strategies
- It's not visible to the Dispatcher — can't choose a strategy per-task
- It couples the pipeline script to a specific content-length policy

A proper design might make truncation its own protocol step, or make it a parameter of the Extractor (since the Extractor knows which model it's using and therefore what context window is available).

### Relationship to the Cleaner

Trafilatura already does content extraction (removes nav, footer, ads). So the input to truncation is already "cleaned" content. But trafilatura can still return 43K chars for a long article. The question is whether to:
- Truncate after cleaning (current) — simple, but blind
- Make the Cleaner responsible for length management — it already understands document structure
- Add a new step between Cleaner and Extractor — keeps concerns separated

### Context from the benchmark

| URL | Raw HTML | After trafilatura | After truncation (6K) | % seen |
|-----|----------|-------------------|----------------------|--------|
| crawl4ai.com | ~50K | 4,723 | 4,723 (no truncation) | 100% |
| huggingface.co | ~30K | 3,513 | 3,513 (no truncation) | 100% |
| htmx.org | ~15K | 2,554 | 2,554 (no truncation) | 100% |
| MCP llms-full.txt | ~1.1M | 1,094,699 | 6,000 | 0.5% |
| Arch Wiki (Pacman) | ~139K | 43,027 | 6,000 | 14% |

For 3 of 5 test URLs, truncation doesn't even trigger. The issue is specifically with long-form content (documentation, wiki articles, large markdown files).
