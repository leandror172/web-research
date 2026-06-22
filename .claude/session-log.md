# Session Log

**Current Session:** 2026-06-22 — Session 17: Phase 3.7 follow-ups — store/extractor logging + queue_width rename
**Current Layer:** Phase 3 (research loop) — logging/observability follow-ups

---
## 2026-06-22 - Session 17: Phase 3.7 follow-ups — store/extractor logging + queue_width rename

### Context

Continuation of Phase 3.7 cleanup. Picked up the two deferred items from Session 16's handoff: store/extractor logging and the queries_per_iteration rename.

### What Was Done

- Added INFO/DEBUG logging to `extractor.extract()` (DEBUG pre-call, INFO on completion with model+elapsed+field count, WARNING on malformed response, re-raised unchanged) and to `store` (INFO on save, DEBUG on init/has_url/query/recent) — closes the dark-modules observability gap from 3.7.
- Renamed `queries_per_iteration` → `queue_width` across conductor.py and test_conductor.py (contained; server.py uses default, no API ripple).
- Opened PR #11 on branch `feat/store-extractor-logging` (2 commits: feat(logging), refactor(conductor)).
- Reformatted a stray task to the (T-NN) convention.

### Decisions Made

- Extractor failure paths use **log-only** (option 1): WARNING + original exception re-raised unchanged. Left TODO markers for later option-2 hardening (wrap into a domain ExtractionError) rather than altering control flow now.

### Next

- Merge PR #11.
- Phase 3.1 — CLI batch mode (deferred).
- Phase 3.2 — JSONL event log (deferred).

### Gotchas

- Logging additions used a `try/except … raise` purely to add context — control flow is unchanged, which is why the 132-test suite stayed green.

