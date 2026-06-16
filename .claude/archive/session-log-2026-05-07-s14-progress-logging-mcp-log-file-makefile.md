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

