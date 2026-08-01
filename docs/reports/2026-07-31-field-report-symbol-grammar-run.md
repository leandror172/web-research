# Field report — `search_topic` on an ambiguous acronym (2026-07-31)

*Second cross-repo field report from the `llm` estate, following
`2026-07-11-field-report-llm-prior-art-run.md`. Same method: `web-research` was run as one arm of
a multi-arm survey alongside a frontier-tools arm answering identical questions, so the
**divergence between arms is the measurement**. One new defect class, one confirmed improvement,
one usage lesson.*

## The run

Called from the `llm` repo during a prior-art survey on symbol-address grammars for code editing:

```
search_topic(
  query="canonical cross-language symbol identifier grammar for code entities:
         SCIP symbol descriptors, LSP DocumentSymbol SymbolKind, ctags kinds —
         how are classes, methods, and overloaded functions uniquely addressed",
  top=3, max_iterations=2)
```

Ran 2 iterations, 6 URLs extracted, ~108 s before backgrounding and several minutes after.
Final verdict: `sufficient: false, confidence: low`.

## Defect 1 (NEW) — ambiguous acronym resolved to the wrong domain, with nothing to notice

**"SCIP" here means the Sourcegraph Code Intelligence Protocol.** The run retrieved
`https://www.gams.com/latest/docs/S_SCIP.html` — **SCIP the mixed-integer-programming solver**
(*Solving Constraint Integer Programs*) — and spent **146 s** extracting 452,781 chars of solver
branching parameters, returning entries like `branchweight`, `solvingphases`, `reoptsols`.

The follow-up query the Auditor recommended, `"SCIP symbol descriptor grammar specification"`,
then retrieved `https://tc39.es/ecma262/` — the full ECMAScript specification, 777,437 chars,
**205 s** — yielding a summary of ECMAScript internal methods and object invariants.

So of 6 extractions, **2 were in an unrelated domain and consumed the majority of wall-clock
time**. The extracted `data` for both is internally coherent and correct *about the document
retrieved*; nothing in the record indicates the document was off-topic.

**Why this is not the same as "the search returned bad results".** The query named three sibling
systems — SCIP, LSP `DocumentSymbol`, ctags — which jointly disambiguate the domain completely.
A retrieval whose corpus contains a MIP solver and the ECMAScript spec has, in effect, ignored
the query's own context. The pipeline has no step that asks whether a retrieved document belongs
to the same domain as the query, so **domain drift is invisible by construction**.

**Suggested fix, cheapest first:**
1. **A domain-coherence check before extraction.** The most expensive step (extraction, up to
   205 s here) runs on documents that a cheap title+URL check would have rejected. Extraction
   cost is roughly linear in `clean_chars`; the two off-domain documents were the two largest
   (452K and 777K chars). **A `clean_chars` ceiling alone would have caught both** and is close
   to free.
2. **Carry the sibling terms into result scoring.** A result matching zero of the query's other
   named entities is a candidate for rejection, not just a lower rank.
3. At minimum, **report the drift**: surface per-result "matched none of the query's key terms"
   in the verdict so the caller can see it without reading the URLs.

## Defect 2 (usage, not a bug) — `search_topic` uses OPEN extraction

Every entry carries `prompt_type: "open"`. For `ctags`, a query explicitly about **kinds
vocabulary** returned:

```
key_features: ["Supports multiple programming languages", "Creates indexes for code navigation",
               "Compatible with editors like Vim and Emacs", "Recursive directory scanning"]
limitations: ["May not support all modern languages", "Configuration requires manual setup"]
```

That is a README summary, not an answer. The ctags man page *does* contain the kinds vocabulary,
the `scope:`/`signature:`/`end:` extension fields, and the `--extras=+q` qualified-name behaviour
— all of which the frontier arm extracted from the same page. **The information was fetched and
then discarded at the extraction step.**

`research_url(focus=...)` uses the focused prompt and would not have done this. So the practical
guidance — worth putting in the tool's own docs — is:

> `search_topic` answers *"what is out there about X"*. It does **not** answer *"what does X say
> about Y"*. For the latter, find the URL and call `research_url(url, focus=Y)`.

The frontier arm's advantage in this run was **not better search** — it was that a human/agent
supplied the URL directly and asked a focused question.

## What IMPROVED since 2026-07-11 — the Auditor discriminated correctly

The prior field report's **D2** was a *non-discriminating auditor verdict*. That did not recur.
Here the Auditor returned:

```json
{"sufficient": false, "confidence": "low",
 "reasoning": "None of the gathered entries explicitly mention a 'SCIP symbol descriptor grammar
   specification' or provide details about grammar structures, syntax, or descriptor formats
   specific to SCIP. The relevant entry from www.gams.com focuses on solver parameters, not
   grammar definitions.",
 "missing_topics": ["SCIP grammar syntax rules", "symbol descriptor format specifications", ...]}
```

**It named the exact failure, including which URL was off-topic, and refused to claim
sufficiency.** That is the behaviour D2 asked for. Worth recording as a closed loop rather than
leaving the improvement unattributed.

The residual gap is that a correct "insufficient" verdict arrives **after** the expensive work,
and its `recommended_queries` (`"SCIP grammar specification official source"`) repeat the
ambiguous token — which is how iteration 2 landed on the ECMAScript spec. **The Auditor diagnosed
the problem and its remedy reproduced it.** That connects to **T-07** (heuristic gate must emit a
recovery *action*): a recommended query that repeats the term that caused the drift is not a
recovery action either.

## One genuinely useful output

A retrieved page's reference list surfaced **Kythe**, **Glean**, and **SemanticDB** — three
symbol-index systems absent from the frontier arm's brief, and SemanticDB is the direct ancestor
of SCIP's descriptor grammar. Fed back into the survey, they materially improved it. **Broad
open extraction over an adjacent document found what a targeted query would not have** — the
mode has real value; it is just not the mode this query needed.

## Cross-reference

Consuming survey: `llm` repo, `docs/research/symbol-addressed-editing/`
(`ref:symbol-addressed-editing-survey`), § 6.
