---
name: evaluator-optimizer
description: Best-of-N quality loop — write the scoring rubric FIRST, generate N independent candidates from different angles, score each against the rubric (separate evaluator pass to avoid self-bias), keep the best and graft the rest, iterate until the top score crosses threshold or plateaus. Use when the user runs /evaluator-optimizer or wants the best version of an open-ended deliverable (design, refactor, copy, algorithm).
---

# evaluator-optimizer — best-of-N with a rubric

**Updated:** `22-jun-2026`

**Charter:** For tasks where quality varies and there's no single right answer, one attempt-iterated loses to *generate-many → judge → synthesize*. The catch that keeps it honest: the rubric is written **before** any candidate exists, so scoring can't be reverse-engineered to bless whatever got produced. This is the loop GEPA-style reflective evolution formalizes.

**Loop archetype:** evaluator-optimizer / best-of-N. **Defaults:** N=3 candidates, 2 rounds max.

## Steps

1. **Write the rubric first.** Before generating anything, define 3–5 weighted criteria for `$ARGUMENTS` and, for each, *how it's measured* (a number, a check, or a concrete yes/no). Set a pass threshold **and a plateau epsilon** (the smallest score gain that justifies another round). Print the rubric, threshold, and epsilon. Do not look at any candidate yet.

2. **Generate N candidates from different angles.** Spawn N independent attempts (use parallel sub-agents via the Agent tool when the task is heavy), each told to optimize for a *different* emphasis — e.g. simplest, most robust, most performant. Keep them isolated so they don't converge.

3. **Score (separate evaluator).** Evaluate each candidate against the frozen rubric — ideally a fresh evaluator pass/sub-agent that didn't write the candidates, to kill self-bias. Print a scorecard: candidate × criterion → score, with the measured evidence per cell.

4. **Keep best + graft + re-score.** Take the top scorer; pull in the specific stronger ideas from runners-up where the scorecard shows they win. **Re-score the synthesized version against the frozen rubric** — a graft can regress, so what you deliver must be the highest-*scored* artifact, not the assumed-best one.

5. **Iterate or stop.** If top score ≥ threshold → deliver. If a second round would help and you have rounds left, generate variants of the leader and re-score. **Stop when the threshold is met or the gain between rounds is ≤ epsilon (plateau)** — don't grind a flat curve.

## The one guardrail that matters
**Rubric before candidates — no post-hoc scoring.** If the criteria were written or edited after seeing outputs, the result is rationalization, not evaluation.

_Source: Anthropic "evaluator-optimizer" agent pattern; GEPA: Reflective Prompt Evolution (arXiv 2507.19457)._
