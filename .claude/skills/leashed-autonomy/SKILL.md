---
name: leashed-autonomy
description: Karpathy-style autonomy slider — run a task autonomously inside an explicit leash (autonomy level 1–5, blast-radius boundaries, budget, escalation rule). The agent works freely until an action would cross a boundary, then stops and asks. Use when the user runs /leashed-autonomy or wants bounded autonomous execution.
---

# leashed-autonomy — the autonomy slider

**Updated:** `22-jun-2026`

**Charter:** Karpathy's framing of agentic engineering: the human is the decision-maker *at the checkpoints*; execution *between* checkpoints is fully autonomous. The skill is judgment about how much leash to give — so you declare the leash up front, out loud, and the agent physically stops at its end instead of guessing. *"A recurring loop with logs, budgets, stop conditions, and escalation is an engineering system."*

**Loop archetype:** bounded autonomous loop. **Default level:** 2.

## Steps

1. **Declare the autonomy level** (from `$ARGUMENTS`, else default 2). Print it:
   - **L1 — propose:** read + plan only; produce a diff/plan, change nothing.
   - **L2 — sandbox:** edit + run tests locally; **ask before any commit.**
   - **L3 — commit-on-green:** edit, test, commit to the current branch when checks pass; no push.
   - **L4 — branch:** multi-file work on a feature branch, push the branch; **ask before opening a PR.**
   - **L5 — until-goal:** run to the verifiable goal or a budget cap with no mid-loop check-ins.

2. **Draw the blast radius.** List the files/dirs it may touch and the hard-forbidden set (no `rm -rf`, no force-push, no `.env`/secret reads, no network calls to prod, no commits to the default/protected branch — `master`/`main`). Anything outside is a boundary.

3. **Set the budget + escalation.** Max iterations, max wall-clock, max files changed (defaults: 8 iters / 20 min / 10 files). State the escalation rule: *the moment an action would cross a boundary or bust the budget → STOP and ask, with the proposed action quoted.*

4. **Run inside the leash.** Work toward the goal autonomously, logging each action. Verify with a deterministic check (borrow `goal-act-verify`'s discipline). Never silently widen the leash.

5. **Stop** when: the goal is verified, the budget/risk threshold is hit, or a boundary crossing needs approval. Report what was done, what's left, and exactly which boundary stopped you.

## The one guardrail that matters
**A boundary crossing requires explicit user approval — every time.** Convenience never promotes the autonomy level on its own.

_Source: Andrej Karpathy, "agentic engineering" / autonomy slider (Sequoia talk, Mar 2026); the leashed-execution-with-checkpoints pattern._
