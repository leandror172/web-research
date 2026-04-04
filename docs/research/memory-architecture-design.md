# Per-Folder Agent Memory Architecture

*Design discussion from 2026-03-26. Applies to both web-research and LLM repos.*

## Premise

Agents operating in a folder need context about that folder. Different types of context
have different lifetimes, sizes, and injection strategies — modeled on the four types
of human memory from cognitive psychology (plus a fifth).

## Memory Types

| Type | Cognitive analog | Folder implementation | Injection |
|------|-----------------|----------------------|-----------|
| **Working** | Working memory | `.memories/QUICK.md` | Always — injected into every agent touching this folder |
| **Semantic** | Semantic memory | `.memories/KNOWLEDGE.md` | On demand — read when deeper context needed |
| **Structural** | Spatial/cognitive map | TBD — index of how things connect | On demand — for navigation and orientation |
| **Episodic** | Episodic memory | Repo-level session logs; consolidates into semantic via "dream" passes | Not injected at folder level |
| **Procedural** | Procedural memory | Repo-level CLAUDE.md / overlays / scripts | Inherited from repo, not per-folder |
| **Prospective** | Prospective memory | QUICK.md "next" section / TODO items | Injected via QUICK |

### Why only two files per folder?

At folder level, episodic and procedural don't have independent existence:
- **Episodic** at folder level is just `git log -- <folder>`. Useful parts get consolidated
  into semantic memory ("we tried X, it failed because Y" → "X doesn't work because Y").
- **Procedural** is almost always repo-wide (CLAUDE.md, overlays). A folder rarely has its
  own unique operating rules that differ from the repo.
- **Structural** is a candidate for a third file, but needs more thought — for docs it's
  ref-indexing; for code it's something else (module map? dependency graph?).

So the minimum viable per-folder memory is: **QUICK.md** (working + prospective) and
**KNOWLEDGE.md** (semantic + consolidated episodic).

## Repo Level vs Knowledge Base Level

These types manifest differently depending on the domain:

| Type | Repo (dev context) | Knowledge base (research output) |
|------|-------------------|----------------------------------|
| Working | Current dev state, active branch | Current research question, open threads |
| Semantic | Dev findings (byproduct) | **The actual accumulated knowledge (the product)** |
| Episodic | Session logs, handoffs | Provenance: source, date, confidence |
| Procedural | CLAUDE.md, overlays, scripts | Ingestion rules, schema, query patterns |
| Structural | File index, module map, ref system | Ontology, topic graph, fact relationships |

Key inversion: in a repo, semantic memory is a byproduct of work. In a knowledge base,
semantic memory IS the primary content. This changes everything about how it's stored,
queried, and consolidated.

### Repo-specific artifacts that don't transfer

- Handoffs → no equivalent in knowledge base (no "sessions")
- Session logs → becomes provenance/audit trail
- CLAUDE.md → becomes knowledge base schema definition

The knowledge base needs its own domain language for these concepts, not a copy of
repo conventions.

## Dream Mode / Consolidation

Analogous to memory consolidation during sleep. An agent periodically reviews episodic
memories (session logs, extraction results) and:
1. Extracts stable facts → promotes to KNOWLEDGE.md (semantic)
2. Updates current state → refreshes QUICK.md (working)
3. Discards noise → archives or deletes session artifacts

The web-research Auditor agent's "sufficiency review" is a form of this — reviewing
what was gathered and deciding what's confirmed knowledge vs what needs more research.

Anthropic's "dream" mode for Claude memory refinement is the same pattern applied to
user-level memories.

## First Instance

`spike/.memories/` in web-research (2026-03-26):
- `QUICK.md` — 25 lines, current state + pointers
- `KNOWLEDGE.md` — model rankings, architecture decisions, failure modes

## Open Questions

- **Structural memory for code:** ref-indexing works for docs but not code. What's the
  code equivalent? Module boundary map? Protocol/interface catalog? Auto-generated?
- **Cross-folder semantic memory:** When findings from `spike/` are relevant to `src/search/`,
  where does that live? Repo-level KNOWLEDGE.md? Or cross-references?
- **Consolidation trigger:** When does "dream" run? On session end? On explicit command?
  On a schedule? Manual for now, but the web-research Conductor could automate it.
- **Knowledge base domain language:** What vocabulary replaces handoff/session/CLAUDE.md
  in the knowledge base context? Needs to emerge from Phase 2+ implementation.
