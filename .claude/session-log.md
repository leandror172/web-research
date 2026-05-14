# Session Log

**Current Session:** 2026-05-07 | **Phase:** Phase 3 complete — progress logging + MCP log file + Makefile

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

## 2026-04-28 — Session 12: Phase 3.6 — MCP wiring + A/B benchmark
**Previous logs:** `.claude/archive/session-log-2026-03-18-to-2026-03-18.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-21-to-2026-03-21.md`, `.claude/archive/session-log-2026-03-24-to-2026-03-24.md`, `.claude/archive/session-log-2026-03-27-to-2026-03-27.md`, `.claude/archive/session-log-2026-04-06-to-2026-04-06.md`, `.claude/archive/session-log-2026-04-07-to-2026-04-07.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-23-to-2026-04-28.md`

---

## 2026-04-28 — Session 12: Phase 3.6 — MCP wiring + A/B benchmark

### Context

Resumed on `phase-3.6-conductor` branch. Conductor was built (174 lines) but MCP `search_topic` still returned raw entries. Goal was to complete Phase 3.6 by wiring the Conductor into MCP, testing end-to-end, and opening the PR.

### What Was Done

- **Wired Conductor into MCP `search_topic`** (`mcp/server.py`): replaced single-round search with full `research_topic()` loop; new return shape `{query, results, iterations_run, verdict, audit_failed}`; two-pass results collection (LIKE on original query + per-URL for follow-up iterations)
- **Fixed cached-results bug** (caught during live test): `_result_to_dict` was returning `results=[]` when all URLs were already cached (cached URLs don't appear in `new_urls`); fixed with two-pass store query
- **Live end-to-end test**: `search "sqlite full text search python" --max-iterations 2` — heuristic passed to model, model returned `sufficient=False` with structured `missing_topics` + `recommended_queries`, loop stopped correctly on `new_urls=[]`
- **Opened PR #7**: `phase-3.6-conductor` → master — 5 commits: Conductor core, CLI wiring, MCP wiring, cached-results fix, benchmark
- **A/B benchmark** (`benchmarks/auditor_ab.py`, 194 lines): pins signals+entries per query, calls `ModelChecker.check()` directly per renderer with `temperature=0` + `seed=42`; run with `--queries` or `--top N`
- **130 tests passing** throughout

### Decisions Made

- **Two-pass results collection in MCP** — LIKE on original query catches cached iteration-1 hits; per-URL lookup covers follow-up iteration results that wouldn't substring-match the original query
- **Benchmark calls `ModelChecker.check()` directly** (not `Auditor.check()`) — bypasses store re-query so both renderers see identical pinned input; the only variable is the renderer
- **`temperature=0` + `seed=42`** in Ollama payload for benchmark determinism

### Findings (A/B benchmark, 2 queries)

- Both renderers agree on `sufficient` verdict in both cases
- Confidence diverges on sparse single-source data: YAML→`low`, Prose→`medium`
- Hypothesis: YAML makes sparseness more legible as a discrete field vs embedded in prose

### Next

- [ ] **Merge PR #7** (all tests passing, live-verified)
- [ ] **Re-run A/B benchmark with richer data** — run 3-4 more searches to get 4-5 entries per query, then `uv run python benchmarks/auditor_ab.py --top 5`
- [ ] **Optional deferred:** Phase 3.1 (CLI batch mode), Phase 3.2 (JSONL event log), heuristic threshold tuning

---

