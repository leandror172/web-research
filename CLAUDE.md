# CLAUDE.md — web-research

This file provides guidance to Claude Code when working with code in this repository.

<!-- overlay:ref-indexing v1 -->
## Reference Indexing Convention

Rules in this file may include `[ref:KEY]` tags pointing to detailed reference material
stored as `<!-- ref:KEY -->` blocks in `*.md` files.

**To look up a ref:** `.claude/tools/ref-lookup.sh KEY` — prints that section.
Run with no args to list all known keys.
**To check integrity:** `.claude/tools/check-ref-integrity.py` — finds broken `[ref:KEY]`
tags and malformed blocks across the repo.

### Two-Tier Notation

| Tier | Notation | When to Use | How to Resolve |
|------|----------|-------------|----------------|
| **Active reference** | `[ref:KEY]` | Agent needs this content during work | `ref-lookup.sh KEY` |
| **Navigation pointer** | `§ "Heading"` | Background reading, archive, rationale | Open the file, find the heading |

Use `ref:KEY` for content agents need at runtime. Use `§ "Heading"` for background or
archive navigation. Do not use `ref:KEY` for content that is only occasionally needed.

### Hard Requirements When Modifying Files

1. **New ref blocks** — wrap with `<!-- ref:KEY -->` / `<!-- /ref:KEY -->`; one concept
   per block; never wrap an entire file in one block
2. **New `[ref:KEY]` tag in CLAUDE.md** — add a corresponding block somewhere in `*.md`
3. **New scripts/tools** — add to `.claude/index.md` under the scripts/tools table
4. **New files of any kind** — add to `.claude/index.md` under the appropriate table

The full indexing convention (examples, block format, § pointer usage) is documented in
`.claude/index.md` under the "Indexing Conventions" section.
<!-- /overlay:ref-indexing -->

<!-- overlay:session-tracking v1 -->
## Resuming Multi-Session Work

**On session start:** run `.claude/tools/resume.sh` — outputs current status, next task, recent commits in ~40 lines.
For deeper context: `ref-lookup.sh current-status` | `ref-lookup.sh active-decisions`
**Knowledge index:** `.claude/index.md` maps every topic to its file location. [ref:resume-steps]

## Workflow Rules (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** — Always wait for explicit user permission
2. **Step-by-step configuration** — Build config files incrementally, explaining each setting
<!-- /overlay:session-tracking -->

<!-- overlay:ollama-scaffolding v1 -->
## Local Model Verdict & Retry Policy

**You MUST read `.claude/overlays/local-model-retry-patterns.md` before evaluating
any local model output.** It defines the verdict protocol (ACCEPTED/IMPROVED/REJECTED),
the decision tree for handling imperfect output, and the cold-start grace period.

Key rules (detail in the reference file):
- Evaluate every local model response with an explicit verdict
- Classify imperfect output by defect type, fix scope, and prompt cost — not line count
- First-call timeouts are `TIMEOUT_COLD_START`, not REJECTED — retry immediately
<!-- /overlay:ollama-scaffolding -->

## Python Code Generation Model Priority

When calling `generate_code` for Python, use these models in order (first available wins):

1. `my-python-q3c30` — highest quality overall; ACCEPTED with context files, IMPROVED without (needs RAM offloading, timeout=300)
2. `my-python-g3-12b` — gemma3 12B; ACCEPTED-level with context files, weaker without; fast, no RAM offloading needed
3. `my-python-q25c14` — VRAM-only fallback, fast, consistent
4. `my-python-dsc16` — last resort if above unavailable

**Context files rule:** Always pass relevant existing files as `context_files` — both models jump at least one tier when given examples. For framework-specific tasks (MCP, FastMCP, protocols), include a working file from the same framework as context.

Benchmark data: `docs/research/python-codegen-model-benchmark.md`

## Repository Purpose

Local-model-powered web research workbench. Fetches, extracts, and accumulates knowledge
from the web using Ollama (7-14B models) for processing. Designed to work with RTX 3060
12GB, integrate with Claude Code via MCP, and progressively become more autonomous.

Architecture: Conductor (orchestration) → Dispatcher (tool execution) → Auditor (sufficiency
review) → Knowledge (persistence). Agents map to DDD bounded contexts. [ref:vision]

Research docs and design decisions: `/mnt/i/workspaces/llm/docs/research/`

## Environment Context

- **Claude Code runs in:** WSL2 (Ubuntu-22.04)
- **Ollama:** `http://localhost:11434` — use `/api/chat` with `stream: false`
- **ollama-bridge MCP:** available globally (`~/.claude/.mcp.json`)
- **sudo commands:** Cannot run through Claude Code. Ask the user.

## Troubleshooting Approach

1. **Ask what's been tried** before suggesting solutions
2. **Check prior context** — read session logs and handoff files first
3. **Propose before executing** — explain intent for diagnostic commands with side effects
