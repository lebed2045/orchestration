---
name: goal-act-verify
description: The minimal disciplined agentic loop — restate the task as a VERIFIABLE end-state, take one action, prove it with a cheap deterministic check, repeat until the check passes. Use when the user runs /goal-act-verify or wants a single task driven to a checkable "done".
---

# goal-act-verify — the disciplined base loop

**Updated:** `22-jun-2026`

**Charter:** The cheapest, most reliable loop there is. Boris Cherny's three-stage definition — *goal → action → evaluation, repeat* — with one rule that makes it work: the stop condition is a check a machine can run, not a feeling. Karpathy: *"if you cannot evaluate the result, you cannot safely automate the loop."* This is the loop to reach for first; the others are specializations.

**Loop archetype:** goal-loop (run-until-condition). **Default cap:** 6 iterations.

## Steps

1. **Restate the goal as a verifiable end-state.** Take `$ARGUMENTS` and rewrite it as a state, not a process. "Refactor X" → "all tests in `tests/` pass with exit 0 AND no function in `X` exceeds 40 lines." If the user already gave a checkable state, keep it. Print the restated goal and the check you'll use; if you had to convert a vague ask, say so in one line (announce-and-proceed).

2. **Name the check (cheapest first).** Pick the most deterministic signal that proves the goal: compile → typecheck → lint → unit test → grep/assertion. Prefer something already in the repo. AI-as-judge only for what deterministic checks genuinely can't cover (and say when you fall back to it). Write the check now if it doesn't exist.

3. **Capture baseline + freeze the check.** Run the check once before changing anything; record pass/fail. This is your regression guard. **From here the check is frozen** — if you edit what you measure mid-loop to get a pass, the stop condition is meaningless.

4. **Loop — one action per turn.** Take a single concrete action toward the goal → run the check → show the last ~10 lines + exit code. Pass → go to 5. Fail → read the output, adjust, repeat. Same failure twice → STOP and escalate (don't thrash).

5. **Stop + prove.** Done only when the check passes with shown output (EXECUTION_BLOCK: command + output + EXIT_CODE=0). If the cap (6) is hit first, STOP and report the last state honestly — never claim done without the passing check.

## The one guardrail that matters
**No "done" without the check's real output.** A passing claim with no command+exit-code shown is a failed loop, full stop.

_Source: Anthropic Claude Code `/goal`; Boris Cherny's three-stage loop definition (Jun 2026); Karpathy's "evaluable metric" rule._
