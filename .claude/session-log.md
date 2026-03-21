# Session Log

---

## 2026-03-21 — Session 3: Extraction Spike + Extraction Model Benchmark

### Context

Resumed from Session 2 (codegen benchmark). Implemented remaining spike files, ran full extraction benchmark (7 models × 5 URLs × 2 tasks), discovered pipeline issues, fixed them.

### What Was Done

- Implemented full spike pipeline: `prompts.py`, `extractor.py`, `output.py`, `extract.py` (main CLI)
- Used `my-python-q3c30` to generate implementations via Ollama, verdicted each (all IMPROVED — consistent defect patterns: inherits from Protocol, unused imports, async instead of sync)
- Ran extraction benchmark: 7 models × 5 URLs (crawl4ai, huggingface, Wikipedia, htmx, MCP llms-full.txt) × 2 tasks (open + focused)
- Discovered 3 pipeline issues: Wikipedia 403 (TLS fingerprinting), no content truncation (1MB sent to 8K-context models), cold-start timeouts on model switching
- Fixed: content truncation (6K char cap), browser User-Agent
- Re-tested: MCP now correctly extracts "Model Context Protocol" (was extracting random SEP fragments); swapped Wikipedia for Arch Wiki
- Created `docs/research/extraction-model-benchmark.md` with full results and priority list
- Created `spike/QUICK-MEMORY.md` — per-folder quick memory (Tier 0 of memory layer design)
- Created `docs/research/memory-layer-design.md` — multi-tier memory architecture design
- Saved user memories: memory layer architecture interest, Ollama for code generation feedback

### Decisions Made

- **Extraction model priority:** qwen3:14b > qwen3:8b > qwen2.5-coder:14b > dsc16 (different from codegen!)
- **deepseek-r1:14b excluded** from extraction — hallucinated "PyTorch" from empty input
- **qwen3:30b-a3b not worth it** for extraction — 2-3x slower, no quality gain over 14b
- **Task-aware model selection validated** — different tasks need different models; Dispatcher should maintain separate priority lists
- **Multi-model extraction** worth exploring — fastest model for quick pass, best for depth, merge results
- **Wikipedia needs a real browser fetcher** (Crawl4AI/Firecrawl) — not fixable with UA alone
- **QUICK-MEMORY.md per folder** adopted as Tier 0 of progressive memory injection

### Next

- [ ] 1.7 — Write `spike/README.md` with findings and verdict
- [ ] Split benchmark tables into separate files (deferred — saves ~3K tokens)
- [ ] html2text comparison on pages where trafilatura fails
- [ ] Chunking strategy for pages >6K (currently just truncates)
- [ ] Consider: model-selects-model for the Dispatcher (classifier picks best extractor per content type)

---

## 2026-03-20 — Session 2: Python Codegen Model Benchmark

### Context

Resumed from Session 1 (repo setup). Goal was to start spike implementation, but first
aligned on architecture decisions (pluggability, model selection, dependency management),
then benchmarked Ollama personas for Python code generation.

### What Was Done

- Discussed and decided spike architecture: Protocol-based boundaries (Fetcher, Cleaner, Extractor, OutputWriter), toolkit pattern for agent composability
- Wrote `spike/protocols.py` (dataclasses + Protocols), `spike/fetcher.py`, `spike/cleaners.py`
- Set up `pyproject.toml` with uv (httpx, trafilatura, html2text)
- Benchmarked 8 Ollama personas (3 runs each, 2 tasks) for Python code generation quality
- Created 4 new Python personas: my-python-q3c30, my-python-q3-30a3b, my-python-dsc16, my-python-dsr14
- Established model priority order: q3c30 > q25c14 > dsc16
- Saved full benchmark results to `docs/research/python-codegen-model-benchmark.md`
- Updated CLAUDE.md with Python code gen model priority section

### Decisions Made

- **Python confirmed** for MVP (was open from Session 1)
- **uv** as dependency manager (pyproject.toml, not poetry)
- **Protocol-based pluggability** — each pipeline step is independently callable with swappable implementations via string parameters (Level 1), composable by Dispatcher agent later (Level 2)
- **Model priority for Python codegen:** q3c30 (best quality) > q25c14 (best VRAM-only) > dsc16 (alternative)
- **Code-specialized models dominate** — general-purpose Qwen3.5 was worst performer despite being newest
- **Ollama should be used for code generation** too, not just as product component (feedback saved to memory)

### Next

- [ ] 1.1 — Implement remaining spike files: OllamaExtractor, JsonOutputWriter, prompts, main script (use q3c30 to generate, verdict each)
- [ ] Test spike against URLs in spike/urls.txt
- [ ] Consider disabling thinking on qwen3:30b-a3b persona for code gen use

---

## 2026-03-18 — Session 1: Repo Setup

### Context

New repo created for the web research tool, designed in sessions 44/44b of the LLM
infrastructure project. Full design docs in `/mnt/i/workspaces/llm/docs/research/`.

### What Was Done

- Initialized git repo at `/mnt/i/workspaces/web-research/`
- Installed all three overlays: ref-indexing, ollama-scaffolding, session-tracking
- Wrote project-specific CLAUDE.md, session-context.md, tasks.md
- Copied research docs to docs/research/ (vision, spike plan, DDD patterns, agent naming)
- Created spike/ directory skeleton per mvp-spike-plan.md
- session-handoff skill installed at user level (~/.claude/skills/)

### Decisions Made

- session-tracking overlay created in LLM repo (PR #19) — first real use is this repo
- Language: Python for spike, overall language TBD after spike validates extraction quality
- Repo name `web-research` is a placeholder — rename when better name emerges
- Research docs copied here (not symlinked) — new repo evolves them freely; LLM repo keeps originals as historical reference

### Next

- [ ] 1.1 — Implement `spike/extract.py`: fetch → clean → extract via Ollama → save JSON

---
