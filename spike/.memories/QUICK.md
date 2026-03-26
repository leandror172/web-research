# spike/ — Quick Memory

*Working memory for this folder. Injected into agents operating here. Keep under 30 lines.*

## Status

Phase 1 complete (2026-03-26). Pipeline validated, findings written, merged to main.
No active work — spike is frozen. Next work happens in Phase 2 (search integration).

## Key Facts

- **Pipeline:** URL → fetch → clean → chunk → extract (per chunk) → merge → JSON
- **Extraction model:** qwen3:14b (best quality), qwen3:8b (best speed/quality)
- **Codegen model:** my-python-q3c30 (best), my-python-q25c14 (VRAM-only)
- **Insight:** Extraction and codegen need different models — task-aware selection validated
- **Chunking:** paragraph-boundary, model-aware context limits, merge with exact-match dedup

## Known Limitations

- Wikipedia 403 (TLS fingerprinting — needs real browser fetcher)
- Dedup is exact-match only (fuzzy/semantic deferred)
- Link URL extraction model-dependent
- Merge takes name/summary from first chunk only

## Deeper Memory

- `KNOWLEDGE.md` — accumulated findings, model rankings, architecture decisions
- `../../docs/research/extraction-model-benchmark.md` — full benchmark data
- `../../docs/research/python-codegen-model-benchmark.md` — codegen benchmark data
- `../README.md` — spike overview and usage
