# Extraction Model Benchmark

*2026-03-21. Tested 7 Ollama models for web content extraction quality across 5 URLs.*

---

## Summary

<!-- ref:extraction-model-priority -->
### Extraction Model Priority

**Best models for structured web extraction, in priority order:**

1. **qwen3:14b** — best overall quality, only model to identify top-level topic on huge documents, links include URLs
2. **qwen3:8b** — best speed/quality ratio, smallest footprint, most items extracted
3. **qwen2.5-coder:14b** — reliable, no hallucination on empty input, good focused extraction
4. **deepseek-coder-v2:16b** — fastest, but consistently shallower extraction (4-7 features vs 8)

**Do not use for extraction:**
- **deepseek-r1:14b** — hallucinated "PyTorch" from empty input (Wikipedia 403). Disqualifying for unsupervised research.
- **qwen3:30b-a3b** — 2-3x slower than qwen3:14b for comparable quality. MoE breadth didn't help.
- **qwen3.5:9b** — returned `"..."` placeholders or timed out. Unusable.

**Key insight:** Extraction rankings are inverted from codegen rankings. Code-specialized models (qwen3-coder:30b) dominate codegen; general-purpose models (qwen3:14b) dominate extraction. Different tasks need different models. § "Codegen vs Extraction" for comparison.
<!-- /ref:extraction-model-priority -->

---

## Test Setup

- **5 URLs** spanning different page types (§ "URL Selection Rationale")
- **7 models** tested per URL, 2 tasks each (open + focused extraction)
- **Focused prompt:** "installation and quickstart" on all URLs
- **Pipeline:** HttpxFetcher → TrafilaturaCleaner → OllamaExtractor → JsonOutputWriter
- **Ollama params:** `stream: false`, `temperature: 0.1`, JSON schema via `format` param
- **Timeout:** 120s per extraction call

### URL Selection Rationale

| URL | Type | Why chosen |
|-----|------|------------|
| `crawl4ai.com` | Tool landing page | Known content, well-structured, baseline |
| `huggingface.co` | Complex multi-domain | Many knowledge domains (models, datasets, spaces, inference) |
| `en.wikipedia.org/wiki/Large_language_model` | Rich Wikipedia | Footnote citations, internal links, long-form |
| `htmx.org` | Opinionated tech site | Mixes essays, docs, philosophy. Server-rendered. |
| `modelcontextprotocol.io/llms-full.txt` | Pure markdown file | ~1MB text file. Tests content-length handling. |

---

## Pipeline Issues Discovered

<!-- ref:extraction-pipeline-issues -->
### Pipeline Issues (Extraction Spike)

Three issues surfaced during the benchmark — these are pipeline problems, not model problems:

1. **Wikipedia 403 Forbidden:** `User-Agent: web-research-spike/0.1` blocked. Models received empty input. Fix: use a real browser User-Agent, or add a fallback fetcher.
2. **No content truncation:** MCP llms-full.txt is ~1MB / ~250K tokens. No truncation before sending to models with 8-16K context. Fix: add a truncation or chunking step to the pipeline.
3. **Cold-start timeouts on model switching:** Sequential benchmarking forces rapid model swaps. 3 failures (all recoverable). Fix: use `warm_model` before first call, or increase timeout.
<!-- /ref:extraction-pipeline-issues -->

---

## Full Results — Open Extraction

### crawl4ai.com (4,723 bytes cleaned)

| Model | Duration | Features | Links (w/ URLs) | Limitations | Name | Notes |
|-------|----------|----------|-----------------|-------------|------|-------|
| **qwen3:8b** | 34.8s | 8 | 5 (0) | 4 | Crawl4AI | Most items. Fast. |
| **qwen3:14b** | 59.4s | 8 | 4 (0) | 3 | Crawl4AI: Open-Source... | Full title captured |
| **qwen2.5-coder:14b** | 46.3s | 8 | 4 (0) | 3 | Crawl4AI | Reliable |
| **deepseek-coder-v2:16b** | 30.2s | 7 | 3 (0) | 2 | Crawl4AI: Open-Source... | Fastest. Fewer features. |
| **deepseek-r1:14b** | 61.6s | 8 | 4 (3) | 3 | Crawl4AI | Only one with link URLs |
| **qwen3:30b-a3b** | 84.1s | 8 | 3 (0) | 2 | Crawl4AI | Slowest. Same quality as 14b. |
| **qwen3.5:9b** | 65.8s | **1** | 1 (0) | 1 | Crawl4AI | **FAILED** — all `"..."` |

### huggingface.co (3,513 bytes cleaned)

| Model | Duration | Features | Links (w/ URLs) | Limitations | Notes |
|-------|----------|----------|-----------------|-------------|-------|
| **qwen3:8b** | 34.2s | 8 | 12 (0) | 4 | Most links extracted. "Hugging Face Platform" |
| **qwen3:14b** | 43.5s | 8 | 8 (0) | 1 | Noted "Python + JS for Transformers.js" |
| **qwen2.5-coder:14b** | 40.5s | 8 | 5 (0) | 4 | Solid |
| **deepseek-coder-v2:16b** | 19.5s | 4 | 3 (0) | 2 | Fastest. Only 4 features. |
| **deepseek-r1:14b** | 41.9s | 8 | 4 (0) | 3 | Good. Noted "Multiple languages" |
| **qwen3:30b-a3b** | 113.4s | 8 | 3 (0) | 2 | **113s** — very slow with RAM offloading |

### htmx.org (2,554 bytes cleaned)

| Model | Duration | Features | Links (w/ URLs) | Limitations | Notes |
|-------|----------|----------|-----------------|-------------|-------|
| **qwen3:8b** | 24.4s | 8 | 4 (0) | 1 | Fast, complete |
| **qwen3:14b** | 54.0s | 8 | 6 (6) | 3 | **All 6 links have URLs** |
| **deepseek-coder-v2:16b** | 18.1s | 4 | 2 (0) | 1 | Fast but shallow |
| **deepseek-r1:14b** | 48.2s | 8 | 3 (3) | 3 | Links have URLs |
| **qwen2.5-coder:14b** | — | — | — | — | TIMEOUT (cold start) |
| **qwen3:30b-a3b** | — | — | — | — | TIMEOUT (cold start + RAM offload) |

### modelcontextprotocol.io/llms-full.txt (~1MB cleaned — NO TRUNCATION)

| Model | Duration | Features | Links (w/ URLs) | Name | Notes |
|-------|----------|----------|-----------------|------|-------|
| **qwen3:14b** | 43.0s | 3 | 3 (3) | **Model Context Protocol (MCP)** | Only model to identify the overall topic |
| **qwen2.5-coder:14b** | 27.1s | 3 | 1 (1) | SEP-991 | Extracted from fragment |
| **deepseek-coder-v2:16b** | 28.4s | 4 | 2 (2) | SEP-994 | Extracted from fragment |
| **deepseek-r1:14b** | 68.4s | 5 | 0 (0) | SEP-991: Enable URL-based... | Detailed but wrong scope |
| **qwen3:30b-a3b** | 110.5s | 4 | 0 (0) | MCP SEP-991 & SEP-994 Summary | Partial topic identification |
| **qwen3:8b** | — | — | — | — | TIMEOUT (cold start) |

### en.wikipedia.org — Large language model (0 bytes — 403 Forbidden)

*Trafilatura received empty input. Tests model behavior on missing content.*

| Model | Behavior | Notes |
|-------|----------|-------|
| **qwen2.5-coder:14b** | "Not specified" | Correct — admitted no content |
| **qwen3:14b** | "N/A" | Correct |
| **qwen3:8b** | "N/A" | Correct |
| **qwen3:30b-a3b** | "No page content provided" | Correct — explicit about the problem |
| **deepseek-coder-v2:16b** | "Tool/Project/Library Name" | Returned schema placeholders |
| **deepseek-r1:14b** | **"PyTorch"** | **HALLUCINATED** an entire extraction from nothing |

---

## Full Results — Focused Extraction ("installation and quickstart")

### crawl4ai.com

| Model | Duration | Facts | Details | Links (URLs) | Assessment |
|-------|----------|-------|---------|-------------|------------|
| **deepseek-coder-v2:16b** | 13.7s | 9 | 5 | 3 (3) | high |
| **qwen3:8b** | 14.4s | 4 | 4 | 3 (2) | high (with reason) |
| **qwen2.5-coder:14b** | 17.4s | 3 | 3 | 4 (0) | High |
| **qwen3:14b** | 21.1s | 3 | 3 | 3 (0) | High (detailed reason) |
| **deepseek-r1:14b** | 42.8s | 3 | 2 | 3 (3) | high (with reason) |
| **qwen3:30b-a3b** | 52.8s | 3 | 4 | 2 (0) | high (with reason) |

### huggingface.co

| Model | Duration | Facts | Details | Links | Assessment | Notes |
|-------|----------|-------|---------|-------|------------|-------|
| **deepseek-coder-v2:16b** | 4.1s | 2 | 2 | 2 | medium | Fastest focused ever (4.1s!) |
| **qwen2.5-coder:14b** | 15.6s | 3 | 3 | 2 | medium | |
| **deepseek-r1:14b** | 17.9s | 2 | 2 | 3 | high | |
| **qwen3:8b** | 18.1s | 3 | 4 | 5 | medium (with reason) | |
| **qwen3:14b** | 24.5s | 3 | 2 | 4 | medium (with reason) | |
| **qwen3:30b-a3b** | 55.9s | 2 | 3 | 2 | **low** | Correctly assessed: "homepage, no install info" |

### htmx.org

| Model | Duration | Facts | Details | Links (URLs) | Assessment |
|-------|----------|-------|---------|-------------|------------|
| **deepseek-coder-v2:16b** | 5.8s | 4 | 4 | 4 (4) | high |
| **qwen3:8b** | 13.9s | 3 | 4 | 3 (3) | high (with reason) |
| **qwen2.5-coder:14b** | 18.3s | 3 | 3 | 3 (0) | high |
| **qwen3:14b** | 24.5s | 3 | 3 | 4 (0) | high (with reason) |
| **deepseek-r1:14b** | 27.5s | 2 | 2 | 2 (2) | high (with reason) |
| **qwen3:30b-a3b** | 80.5s | 3 | 5 | 4 (4) | high (with reason) |

### modelcontextprotocol.io/llms-full.txt

| Model | Duration | Facts | Details | Links (URLs) | Assessment |
|-------|----------|-------|---------|-------------|------------|
| **deepseek-coder-v2:16b** | 18.8s | 12 | 9 | 3 (3) | SEP-994 focused |
| **qwen3:8b** | 19.8s | 5 | 5 | 2 (0) | MCP overview |
| **qwen2.5-coder:14b** | 19.3s | 4 | 4 | 2 (0) | SEP-991 focused |
| **qwen3:14b** | 33.1s | 1 | 1 | 3 (3) | MCP framework overview |
| **deepseek-r1:14b** | 44.3s | 5 | 5 | 0 (0) | OAuth registration focused |
| **qwen3:30b-a3b** | 83.0s | 10 | 2 | 0 (0) | SEP comparison |

---

## Codegen vs Extraction

Rankings differ significantly between code generation and web extraction tasks:

| Model | Codegen Rank | Extraction Rank | Why |
|-------|-------------|-----------------|-----|
| qwen3-coder:30b | #1 | not tested | Code-specialized, not general extraction |
| qwen2.5-coder:14b | #2 | #3 | Strong at both, but general models edge it on extraction |
| deepseek-coder-v2:16b | #3 | #4 | Fast but shallow for extraction |
| qwen3:14b | #5 | **#1** | General knowledge + instruction following = best extractor |
| qwen3:8b | #7 | **#2** | Surprising: worst codegen tier, second-best extraction |
| deepseek-r1:14b | #4 | **excluded** | Hallucination on empty input disqualifies |
| qwen3:30b-a3b | #6 | #5 | Too slow for both tasks |
| qwen3.5:9b | #8 | **excluded** | Broken for both tasks |

**Implication:** The Dispatcher agent should select models per-task, not use one model for everything. § "Model Selection Architecture" in spike plan.

---

## Key Findings

1. **Extraction is a different skill than code generation.** General-purpose models (qwen3:14b) outperform code-specialized models (qwen2.5-coder:14b) at reading comprehension + structured output.

2. **deepseek-r1:14b is unsafe for autonomous research.** It hallucinated a complete PyTorch extraction when given no page content. All other models correctly returned N/A or empty. Reasoning models may "reason" their way into fabrication.

3. **qwen3:14b has the best topic identification.** On the 1MB MCP document (no truncation), it was the only model to identify the overall topic ("Model Context Protocol") rather than extracting from a random fragment.

4. **deepseek-coder-v2:16b trades depth for speed.** Consistently 4-7 features where others extract 8. Focused extraction as fast as 4.1s. Useful when speed matters more than completeness.

5. **qwen3:30b-a3b (MoE) offers no quality advantage** over qwen3:14b at 2-3x the latency. The wider knowledge base (30B parameters) didn't measurably improve extraction on any URL tested.

6. **Focused extraction works across all viable models.** All models (except qwen3.5:9b) correctly assessed relevance and extracted different content for the focused prompt vs open prompt.

7. **Link URL extraction is model-dependent.** qwen3:14b and deepseek-r1:14b include actual URLs in link objects; qwen3:8b and qwen2.5-coder:14b typically return descriptions only. Schema allows but doesn't require URLs.

8. **Assessment quality varies.** qwen3:30b-a3b correctly assessed HuggingFace as "low" relevance for "installation and quickstart" (it's a homepage, not a docs page). Others rated it "medium" or "high" — less accurate.

---

## Recommendations

### For the Spike → MVP Transition

1. **Add content truncation** — cap at ~6000 chars before sending to model (fits 8K context with prompt overhead)
2. **Fix User-Agent** — use a real browser UA for fetching, or add retries with different UAs
3. **Add the html2text cleaner comparison** — trafilatura failed on Wikipedia (returned 0 bytes). Test whether html2text fares better on the same page.
4. **Model selection should be task-aware** — codegen and extraction need different models. The Dispatcher should maintain separate priority lists.

### Multi-Model Extraction (Future)

Running the same extraction with multiple models and comparing/merging results could improve quality:
- Use the fastest model (dsc16) for a quick first pass
- Use the highest-quality model (qwen3:14b) for depth
- A meta-model or heuristic could merge results, taking the union of features and validating links
