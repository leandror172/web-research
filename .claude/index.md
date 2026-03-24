# Knowledge Index

**Purpose:** Map of where all project information lives. Read this to find anything.

<!-- ref:indexing-convention -->
### Indexing Conventions (Two-Tier System)

| Tier | Notation | When to Use | Lookup Method |
|------|----------|-------------|---------------|
| **Active reference** | `<!-- ref:KEY -->` + `[ref:KEY]` | Agent needs this during work; CLAUDE.md rules point here | `.claude/tools/ref-lookup.sh KEY` (machine-lookupable) |
| **Navigation pointer** | `§ "Heading"` | Index/docs pointing to sections for background reading | Open file, find heading (human/agent reads) |

**Active refs** are for high-frequency, runtime lookups.
**§ pointers** are for low-frequency, "read when needed" navigation.

**Single-responsibility rule:** One ref block per concept — don't wrap an entire file in one block.
Keep blocks narrow enough that `ref-lookup.sh KEY` returns only what's needed for the task.
<!-- /ref:indexing-convention -->

---

## Quick Pointers

| What | Where |
|------|-------|
| Project rules & constraints | `CLAUDE.md` (repo root) |

---

## Files

| File | Purpose |
|------|---------|
| `docs/research/python-codegen-model-benchmark.md` | Benchmark of 8 Ollama personas for Python code gen — model priority list |
| `spike/protocols.py` | Protocol definitions and dataclasses for extraction pipeline |
| `spike/fetcher.py` | HttpxFetcher implementation (Fetcher protocol) |
| `spike/cleaners.py` | TrafilaturaCleaner + Html2TextCleaner implementations (Cleaner protocol) |
| `pyproject.toml` | Project config — uv, dependencies (httpx, trafilatura, html2text) |
| `spike/prompts.py` | Extraction prompts (open + focused) and JSON schemas |
| `spike/extractor.py` | OllamaExtractor implementation (Extractor protocol) |
| `spike/output.py` | JsonOutputWriter implementation (OutputWriter protocol) |
| `spike/extract.py` | Main spike script — CLI for fetch→clean→chunk→extract→merge→save |
| `spike/benchmark.sh` | Single-URL extraction benchmark (7 models × 2 tasks) |
| `spike/benchmark-full.sh` | Full extraction benchmark (6 models × 4 URLs × 2 tasks) |
| `spike/QUICK-MEMORY.md` | Per-folder quick memory — recent spike findings |
| `docs/research/extraction-model-benchmark.md` | Benchmark of 7 models for web extraction — model priority list |
| `docs/research/memory-layer-design.md` | Multi-tier memory system design (QUICK-MEMORY → session → ref → user) |
| `docs/research/truncation-design-notes.md` | Truncation problem analysis, strategy comparison, decision log |
| `spike/models.json` | Model context-window overrides/fallback data file |
| `spike/models.py` | Model context-window lookup — Ollama API + JSON override + fallback |
| `spike/chunker.py` | Text chunking at paragraph/sentence boundaries with configurable overlap |
| `spike/merger.py` | Merge N ExtractionResults — dedup lists, merge dicts, by prompt type |

---

## Scripts & Tools

| Script | Purpose |
|--------|---------|
| `.claude/tools/ref-lookup.sh KEY` | Print a `[ref:KEY]` block by key |
| `.claude/tools/check-ref-integrity.sh` | Find broken ref tags and malformed blocks |
