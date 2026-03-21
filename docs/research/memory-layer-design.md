# Memory Layer Design — Progressive Context Injection

*2026-03-21. Design notes on a multi-tier memory system for agent context.*

---

## Problem

Agents working in a codebase need context, but context is expensive:
- Full project memory is too large to inject everywhere
- No memory means repeating discoveries every session
- Stale memory is worse than no memory — leads to wrong assumptions

## Proposed Tiers

### Tier 0: QUICK-MEMORY.md (per-folder)

- **Injected:** automatically when a folder is explored
- **Size:** ~20-40 lines, ~500 tokens
- **Language:** compressed, truncated, telegram-style
- **Content:** current status, active findings, known gaps, last-changed dates
- **Lifecycle:** overwritten frequently, no history kept
- **Example:** `spike/QUICK-MEMORY.md` — "extraction priority: qwen3:14b > qwen3:8b"

### Tier 1: Session Context (per-repo)

- **Injected:** on session start (via resume.sh)
- **Size:** ~100-200 lines, ~2K tokens
- **Content:** active decisions, current phase, what's blocked, recent commits
- **Lifecycle:** updated at session boundaries (handoff)
- **Example:** `.claude/session-context.md`

### Tier 2: Reference Memory (per-repo, indexed)

- **Injected:** on demand via `ref-lookup.sh KEY`
- **Size:** unbounded (each block is small, ~50-200 lines)
- **Content:** design decisions, architecture rationale, benchmark results
- **Lifecycle:** updated when decisions change
- **Example:** `docs/research/extraction-model-benchmark.md` with ref block `extraction-model-priority`

### Tier 3: Cross-Session Memory (per-user or per-project)

- **Injected:** always loaded (small index) + on-demand (memory files)
- **Size:** index ~200 lines; individual memories ~10-30 lines each
- **Content:** user preferences, feedback patterns, project context
- **Lifecycle:** accumulates over time, pruned when stale
- **Example:** Claude Code's `MEMORY.md` system

## Design Principles

1. **Smaller tiers load faster and more often.** QUICK-MEMORY is always injected; reference memory is pulled on demand.
2. **Each tier has a compression ratio.** Tier 0 compresses Tier 1+2 findings into telegram-style summaries.
3. **Staleness increases with tier.** QUICK-MEMORY is overwritten per-session; Tier 2 refs persist across weeks.
4. **Injection is contextual.** QUICK-MEMORY loads when a folder is explored, not globally. This gives agents "spatial memory" — they remember things about *this area* of the codebase.
5. **Tiers reference each other.** QUICK-MEMORY points to ref blocks for details: "extraction priority: qwen3:14b > qwen3:8b — § extraction-model-benchmark.md"

## Relationship to Agent Pipeline

The Dispatcher (or any agent) builds context by:
1. Reading QUICK-MEMORY for the working folder (Tier 0) — always, automatically
2. Loading session context (Tier 1) — at session start
3. Pulling specific refs when a task needs them (Tier 2) — on demand
4. Checking user memories for preferences (Tier 3) — always loaded as index

This maps to human memory: working memory (Tier 0), short-term (Tier 1), long-term declarative (Tier 2), personality/habits (Tier 3).

## Open Questions

- Should QUICK-MEMORY be auto-generated from Tier 1+2, or manually curated?
- How to detect staleness? Timestamp-based? Git-diff-based?
- Should agents be able to *write* to QUICK-MEMORY as they discover things?
- Integration with Claude Code's existing MEMORY.md system vs. a new protocol?
