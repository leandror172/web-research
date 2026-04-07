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
| Project overview & usage | `README.md` (repo root) |

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview — architecture, usage, status |
| `docs/research/python-codegen-model-benchmark.md` | Benchmark of 8 Ollama personas for Python code gen — model priority list |
| `docs/research/extraction-model-benchmark.md` | Benchmark of 7 models for web extraction — model priority list |
| `docs/research/memory-layer-design.md` | Multi-tier memory system design (QUICK-MEMORY → session → ref → user) |
| `docs/research/memory-architecture-design.md` | Per-folder agent memory architecture — types, levels, knowledge base vs repo |
| `docs/research/truncation-design-notes.md` | Truncation problem analysis, strategy comparison, decision log |
| `.memories/QUICK.md` | Repo-root working memory — current phase, structure, key rules |
| `.memories/KNOWLEDGE.md` | Repo-root semantic memory — structural decisions, phase plan |
| `engine/.memories/QUICK.md` | Engine working memory — placeholder, DDD architecture overview |
| `engine/.memories/KNOWLEDGE.md` | Engine semantic memory — tool integration patterns, libs/ trigger |
| `tools/web-research/.memories/QUICK.md` | Tool working memory — current status, pipeline overview |
| `tools/web-research/.memories/KNOWLEDGE.md` | Tool semantic memory — architecture, codegen patterns, decisions |
| `tools/web-research/docs/capabilities.md` | Capability map — content types × fetch/clean/extract quality, tested configs |
| `tools/web-research/web_research/extraction/protocols.py` | Protocol definitions and dataclasses for extraction pipeline |
| `tools/web-research/web_research/extraction/models.py` | Model context-window lookup — Ollama API + JSON override + fallback |
| `tools/web-research/web_research/knowledge/store.py` | SQLite knowledge store — save/query/has_url across sessions |
| `tools/web-research/pyproject.toml` | Tool package config — uv, dependencies, CLI entry point |

---

## Scripts & Tools

| Script | Purpose |
|--------|---------|
| `.claude/tools/ref-lookup.sh KEY` | Print a `[ref:KEY]` block by key |
| `.claude/tools/check-ref-integrity.sh` | Find broken ref tags and malformed blocks |
