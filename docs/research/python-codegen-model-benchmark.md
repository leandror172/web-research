# Python Code Generation Model Benchmark

*2026-03-20. Tested 8 Ollama personas for Python code generation quality.*

---

## Summary

**Best models for Python code generation, in priority order:**

1. **my-python-q3c30** (qwen3-coder:30b) — highest quality, deterministic, needs RAM offloading
2. **my-python-q25c14** (qwen2.5-coder:14b) — best bang-for-buck, fits 12GB VRAM, fast
3. **my-python-dsc16** (deepseek-coder-v2:16b) — strong alternative, terse output, fits VRAM

Code-specialized models dominate. General-purpose models (qwen3.5, qwen3) consistently
over-engineer and introduce more bugs.

---

## Full Results

### Test Setup

- **Task A (simple):** Implement `HttpxFetcher` — single class, one method, clear requirements
- **Task B (complex):** Implement `TrafilaturaCleaner` + `Html2TextCleaner` + registry + factory — multi-class, library integration
- **Runs:** 3 per model per task (same prompt each time)
- **Context:** `spike/protocols.py` provided via `context_files` parameter
- **All personas** share the same system prompt (copied from `my-python-q25c14`)

### Verdict Scale

- **ACCEPTED** (1.0) — used as-is, no changes needed
- **IMPROVED** (0.5) — usable with mechanical fixes (unused imports, minor nits)
- **REJECTED** (0.0) — not usable (wrong APIs, structural bugs, hallucinated code)

### Fetcher Results (simple task)

| Model | Base | Size | Run 1 | Run 2 | Run 3 | Score |
|-------|------|------|-------|-------|-------|-------|
| my-python-q3c30 | qwen3-coder:30b | 17.3GB | ACCEPTED | ACCEPTED | ACCEPTED | **3.0/3** |
| my-python-q3-30a3b | qwen3:30b-a3b | 17.3GB | ACCEPTED | ACCEPTED | ACCEPTED | 3.0/3 |
| my-python-dsc16 | deepseek-coder-v2:16b | 8.3GB | ACCEPTED | IMPROVED | ACCEPTED | 2.5/3 |
| my-python-q25c14 | qwen2.5-coder:14b | 8.4GB | IMPROVED | IMPROVED | ACCEPTED | 2.0/3 |
| my-python-q3 | qwen3:8b | 4.9GB | IMPROVED | IMPROVED | ACCEPTED | 2.0/3 |
| my-python-dsr14 | deepseek-r1:14b | 8.4GB | IMPROVED | IMPROVED | IMPROVED | 1.5/3 |
| my-python-q3-14b | qwen3:14b | 8.6GB | IMPROVED | IMPROVED | IMPROVED | 1.5/3 |
| my-python-q35 | qwen3.5:9b | 6.1GB | IMPROVED | REJECTED | IMPROVED | 1.0/3 |

### Cleaners Results (complex task)

| Model | Base | Size | Run 1 | Run 2 | Run 3 | Score |
|-------|------|------|-------|-------|-------|-------|
| my-python-q25c14 | qwen2.5-coder:14b | 8.4GB | IMPROVED | IMPROVED | IMPROVED | **1.5/3** |
| my-python-q3c30 | qwen3-coder:30b | 17.3GB | IMPROVED | IMPROVED | IMPROVED | **1.5/3** |
| my-python-dsc16 | deepseek-coder-v2:16b | 8.3GB | IMPROVED | IMPROVED | IMPROVED | **1.5/3** |
| my-python-q3-30a3b | qwen3:30b-a3b | 17.3GB | IMPROVED | IMPROVED | REJECTED | 1.0/3 |
| my-python-q3-14b | qwen3:14b | 8.6GB | IMPROVED | IMPROVED | REJECTED | 1.0/3 |
| my-python-dsr14 | deepseek-r1:14b | 8.4GB | IMPROVED | IMPROVED | REJECTED | 1.0/3 |
| my-python-q3 | qwen3:8b | 4.9GB | IMPROVED | REJECTED | REJECTED | 0.5/3 |
| my-python-q35 | qwen3.5:9b | 6.1GB | REJECTED | REJECTED | REJECTED | 0.0/3 |

### Overall Ranking

| Rank | Model | Combined | Key Observations |
|------|-------|----------|-----------------|
| **1** | **my-python-q3c30** (qwen3-coder:30b) | 4.5/6 | Byte-for-byte identical fetcher across 3 runs. Cleaners defects are consistent and predictable (TYPE_CHECKING guard, lazy imports). No thinking dump despite being Qwen3 family. Needs RAM offloading (17.3GB on 12GB VRAM). |
| **2** | **my-python-q25c14** (qwen2.5-coder:14b) | 3.5/6 | Fits entirely in 12GB VRAM. Fast inference. Defects always mechanical (unused imports) — never wrong API calls or structural bugs. Most reliable for unattended use. |
| **3** | **my-python-dsc16** (deepseek-coder-v2:16b) | 4.0/6 | Tersest output (fewest wasted tokens). Fits VRAM (8.3GB). Ranked below q25c14 despite higher score because: run 2 fetcher used wrong API (`response.url.human_repr()` = aiohttp, not httpx), run 3 cleaners missing `import html2text`. API confusion is worse than unused imports. |
| **4** | **my-python-q3-30a3b** (qwen3:30b-a3b) | 4.0/6 | Good code quality but massive thinking overhead (~2000 tokens of chain-of-thought for ~150 tokens of code). Times out on complex prompts even at 300s. Not viable for code gen without disabling thinking. |
| **5** | **my-python-q3-14b** (qwen3:14b) | 2.5/6 | Mid-tier. Tends to invent abstractions (re-implemented html2text from scratch on run 3). Repeats same bugs across runs (`with httpx.get()` as context manager). |
| **6** | **my-python-dsr14** (deepseek-r1:14b) | 2.5/6 | Consistent relative-import bug (`.protocols` / `..protocols` instead of `spike.protocols`). Wrong API on run 3 (`.convert()` instead of `.handle()` for html2text). No thinking dump despite being a reasoning model. |
| **7** | **my-python-q3** (qwen3:8b) | 2.5/6 | Acceptable for simple tasks, breaks on complex. Repeating `self.html23text` typo bug across runs is a red flag — memorized a wrong pattern. |
| **8** | **my-python-q35** (qwen3.5:9b) | 1.0/6 | Worst performer despite being newest Qwen. Over-engineers everything, misspells `trafilatura` as `trafiladora`, puts imports under `TYPE_CHECKING` (runtime crash). Not recommended. |

### Key Findings

1. **Code-specialized training > parameter count > architecture novelty.** The top 3 are all code-tuned models. qwen3.5:9b (newest, general-purpose) scored worst.

2. **Determinism correlates with quality.** q3c30 produced byte-identical fetcher output across 3 runs. q35 produced different (and increasingly broken) output each run.

3. **No model achieved ACCEPTED on cleaners.** Every model adds things not requested: base classes, error handling, lazy imports, logging. The stubs-then-Ollama retry pattern would likely improve this.

4. **Thinking models waste tokens on code gen.** q3-30a3b produces good code but burns 10-20x the tokens on chain-of-thought reasoning, and times out on complex prompts.

5. **Common defects across all models:**
   - Unused imports (universal — every model adds `Protocol`, `Path`, `dataclass` etc.)
   - Re-declaring types instead of importing (especially smaller models)
   - `get_cleaner()` returning the class instead of an instance
   - Inheriting from Protocol (misunderstanding structural typing)

### Defect Patterns by Model (Cleaners Task)

| Defect | q3c30 | q25c14 | dsc16 | q3-30a3b | q3-14b | dsr14 | q3 | q35 |
|--------|-------|--------|-------|----------|--------|-------|-----|------|
| Unused imports | yes | yes | yes | yes | yes | yes | yes | yes |
| Re-declares types | no | no | no | no | no | no | run1 | run1-3 |
| Inherits Protocol | no | no | no | yes | no | no | no | no |
| Wrong API calls | no | no | run3 | no | run3 | run3 | no | run3 |
| Lazy imports | yes | no | no | yes | run3 | run1,3 | no | run2,3 |
| Error swallowing | no | no | no | no | run2 | no | no | run2,3 |
| Thinking dump | no | no | no | yes | no | no | no | no |
| Typo bugs | no | no | no | no | no | no | run2,3 | run2,3 |
