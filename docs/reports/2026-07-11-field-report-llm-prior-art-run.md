# Field report: web-research MCP under a real research task (2026-07-11)

**Origin:** llm repo, prior-art survey for the coding-subagent vision (ollama-bridge
`generate_code` evolution). A two-agent comparison run: one subagent restricted to the
web-research MCP tools only (`search_topic`, `research_url`, `query_knowledge`), one control
subagent on frontier web tools (WebSearch/WebFetch), same research questions.
**For:** the web-research repo to triage — behavior observations, bug reports, proposed fixes.
**Full artifacts (in the llm repo):**
- web-research arm report + per-call operational appendix: `~/workspaces/llm/docs/research/coding-subagent-prior-art-webresearch.md`
- control-arm report: `~/workspaces/llm/docs/research/coding-subagent-prior-art.md`

---

## Headline comparison

| | web-research arm | frontier control arm |
|---|---|---|
| Tool invocations | 15 web-research calls (19 tool uses total) | 56 tool uses |
| Wall clock | ~49 min | ~8.5 min |
| Topics covered | 3 assigned; 2 covered well, 1 (small-model self-repair) mostly failed on search | 6 assigned, all covered |
| Agent tokens | ~141k | ~145k |
| External API cost | zero for the searches (local GPU) | frontier usage |

Quality on well-indexed, mainstream topics was **comparable to the control arm** — in one case
better sourced (it landed the official MCP Tasks extension spec page and the originating GitHub
design discussion directly). The gap is concentrated in tail/narrow queries and latency.

## What worked well (keep)

- **High-authority source targeting:** official docs sites, GitHub repos, arXiv HTML renders
  were found and extracted correctly on topics 1-2 with no manual intervention.
- **Base64-embedded code decoding:** the OpenHands arXiv SDK-paper page had base64-encoded code
  diffs; the extraction decoded them into readable Python — primary-source detail a summary
  page would not have carried.
- **GitHub license-badge parsing:** UI-rendered license badges were parsed into a clean
  `license` field (used for Apache-2.0 / MIT confirmations).
- **The auto-iterating loop (search → extract → audit → follow-up)** functioned as designed on
  topics where the index had coverage.
- **Large-document extraction:** a 54k-char arXiv HTML paper was extracted intact and was the
  best value-for-time call of the run.

## Defects (bug reports)

### D1 — Narrow queries fail to hard zero, with no graceful degradation
`search_topic` returned **literally zero fetched pages** (not fewer, not looser matches) on
narrow/compound queries — e.g. "third-party MCP servers implementing submit-then-poll" and
"7-14B self-repair convergence". **Three independent rewordings all failed identically** (calls
5-8 in the appendix), which points at the search backend/index, not phrasing.
**Proposed fix:** on zero hits, automatically fall back to progressively broader queries
(drop qualifiers, split compound terms) before returning; return loose matches marked
low-confidence rather than an empty set.

### D2 — Verdict/auditor self-assessment is internally inconsistent (non-discriminating signal)
Several calls that fetched 3-5 good pages still reported `"reasoning": "Only 0 results found;
below threshold"` in the verdict block — contradicting the `results` array in the same
response. A caller cannot use the verdict as a stopping signal.
**Proposed fix:** derive the verdict from the actual returned artifacts (count/size of
`results`), never from separately-tracked state. Note: this is the same defect class the llm
repo spent session 111 removing from its overlay installer — a signal that fires (or reports
the same thing) regardless of the underlying state carries zero bits, and teaches callers to
ignore the auditor entirely.

### D3 — No bot-wall / low-content-yield detection
Two calls spent 26-46s each on OpenReview pages gated behind client-side verification,
returning ~350 chars of boilerplate as if it were a normal success (calls 2 and 9).
**Proposed fix:** detect low-yield fetches (tiny `clean_chars`, verification/login-wall markers
in the text) and either retry the next candidate URL from the same search or flag the result
low-confidence. A fingerprint list for common walls (OpenReview, Cloudflare challenge) would
cover most cases cheaply.

### D4 — No arXiv URL canonicalization in `research_url`
Hand-constructed arXiv `/html/<id>` URLs 404'd twice because the version suffix (`vN`) was
unknown (calls 12-13), while `search_topic`'s own discovery step found a correct fully-versioned
HTML URL for a different paper (call 14).
**Proposed fix:** canonicalize `/abs/<id>` → resolve the current `/html/<id>vN` internally
(one HEAD request or the arXiv API); more generally, when a direct URL 404s, try the
site-specific canonical form before giving up.

### D5 — `query_knowledge` misses content already in the store (literal matching)
A query for "self-repair small model iterations convergence" returned `[]` even though the
session's knowledge store already held a page **literally containing** "SLMs (small language
models)... may fail to address complex code repair tasks" (call 15). Matching appears to be
close-to-literal substring/keyword, so the within-session cache under-recalls and forces
redundant re-searching.
**Proposed fix:** lightweight semantic or fuzzy matching (embeddings already exist in the llm
stack — qwen3-embedding:8b), or at minimum normalized token/stem matching plus exposing each
stored page's extracted keyword list so callers can query on the store's own vocabulary.

## Suggested triage order

D2 first (it corrupts the tool's own control loop and is likely a bookkeeping fix), then D1
(biggest capability gap), D3 (pure waste, cheap heuristic), D5 (compounding value for long
sessions), D4 (niche but trivial).

---

*Report authored in the llm repo session of 2026-07-11; the run's exact per-call latencies,
result quality notes, and verdict text are in the operational appendix of
`coding-subagent-prior-art-webresearch.md` (llm repo).*
