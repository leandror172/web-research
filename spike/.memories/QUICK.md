# spike/ — Quick Memory

*Working memory for this folder. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 1 complete (2026-03-26). Frozen — reference only, not imported by production code.
Findings validated and carried forward into tools/web-research/.

## What This Proved

Local 7-14B models running on an RTX 3060 12GB can reliably extract structured information
from web pages. Quality is sufficient to build an automated research pipeline on top of.

## Pipeline

```
URL → HttpxFetcher → TrafilaturaCleaner → Chunker → OllamaExtractor (per chunk) → Merger → JSON
```

Each step implements a Protocol — independently callable, implementations swappable.

## Key Findings

- **Best extraction model:** qwen3:14b (only model to identify top-level topics across chunks)
- **Best speed/quality:** qwen3:8b (smallest footprint, good enough for most pages)
- **Best codegen model:** my-python-q3c30 (qwen3-coder:30b with custom persona)
- **Critical insight:** extraction and codegen need different models — task-aware selection validated
- **Chunking:** paragraph-boundary splitting, model-aware context limits from Ollama API

## Known Limitations

- Wikipedia blocks httpx (TLS fingerprinting — needs browser-based fetcher)
- Deduplication is exact-match only (fuzzy/semantic deferred)
- Merge takes name/summary from first chunk only

## Deeper Memory → KNOWLEDGE.md

- **Model Rankings** — 7 extraction models × 5 URLs, 8 codegen personas × 2 tasks
- **Pipeline Evolution** — v1 → v2 → v3, what changed and why
- **Failure Modes** — Wikipedia 403, cold-start, empty-input hallucination, MoE overhead
