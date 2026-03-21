# spike/ — Quick Memory

*Injected when this folder is explored. Keep short — expand in docs/research/.*

## Status
- Spike functional: fetch→clean→extract→save pipeline works
- Extraction benchmark complete (7 models × 5 URLs × 2 tasks)

## Active Findings
- **Extraction priority:** qwen3:14b > qwen3:8b > qwen2.5-coder:14b > dsc16
- **Codegen priority is different:** q3c30 > q25c14 > dsc16 — task-aware model selection needed
- **deepseek-r1:14b hallucinated on empty input** — exclude from unsupervised extraction
- **qwen3.5:9b broken** — returned `"..."` or timed out on all tasks
- **trafilatura returned 0 bytes for Wikipedia** (403 + content extraction failure)
- **No content truncation** — 1MB doc sent to 8K-context models; only qwen3:14b identified top-level topic

## Pipeline Fixes Applied
- Content truncation: 6K char cap before extraction (MCP 1MB → now correctly extracts "MCP")
- User-Agent: switched to browser-like UA
- Wikipedia: 403 even with real UA — TLS fingerprinting, needs real browser fetcher (Crawl4AI/Firecrawl)
- Swapped Wikipedia test URL for Arch Wiki (wiki.archlinux.org) — works, rich content

## Remaining Gaps
- html2text comparison on pages where trafilatura fails
- Link URL extraction inconsistent across models
- Chunking for pages >6K (currently just truncates)

## Architecture Insight
- Different tasks → different optimal models → Dispatcher should select per-task
- Same task, multiple models → merge/compare results → higher quality extraction
- Model-selects-model: use a classifier to pick the best extractor for the content type
