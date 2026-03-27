# web-research Tool — Capability Map

*Living document. Updated as content types are tested. Each row is evidence, not speculation.*

---

## Fetch + Clean

| Content Type | Example | Status | trafilatura | html2text | Notes |
|---|---|---|---|---|---|
| Static HTML (docs) | docs.crawl4ai.com | ✅ | 4663 chars, good | — | Clean extraction, good quality |
| Static HTML (wiki) | wiki.archlinux.org | ✅ | 42838 chars, good | — | Rich content, 1 chunk |
| Discourse forum | discuss.python.org | ✅ | ~2000 chars | — | Trafilatura strips noise well |
| JS-rendered (SPA) | vercel.com | ⚠️ | 661 chars (thin) | 8455 chars | Trafilatura gets only above-fold text; html2text richer but noisy |
| YouTube | youtube.com | ⚠️ | 206 chars | — | Near-empty; JS-rendered, no transcript |
| Medium (paywall) | medium.com | ❌ | 41 chars | — | Paywall blocks content |
| Reddit | reddit.com | ❌ | 0 chars | — | JS-rendered, trafilatura gets nothing |
| Plain text / llms.txt | modelcontextprotocol.io/llms-full.txt | ✅ | 1.16M chars | — | 10 chunks × 120K; chunking + merge path exercises correctly |
| 404 page | httpbin.org/status/404 | ⚠️ | varies | — | Fetcher returns HTML without raising; pipeline processes 404 body |

## Extraction Quality

| Content Type | Model | Prompt Type | Quality | Notes |
|---|---|---|---|---|
| Docs (crawl4ai) | qwen3:14b | open | ✅ High | 8 features, accurate summary, good technical_details |
| Forum post | qwen3:14b | focused | ✅ Medium | Relevant facts extracted; assessment field useful for relevance scoring |
| Near-empty (<100 chars) | qwen3:14b | open | ❌ | Returns empty arrays, no key features — model handles gracefully but wasteful |
| Large doc (1.16M) | qwen3:14b | open | ✅ | Chunking + merge works; only qwen3:14b identifies top-level topic across chunks |

## Search Result Quality (Firecrawl)

| Query Type | Observation |
|---|---|
| Specific library ("crawl4ai python") | Top 2 results directly relevant |
| Setup/how-to ("SearXNG self-hosted setup") | Positions 1-3: YouTube, paywalled Medium, Reddit (all poor); positions 4-5: actual docs (skipped) |
| Best practices ("python asyncio best practices") | Top result: forum thread (low content density but on-topic) |

## Known Gaps

| Gap | Severity | Affects | Mitigation |
|---|---|---|---|
| No content guard before extraction | Medium | Any URL with <100 chars after cleaning | Skip + try next result; add `min_chars` threshold |
| JS-rendered pages | High | YouTube, Reddit, React SPAs, many modern sites | FirecrawlFetcher (not yet built) |
| Paywalled content | High | Medium, NYT, most news sites | No good mitigation; filter by domain blacklist or char count |
| Search result ordering | Medium | How-to queries surface YouTube/Reddit before docs | `--top N` should mean N *usable* results, not N attempts |
| 404 not detected | Low | Broken links in search results | Check `status_code` before cleaning |
| Multi-chunk merge loses context | Low | Very large docs (>1 chunk) | Merge takes name/summary from first chunk only |

## Tested Configurations

| Date | Test | Config | Result |
|---|---|---|---|
| 2026-03-27 | Single URL extract | qwen3:14b, trafilatura, open | ✅ docs.crawl4ai.com — 8 features, 42s |
| 2026-03-27 | Focused extract | qwen3:14b, trafilatura, focused | ✅ discuss.python.org — medium relevance, 38s |
| 2026-03-27 | Multi-result --top 3 | qwen3:14b, Firecrawl search | ⚠️ 3/3 poor results (YouTube, Medium, Reddit) — search ranking issue |
| 2026-03-27 | Long page chunking | qwen3:14b, MCP llms-full.txt | ✅ 1.16M → 10 chunks, merge pipeline exercised |
| 2026-03-27 | JS-heavy comparison | vercel.com, both cleaners | ⚠️ trafilatura thin; html2text richer but noisy |
