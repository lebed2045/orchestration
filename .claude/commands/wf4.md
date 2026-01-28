# /wf4 - Workflow v4 (Autonomous)

**Version 4**: Maximum autonomy. Infer from codebase, auto-update on feedback, minimal human involvement.

**Core principle**: DO THE WORK. Only ask humans when truly blocked.

Uses agents: `coder-v4`, `planner-v4`, `intake-v4`, `fresh-reviewer-v4`

---

## PHILOSOPHY: AUTONOMOUS BY DEFAULT

| Old Behavior (wf1-3) | New Behavior (wf4) |
|----------------------|-------------------|
| Ask about inputs/outputs/edge cases | Infer from codebase + task description |
| "Should I update the plan?" | Just update it |
| "Should I proceed?" | Proceed unless blocked |
| Wait for approval at every gate | Only pause for CRITICAL decisions |
| Ask clarifying questions | Make reasonable assumptions, document them |

**Human involvement triggers (ONLY these):**

1. Multiple valid architectural approaches with significant trade-offs
2. Destructive operations (delete files, breaking changes)
3. Ambiguity that cannot be resolved from codebase context
4. Circuit breaker activated (2x same error)

---

## VSCODE COMPATIBILITY (CRITICAL)

**VSCode plugin has a bug with parallel tool calls. To avoid "API Error: 400":**

1. **DO NOT use Task tool with Explore agent** - It makes parallel calls that crash
2. **Explore manually** - Use Read, Grep, Glob directly, ONE AT A TIME
3. **Sequential tool calls only** - Never batch multiple tool calls in one response
4. **Wait for each result** - Before making next tool call

---

## MANDATORY PROOF BLOCKS

Same as wf3 - these are non-negotiable:

### BASELINE_BLOCK (captured BEFORE any changes)

```text
┌─────────────────────────────────────────────┐
│ BASELINE_BLOCK                              │
├─────────────────────────────────────────────┤
│ Tests passing: [N]                          │
│ Tests failing: [N]                          │
│ Warnings: [N]                               │
│ Git SHA: [hash]                             │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

### EXECUTION_BLOCK (required for ANY completion claim)

```text
┌─────────────────────────────────────────────┐
│ EXECUTION_BLOCK                             │
├─────────────────────────────────────────────┤
│ $ [actual command run]                      │
│ [actual output - last 20+ lines]            │
│ EXIT_CODE: [0 or N]                         │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

### REGRESSION_DELTA (captured AFTER changes)

```text
┌─────────────────────────────────────────────┐
│ REGRESSION_DELTA                            │
├─────────────────────────────────────────────┤
│ Tests: [N] passed (was [M]) [+/-diff]       │
│ Warnings: [N] (was [M]) [+/-diff]           │
│ VERDICT: [SAFE|REGRESSION]                  │
└─────────────────────────────────────────────┘
```

---

## State Tracking

Every response MUST start with:

```text
[WF4.PhaseX] [Baseline: SET|UNSET] [Regression: SAFE|DETECTED|UNKNOWN] [Status: in_progress|blocked|complete]
```

---

## Phase Flow (8 Phases, 1 Gate)

### Phase 1: BASELINE_CAPTURE

**Before touching ANY code:**

1. Run existing tests, capture output
2. Count current warnings/errors
3. Record git SHA
4. Output BASELINE_BLOCK

```bash
# Capture baseline
npm test 2>&1 | tee /tmp/baseline.txt || true
echo "TESTS: $(grep -c 'passing\|✓' /tmp/baseline.txt || echo 0)"
echo "WARNINGS: $(grep -ci 'warn' /tmp/baseline.txt || echo 0)"
echo "GIT_SHA: $(git rev-parse HEAD)"
```

**Do NOT proceed without BASELINE_BLOCK.**

---

### Phase 2: AUTONOMOUS_INTAKE

**NO CLARIFYING QUESTIONS by default.** Infer everything from:

1. User's task description
2. Codebase exploration (Read, Grep, Glob)
3. Existing patterns in the code
4. Test files (they document expected behavior)

**Process:**

1. Read user's task
2. Explore relevant codebase areas (5-10 files max)
3. Document ASSUMPTIONS (things you inferred, not asked)
4. Write `.claude/temp/spec.md` with inferred requirements

**Spec format:**

```markdown
# Specification: [Feature Name]

## Task
[User's original request]

## Inferred Requirements
- IR1: [inferred from codebase/task]
- IR2: [inferred from codebase/task]

## Assumptions Made
- A1: [assumption] - Inferred from [source]
- A2: [assumption] - Inferred from [source]

## Files to Modify
| File | Purpose |
|------|---------|
| ... | ... |

## Success Criteria
- [ ] [criterion based on task]
```

**ONLY ask human if:**
- Task is fundamentally ambiguous (e.g., "improve the app")
- Multiple conflicting patterns exist in codebase
- Destructive action required

---

### Phase 3: AUTONOMOUS_PLANNING

**Design architecture based on inferred spec.**

1. Write `.claude/temp/architecture.md`:
   - Component design
   - File structure
   - TDD test plan
   - Regression checkpoints

**NO human approval needed.** Proceed directly to review.

---

### Phase 4: TRIPLE_REVIEW_PLAN (AUTO-FIX)

**Key change: Auto-update on feedback, don't ask permission.**

**ALL THREE reviewers must approve before proceeding.**

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini`:

```text
Review spec + architecture. Be specific about issues.
VERDICT: APPROVED or NEEDS_WORK
If NEEDS_WORK, list EXACT changes needed.
```

#### Reviewer 2: Codex

Call `mcp__codex-cli__codex` tool with these parameters:

| Parameter          | Value                                         |
|--------------------|-----------------------------------------------|
| `prompt`           | See below                                     |
| `workingDirectory` | Project root path                             |

**Prompt content:**

```text
Review the plan files for a software implementation task.

Read these files:
- .claude/temp/spec.md
- .claude/temp/architecture.md

Evaluate:
1. Requirements completeness - are all user needs captured?
2. Architecture feasibility - is the design sound?
3. TDD strategy - are tests well-planned?
4. Regression strategy - how will we prevent breaking existing functionality?

Output format:
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES: [numbered list or "none"]
SUGGESTIONS: [numbered list or "none"]
```

**Capture output**: Paste the Codex response directly. The verdict line must be visible.

#### Reviewer 3: Isolated Claude

```bash
claude -p "Review .claude/temp/spec.md and .claude/temp/architecture.md
Output VERDICT + specific ISSUES to fix." \
  --allowedTools Read,Glob,Grep,Write \
  --model sonnet \
  --print
```

#### AUTO-FIX LOOP (max 3 iterations)

```text
IF any reviewer says NEEDS_WORK:
  1. Parse their specific feedback
  2. UPDATE spec/architecture directly (no asking)
  3. Re-run ALL THREE reviewers
  4. Repeat until all APPROVED or max iterations
```

**Only escalate to human if:**

- Reviewers contradict each other
- 3 iterations exhausted with no convergence

Output after approval:

```text
┌─────────────────────────────────────────────┐
│ PLAN AUTO-APPROVED                          │
├─────────────────────────────────────────────┤
│ Iterations: [N]                             │
│ Gemini: APPROVED                            │
│ Codex:  APPROVED                            │
│ Claude: APPROVED                            │
│ Auto-fixes applied: [list]                  │
└─────────────────────────────────────────────┘
```

---

### Phase 5: TDD_RED (ISOLATED CODER)

Spawn isolated coder to write failing tests.

```bash
claude -p "You are a TDD test writer.
Read: .claude/temp/spec.md, .claude/temp/architecture.md
Write tests that MUST FAIL.
LOOP until tests fail, then output EXECUTION_BLOCK." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

VERIFY: EXECUTION_BLOCK shows EXIT_CODE≠0 (tests failing).

---

### Phase 6: TDD_GREEN (ISOLATED CODER)

Spawn isolated coder to implement.

```bash
claude -p "You are a TDD implementer.
Read: .claude/temp/spec.md, .claude/temp/architecture.md, tests/, /tmp/baseline.txt
CRITICAL: Test files are READ-ONLY.
CRITICAL: After EVERY change, check REGRESSION_DELTA.
LOOP (max 5): Fix one error until tests pass.
Output EXECUTION_BLOCK + REGRESSION_DELTA when done." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

VERIFY: EXIT_CODE=0 + REGRESSION_DELTA=SAFE

---

### Phase 7: TRIPLE_REVIEW_CODE (AUTO-FIX)

Same auto-fix pattern as Phase 4. **ALL THREE reviewers must approve.**

#### Reviewer 1: Gemini

```text
Review implementation.
VERDICT: APPROVED or NEEDS_WORK
If NEEDS_WORK, list EXACT code changes needed.
```

#### Reviewer 2: Codex

Call `mcp__codex-cli__codex` tool:

| Parameter          | Value                                         |
|--------------------|-----------------------------------------------|
| `prompt`           | See below                                     |
| `workingDirectory` | Project root path                             |

**Prompt content:**

```text
Review the implementation for a software task.

Read the source files and tests. Evaluate:
1. Does implementation match the spec in .claude/temp/spec.md?
2. Code quality and patterns
3. Test coverage adequate?
4. Any regressions or breaking changes?

Output format:
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES: [numbered list or "none"]
MUST_FIX: [critical items or "none"]
```

#### Reviewer 3: Isolated Claude

```bash
claude -p "Review src/ and tests/.
Run: npm test 2>&1 | tee /tmp/final.txt; echo EXIT_CODE: \$?
Compare warnings to baseline: grep -ci warn /tmp/final.txt vs /tmp/baseline.txt
Output to .claude/temp/code-review.md:
- VERDICT
- EXIT_CODE
- REGRESSION_DELTA (compare to baseline)
- SMOKE_TEST block
- MUST_FIX table (if any)" \
  --allowedTools Read,Glob,Grep,Write,Bash \
  --print
```

#### SMOKE_TEST (required)

Run platform-specific smoke test:

```bash
npm test 2>&1 | tee /tmp/smoke.txt
echo "Warnings: $(grep -ci warn /tmp/smoke.txt || echo 0)"
```

Output SMOKE_TEST block:

```text
┌─────────────────────────────────────────────┐
│ SMOKE_TEST                                  │
├─────────────────────────────────────────────┤
│ Method: [npm test | Editor logs | etc]      │
│ Warnings before: [N]                        │
│ Warnings after: [N]                         │
│ New errors: [list or "none"]                │
│ VERDICT: [PASS|FAIL]                        │
└─────────────────────────────────────────────┘
```

#### AUTO-FIX LOOP:

```text
IF NEEDS_WORK:
  1. Apply reviewer's suggested fixes
  2. Re-run tests
  3. Re-run reviewers
  4. Repeat until APPROVED or max 3 iterations
```

---

### Phase 8: COMPLETION

Only output completion if ALL conditions met:

- [ ] BASELINE_BLOCK captured
- [ ] EXECUTION_BLOCK shows EXIT_CODE=0
- [ ] REGRESSION_DELTA shows SAFE
- [ ] Both reviewers APPROVED

```text
┌─────────────────────────────────────────────┐
│ WF4_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description]                         │
│ Status: SUCCESS                             │
│ Assumptions made: [list]                    │
│ Auto-fixes applied: [count]                 │
│ Human interactions: [count - should be 0-1] │
│ Tests: [N passed]                           │
│ Regression: SAFE                            │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

Output: `✓ ORCHESTRATION COMPLETE`

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No BASELINE_BLOCK | STOP. Capture baseline first |
| Claim without EXECUTION_BLOCK | RETRACT. Run verification |
| REGRESSION_DELTA = REGRESSION | STOP. Auto-revert, try different approach |
| Same error 2x | STOP. Escalate to human |
| Review loop 3x no convergence | STOP. Escalate to human |
| Reviewers contradict | STOP. Escalate to human |

---

## Comparison: wf3 vs wf4

| Aspect | wf3 | wf4 |
|--------|-----|-----|
| Intake questions | Ask about inputs/outputs/edge cases | Infer from codebase |
| Plan approval | Wait for human | Auto-approve after triple review |
| Reviewers | Gemini + Isolated Claude (2) | Gemini + Codex + Isolated Claude (3) |
| Review feedback | "Should I update?" | Just update |
| Gates | 3 (plan, tests, code) | 2 (plan, code) - both auto-fix |
| Human interactions | 3-5 typical | 0-1 typical |
| Autonomy | Medium | Maximum |

---

## User's Task

$ARGUMENTS
