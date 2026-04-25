# Auditor Iteration Control — Ideas to Revisit

*Stashed 2026-04-23 during Phase 3.6 design (Conductor wire-up). Not implemented in 3.6;
revisit once we have real-run data on how the loop behaves in practice.*

<!-- ref:auditor-iteration-control-ideas -->

Two complementary ideas for giving the Conductor's audit loop better stopping behavior
than "always stop on the first `sufficient=True`, otherwise stop at `max_iterations`".

## Idea 1 — Configurable confidence threshold (caller-side)

Add a parameter to the Conductor loop:

```python
stop_on_confidence: Literal["low", "medium", "high"] = "low"
```

Semantics: stop only on a `sufficient=True` verdict whose `confidence` is at least the
threshold. Default `"low"` reproduces current behavior (stop on any sufficient). Users
who want safer loops set `"medium"` or `"high"`; the loop continues iterating when a
low-confidence "sufficient" comes back.

**Pros:** trivial to implement; entirely caller-controlled; no prompt changes; backward
compatible.

**Cons:** the Auditor's confidence field becomes load-bearing in a way it may not have
been tuned for — if the model is sloppy about `low` vs `medium`, the threshold is noise.
Caller has to guess the right value without feedback.

## Idea 2 — Iteration-aware Auditor prompt (domain-side)

Thread iteration state into the sufficiency prompt so the Auditor itself raises its bar
as iterations progress:

```text
This is iteration {n} of {max}. Earlier iterations already explored: {prior_queries}.
Bias toward 'sufficient' unless a core aspect of the query is clearly missing —
additional iterations are expensive and yield diminishing returns.
```

**Pros:** puts the decision in the domain expert (the Auditor itself) rather than
layering a heuristic on top. Naturally captures the vision's "decreasing 'more' signal"
(vision doc §Architecture, line 98). One place to tune — the prompt template.

**Cons:** more invasive. Requires:
- New fields on `SufficiencyVerdict` input (iteration number, budget, prior queries)
- Prompt template changes + re-tuning
- New test fixtures covering iteration-aware behavior
- Possibly new signals (e.g. "iterations_remaining" as a heuristic signal)

Risk: the model may over-correct and declare sufficient too early.

## When to revisit

After Phase 3.6 is wired and we have logs from real queries, look at:

- How often the loop hits `max_iterations` vs stops early
- Whether low-confidence sufficient verdicts correlate with actually-poor research
- Whether Auditor `recommended_queries` converge or drift across iterations

If low-confidence sufficients are frequent and correlate with bad outputs, Idea 1 gives
a quick fix. If the loop routinely overshoots, Idea 2 is the more architecturally
aligned solution.

## Combined option

The two are not exclusive. Idea 2 handles the "should I say sufficient at all" decision;
Idea 1 gives the caller a safety net if they don't trust the Auditor's calibration yet.
A conservative rollout: ship Idea 1 first (cheap, reversible), gather data, then
consider Idea 2 if it's still warranted.

<!-- /ref:auditor-iteration-control-ideas -->
