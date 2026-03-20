# Session Log

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
