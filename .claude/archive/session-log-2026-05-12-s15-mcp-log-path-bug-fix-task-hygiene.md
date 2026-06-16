## 2026-05-12 — Session 15: MCP log path bug fix + task hygiene

### Context

Resumed on `feat/progress-logging` (PR #8 open). User verified Session 14 smoke tests — 1–3 passed, 4–5 failed (logs in wrong directory).

### What Was Done

- **Restored dropped task pointer** — `auditor-iteration-control-ideas` note was silently removed from QUICK.md during Session 14's Phase 3 rewrite; restored as task 3.7 in `tasks.md` and added `## Parked / Revisit` section back to QUICK.md with updated wording (ship condition now met)
- **Synced task status** — marked 3.4/3.5/3.6 complete; corrected test count to 130; added progress logging to "Also completed" list
- **Fixed MCP log path off-by-one** — `pathlib.Path(__file__).parents[3]` resolved to `tools/` instead of `tools/web-research/`, so logs landed in `tools/output/` instead of `tools/web-research/output/`; fix: `parents[2]`
- **Updated PR #8 description** — added bug fix + completed smoke test checklist

### Decisions Made

- Dropped note graduates to task, not just restored — 3.6 had shipped so the "revisit after ship" condition was already met

### Next

- [ ] Merge PR #8
- [ ] Phase 3.7 — Auditor loop tuning (review real-run logs; confidence threshold vs iteration-aware prompt) [ref:auditor-iteration-control-ideas]
- [ ] Phase 3.1 — CLI batch mode (deferred)
- [ ] Phase 3.2 — JSONL event log (deferred)
- [ ] Add `logger.debug()`/`logger.info()` in auditor/store/extractor so `--log-level DEBUG` actually surfaces useful detail

---

