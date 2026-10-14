---
name: reflexion-repair
description: Failure-driven self-critique loop for debugging and test repair — reproduce the failure, form ONE hypothesis citing the concrete log/diff, make the smallest fix, re-run, reflect on what the new output proves. Stops on green or when the same hypothesis fails twice. Use when the user runs /reflexion-repair or hands you a failing test, bug, or error.
---

# reflexion-repair — failure-driven self-critique

**Updated:** `22-jun-2026`

**Charter:** The Reflexion pattern made disciplined: the agent improves by reflecting on *concrete evidence* of its last failure, not by vibing a new attempt. Every reflection must point at a real log line or diff hunk — generic "let me reconsider my approach" is banned. Pairs with strict TDD: you must see RED before GREEN.

**Loop archetype:** reflect-retry loop. **Circuit breakers:** same hypothesis fails 2× → STOP; 5 total iterations → STOP.

## Steps

1. **Reproduce (RED).** Run the failing thing from `$ARGUMENTS` (test, repro command, error). Capture the exact error + last ~10 lines + exit code. If you can't reproduce it, say so and stop — you can't repair what you can't see.

2. **One hypothesis, cited.** State a single, specific cause and quote the concrete evidence for it — the failing assertion, the stack frame, the diff line. No evidence → no hypothesis. One hypothesis per iteration (don't shotgun).

3. **Smallest fix.** Make the minimal change that this hypothesis predicts will fix it. Touch only what the hypothesis implicates.

4. **Re-run + reflect.** Run the check again, show output. Green → go to 6. Still red → write a 1–2 line reflection that says *what the new output proves* about the previous hypothesis, then form the next cited hypothesis. **If the same hypothesis fails twice, STOP** — escalate with everything tried.

5. **Repeat** 2–4 under the circuit breakers (5 iterations max).

6. **Stop + prove (GREEN).** Done only with the passing check shown (command + output + EXIT_CODE=0). Then state the root cause in one line. If breakers tripped first, report the hypotheses tried and the evidence against each — honestly, no false "fixed".

## The one guardrail that matters
**Every critique cites concrete logs/diffs, never generic reflection.** A reflection with no quoted evidence doesn't count as an iteration.

_Source: Reflexion (verbal self-reflection loop); project TDD rule (RED→GREEN, both shown); circuit-breaker ladder from CLAUDE.md._
