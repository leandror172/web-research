# Session Log

**Previous logs:** `.claude/archive/session-log-2026-04-28-to-2026-04-28.md`
**Current Session:** 2026-05-20 — Session 16: Phase 3.7 — queue-based Conductor + audit logging
**Current Layer:** Phase 3.7 complete — queue-based Conductor

---

## 2026-05-20 — Session 16: Phase 3.7 — queue-based Conductor + audit logging

### Context

Resumed on master (all PRs merged). Discussed Phase 3.7 (Auditor loop tuning). Ran real `search_topic` calls to observe loop behavior; found logs were empty (WR_LOG_LEVEL=WARNING, no warnings in normal runs). Added INFO-level logging to diagnose the actual failure mode.

### What Was Done

- **Added INFO logging to Auditor and Conductor** — `auditor.py`: heuristic gate fire + model verdict + recommended_queries; `conductor.py`: stop reason per condition + next-query queued; `WR_LOG_LEVEL` bumped to `INFO` in `.mcp.json`
- **Diagnosed real failure mode** — real-run logs revealed the problem wasn't a bad `sufficient=True` verdict but Q1 follow-up returning 0 results and the loop dying before trying Q2 (which was already in the verdict's `recommended_queries`)
- **Implemented queue-based Conductor (Phase 3.7)** — replaced scalar `current_query` + `_should_stop()` + `_next_query()` with a `deque`-based pending queue; each verdict's `recommended_queries` (up to `queries_per_iteration`) are enqueued; `seen` set prevents duplicate queries; `queries_per_iteration` default bumped 1→2
- **Updated tests** — updated `test_stops_when_iteration_produces_no_new_urls` (old `not new_urls` hard-stop removed); added `test_falls_back_to_second_recommended_when_first_yields_nothing` and `test_max_iterations_caps_growing_queue`; 132 tests passing
- **Updated `search_topic` docstring** — reflects new "top 2 recommended queries enqueued" behavior
- **End-to-end verified** — reran "SQLite FTS5 ranking algorithms"; log confirmed `queued[0]` for both Q1+Q2, Q1 failed (0 results), Q2 tried and succeeded, loop ran all 3 iterations instead of dying at iteration 1
- **Branch:** `feat/queue-based-conductor` — 1 commit; PR pending

### Decisions Made

- **Queue model over confidence threshold (Idea 1) or iteration-aware prompt (Idea 2)** — log analysis showed the failure was a resilience gap (Q2 never tried), not a calibration problem; the queue fix is simpler and more targeted
- **`queries_per_iteration` default 1→2** — keeps the parameter as a width cap rather than removing it; fixes the observed failure by default without breaking callers
- **`not new_urls` stop condition removed** — 0-result iterations now drain naturally (heuristic verdict has no recommended_queries → nothing enqueued → queue empties)

### Next

- [ ] Open PR for `feat/queue-based-conductor`
- [ ] Add `logger.debug()`/`logger.info()` to store.py and extractor so `--log-level DEBUG` surfaces useful detail there too (auditor/conductor now covered)
- [ ] Consider renaming `queries_per_iteration` → `queue_width` for clarity (deferred)
- [ ] Phase 3.1 — CLI batch mode (deferred)
- [ ] Phase 3.2 — JSONL event log (deferred)

---

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

## 2026-05-07 — Session 14: Progress logging, MCP log file, Makefile

### Context

Resumed on master (PR #7 merged, branch cleaned up). Phase 3 fully complete. User asked about progress visibility during a running research — found the auditor call was the main silent gap.

### What Was Done

- **Conductor callbacks** — added `on_iteration_start(iteration, max, query)` and `on_pre_audit(query)` optional callables to `iterate()`; CLI wires print lambdas, MCP passes `None`; conductor stays output-agnostic (MCP stdio constraint — any print corrupts JSON-RPC framing)
- **CLI progress** — iteration header box printed before search, "Auditing knowledge coverage..." before the slow Ollama call; `_print_iteration_banner` → `_print_iteration_summary` (closing summary only, no duplicate header)
- **CLI `--log-level`** — moved from root parser to each subparser so it works after the subcommand, not just before
- **MCP log file** — `logging.FileHandler` writing to `output/mcp-server-{pid}.log`; per-PID (not rotating) because `RotatingFileHandler` is not multi-process safe; `WR_LOG_LEVEL` + `WR_LOG_FILE` env vars; default level set in `.mcp.json`
- **`run-server.sh`** — prints log file path to stderr on startup
- **`Makefile`** — `make logs` (`tail -F output/mcp-server-*.log`, glob covers all sessions), `make test`, `make help`; `-F` not `-f` (follows by name, survives rotation)
- **Documentation** — README updated (architecture, phase table, usage, MCP section, dev commands); `.memories/QUICK.md` rewritten for current state; `.memories/KNOWLEDGE.md` Phase 3 decisions appended; `session-context.md` current-status updated
- **Branch:** `feat/progress-logging` — 2 commits (feat + docs); 130 tests passing throughout

### Decisions Made

- **Per-PID log file over rotating** — `RotatingFileHandler` corrupts under concurrent writes from multiple Claude Code sessions; per-PID is fully isolated with no locking needed
- **Callbacks over prints in conductor** — MCP server uses stdio transport; `print()` in library code would corrupt the protocol; callbacks keep conductor output-agnostic
- **`--log-level` per subparser** — argparse root-level flags must precede the subcommand; per-subparser placement works in any position
- **`tail -F` in Makefile** — `-f` follows by inode (loses track after log rotation); `-F` follows by name and reopens

### Advisor review highlights

Called advisor mid-session; caught: (1) `RotatingFileHandler` not multi-process safe → switched to per-PID, (2) `tail -f` vs `-F` rotation issue, (3) `--log-level` argparse placement, (4) DEBUG pitch overpromised what was actually instrumented.

### Next

- [ ] Phase 3.1 — CLI batch mode (deferred)
- [ ] Phase 3.2 — JSONL event log (deferred)
- [ ] Heuristic threshold tuning after more live testing
- [ ] Add `logger.debug()`/`logger.info()` calls in auditor, store, extractor so `--log-level DEBUG` actually reveals useful detail

---

## 2026-04-29 — Session 13: A/B benchmark confirmation + renderer decision

### Context

Resumed on `phase-3.6-conductor`. PR #7 open (user handling merge). Previous session's A/B benchmark ran on only 2 queries and was inconclusive. Advisor (Opus) from the prior session flagged: verify `seed=42` determinism before trusting results.

### What Was Done

**Seed determinism check (Opus advisor concern)**
- `seed=42` + `temperature=0` stabilises binary verdict and confidence tier — both match across two runs
- Free-text fields (reasoning, missing_topics, rec_queries) vary — non-deterministic
- Implication: verdict/confidence comparisons in the A/B are reliable; text field comparisons are not

**A/B benchmark re-run (4 queries, richer data)**
- Populated store with 4 new searches (`qwen3:8b` for speed); landed 3 entries each for `httpx python async http client` and `python dataclasses guide`
- Ran `uv run python benchmarks/auditor_ab.py --top 5` — 4 queries evaluated (1 skipped by heuristic gate)

### Findings

| Query | Entries | YAML | Prose | Verdict agree? |
|---|---|---|---|---|
| httpx python async http client | 3 | False/medium | True/high | ✗ |
| python dataclasses guide | 3 | False/medium | False/medium | ✓ |
| sqlite full text search python | 2 | False/medium | False/medium | ✓ |
| proxify.ai (1 source) | 2 | False/low | False/medium | ✓ |

- Verdict agreement: 3/4 — Confidence agreement: 2/4
- **Pattern:** Prose is systematically more optimistic. Narrative coherence masks coverage gaps — the `httpx` case is canonical: 3 entries covering httpx breadth-first reads as "comprehensive" in prose but YAML exposes each feature is lightly covered.
- **YAML's conservatism is the right property** — for a research tool, over-stopping is the failure mode; the Conductor should run more iterations, not fewer.

### Decision

**YAML renderer is the production default.** Already wired into `build_default_auditor()` in `conductor.py`. Prose stays available via `ProseRenderer()` for throughput-optimised use cases (e.g. shallow scans where a quick answer beats depth).

### Next

- [ ] Phase 3.1 — CLI batch mode (deferred)
- [ ] Phase 3.2 — JSONL event log (deferred)
- [ ] Tune heuristic thresholds after more live testing

---

