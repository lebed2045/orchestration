# /wf7 - Workflow v7 (Token-Optimized)

**Version 7**: Token-optimized with parallel TDD_RED and sequential reviews.

**Core principle**: 75% fewer reviewer calls than wf6 while maintaining quality.

Based on wf6 retrospective: Codex most useful, Gemini occasional value, Sonnet/Opus redundant in reviews.

---

## VSCODE COMPATIBILITY (CRITICAL)

**VSCode plugin has a bug with parallel tool calls. To avoid "API Error: 400":**

1. **DO NOT use Task tool with Explore agent** - It makes parallel calls that crash
2. **Explore manually** - Use Read, Grep, Glob directly, ONE AT A TIME
3. **Sequential tool calls only** - Never batch multiple tool calls in one response
4. **Wait for each result** - Before making next tool call

---

## MANDATORY PROOF BLOCKS

### BASELINE_BLOCK (captured BEFORE any changes)

```text
┌─────────────────────────────────────────────┐
│ BASELINE_BLOCK                              │
├─────────────────────────────────────────────┤
│ Tests passing: [N]                          │
│ Tests failing: [N]                          │
│ Warnings: [N]                               │
│ Errors: [N]                                 │
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
│ Errors: [N] (was [M]) [+/-diff]             │
│ VERDICT: [SAFE|REGRESSION]                  │
└─────────────────────────────────────────────┘
```

---

## Git Staging Discipline

| Phase | Action | Git Staging |
|-------|--------|-------------|
| TDD_RED | Write tests | Not staged yet |
| After TDD_RED | Merge tests | **Auto-stage tests** |
| TDD_GREEN | Write implementation | Not staged yet |
| CODE_REVIEW (Gate 2) | Review code | **Ask user** before staging |
| Completion | Done | **Never auto-commit** |

---

## State Tracking

Every response MUST start with:

```text
[WF7.PhaseX] [Baseline: SET|UNSET] [Regression: SAFE|DETECTED|UNKNOWN] [Status: in_progress|blocked|complete]
```

---

## Phase Flow (9 Phases, 2 Gates)

### Phase 1: BASELINE_CAPTURE

**Before touching ANY code:**

1. Run existing tests, capture output
2. Count current warnings/errors
3. Record git SHA
4. Output BASELINE_BLOCK

```bash
# Capture baseline (adapt command to project)
npm test 2>&1 | tee /tmp/baseline.txt || true
echo "TESTS: $(grep -c 'passing\|✓' /tmp/baseline.txt || echo 0)"
echo "WARNINGS: $(grep -ci 'warn' /tmp/baseline.txt || echo 0)"
echo "GIT_SHA: $(git rev-parse HEAD)"
```

**Do NOT proceed without BASELINE_BLOCK.**

---

### Phase 2: INTAKE

Enter plan mode, ask clarifying questions.

1. Call `EnterPlanMode` tool
2. Ask clarifying questions using `AskUserQuestion`
3. Cover: issue, expected behavior, reproduction steps
4. Write spec to `.claude/temp/spec.md` (include BASELINE_BLOCK)
5. VERIFY: Show `cat .claude/temp/spec.md | head -30` output

---

### Phase 3: PLANNING

Design architecture (still in plan mode).

1. Design architecture based on spec
2. Write to `.claude/temp/architecture.md`:
   - Component design
   - File structure
   - Dependencies
   - TDD test plan
   - Regression checkpoints
   - Smoke test plan
3. VERIFY: Show `cat .claude/temp/architecture.md | head -30` output

---

### Phase 4: GATE 1 - PLAN_REVIEW (Codex + Gemini)

**Exit plan mode to run reviewers.**

1. Call `ExitPlanMode` tool
2. Initialize gate review file:

```bash
echo "# Gate 1: Plan Review" > .claude/temp/gate-1-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-1-reviews.md
```

#### Reviewer 1: Codex (runs first)

Call `mcp__codex-cli__codex`:

| Parameter | Value |
|-----------|-------|
| prompt | See below |
| workingDirectory | Project root |

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
REVIEWER: Codex
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES_CAUGHT: [numbered list or "none"]
SUGGESTIONS: [numbered list or "none"]
```

**Append Codex output to gate file.**

#### Reviewer 2: Gemini (runs second)

Call `mcp__gemini__ask-gemini`:

```text
Working directory: [pwd]

Review the plan for a software implementation task.

Read: .claude/temp/spec.md and .claude/temp/architecture.md

Also read Codex's review in .claude/temp/gate-1-reviews.md

Evaluate:
1. Requirements completeness
2. Architecture feasibility
3. TDD strategy adequacy
4. Regression prevention strategy
5. Did Codex miss anything?

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
CODEX_MISSED: [issues Codex didn't catch, or "none"]
ISSUES_CAUGHT: [numbered list or "none"]
SUGGESTIONS: [numbered list or "none"]
```

**Append Gemini output to gate file.**

#### BLOCKING: Verify Gate 1 Review File

```bash
echo "=== Gate 1 Review File Verification ==="
cat .claude/temp/gate-1-reviews.md
echo ""
grep -c "REVIEWER:" .claude/temp/gate-1-reviews.md | xargs -I {} test {} -ge 2 && echo "✓ Both reviewers recorded" || echo "✗ MISSING REVIEWERS"
```

#### Gate 1 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 1 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Gemini: [APPROVED|NEEDS_WORK]               │
├─────────────────────────────────────────────┤
│ Review file verified: [YES|NO]              │
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-1-reviews.md │
└─────────────────────────────────────────────┘
```

**If ANY reviewer returns NEEDS_WORK (max 3 iterations):**

1. Call `EnterPlanMode` tool
2. Fix issues in spec/architecture
3. Call `ExitPlanMode` tool
4. Re-run BOTH reviewers

---

### Phase 5: USER_GATE_PLAN

Present plan for user approval.

**MUST include these tables:**

#### TLDR: Files Summary

```text
| File | Action | Purpose |
|------|--------|---------|
| [path] | CREATE/MODIFY/DELETE | [brief purpose] |
```

#### Implementation Details

```text
| Component | What Will Be Made | Lines Est. |
|-----------|-------------------|------------|
| [name] | [description] | ~[N] |
```

**MUST PRESENT:**

1. Artifact paths: spec.md, architecture.md, gate-1-reviews.md
2. Spec summary: Key requirements (3-5 bullet points)
3. Architecture summary: Components, files to create/modify
4. TDD plan: What tests will be written
5. Regression strategy: How we'll prevent regressions
6. Both review verdicts

```text
┌─────────────────────────────────────────────┐
│ PLAN SUMMARY                                │
├─────────────────────────────────────────────┤
│ Spec: .claude/temp/spec.md                  │
│ Architecture: .claude/temp/architecture.md  │
│ Reviews: .claude/temp/gate-1-reviews.md     │
├─────────────────────────────────────────────┤
│ BASELINE:                                   │
│ • Tests: [N] passing                        │
│ • Warnings: [N]                             │
│ • Git SHA: [hash]                           │
├─────────────────────────────────────────────┤
│ REVIEW VERDICTS:                            │
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Gemini: [APPROVED|NEEDS_WORK]               │
└─────────────────────────────────────────────┘
```

Output: `--- WAITING FOR PLAN APPROVAL ---`

Wait for user approval.

---

### Phase 6: TDD_RED (Orchestrator + Codex)

**Parallel test writing: Orchestrator writes tests, then Codex writes additional tests.**

#### Step 1: Orchestrator writes tests

Write RED tests directly based on spec and architecture:
- At least 1 test per requirement
- Tests MUST FAIL (no implementation exists)
- Include falsifiability checks (tests cannot pass with `return true`)

Run tests to verify they fail:

```bash
npm test 2>&1 | tee /tmp/tdd-red.txt
echo "EXIT_CODE: $?"
# Must be non-zero (tests failing)
```

#### Step 2: Codex writes additional tests

Call `mcp__codex-cli__codex`:

| Parameter | Value |
|-----------|-------|
| prompt | See below |
| workingDirectory | Project root |

```text
Read .claude/temp/spec.md and .claude/temp/architecture.md

Review the existing tests that were just written.

Write at least 1 additional RED test that covers:
- Edge cases the existing tests missed
- Boundary conditions
- Error handling paths

Tests MUST FAIL (no implementation exists yet).
Ensure tests are FALSIFIABLE (cannot pass with trivial implementation like 'return true').

Output:
- The test code you wrote
- EXECUTION_BLOCK showing tests fail
```

#### Step 3: Merge and verify

1. Merge Codex's tests into test files
2. Dedup any overlapping tests
3. Run all tests to verify RED phase:

```bash
npm test 2>&1 | tee /tmp/tdd-red-merged.txt
echo "EXIT_CODE: $?"
```

**EXECUTION_BLOCK must show EXIT_CODE≠0 (tests failing).**

#### Auto-stage tests

```bash
git add tests/  # or test files location
echo "✓ Tests staged after TDD_RED"
```

---

### Phase 7: TDD_GREEN (Orchestrator)

Orchestrator implements directly.

1. Read merged tests
2. Implement code to pass tests
3. Do NOT modify test files
4. After EVERY change, check REGRESSION_DELTA

```bash
npm test 2>&1 | tee /tmp/tdd-green.txt
echo "EXIT_CODE: $?"
```

**EXECUTION_BLOCK must show EXIT_CODE=0 (tests passing).**

Output REGRESSION_DELTA comparing to baseline.

---

### Phase 8: GATE 2 - CODE_REVIEW (Codex + Gemini + CodeSmell)

**Triple check: Codex reviews first, then Gemini, then CodeSmell.**

Initialize gate review file:

```bash
echo "# Gate 2: Code Review" > .claude/temp/gate-2-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-2-reviews.md
```

#### Step 1: CodeSmell Check

```bash
# Run on each modified file
for file in $(git diff --name-only --cached); do
  echo "Checking: $file"
  ./Tools/code-smell.sh "$file" --gemini 2>&1 | tee -a /tmp/codesmell.txt
done
echo ""
echo "=== CodeSmell Results ==="
grep -E "Score:|PASS|FAIL" /tmp/codesmell.txt
```

**If any file scores < 60, STOP and refactor before continuing.**

#### Step 2: Codex Review (runs first)

Call `mcp__codex-cli__codex`:

| Parameter | Value |
|-----------|-------|
| prompt | See below |
| workingDirectory | Project root |

```text
Review the implementation for a software task.

Read the source files and tests. Evaluate:
1. Does implementation match the spec in .claude/temp/spec.md?
2. Code quality and patterns
3. Test coverage adequate?
4. Any regressions or breaking changes?
5. Security issues?

Output format:
REVIEWER: Codex
VERDICT: [APPROVED|NEEDS_WORK]
SPEC_MATCH: [YES|NO]
CODE_QUALITY: [assessment]
SECURITY_ISSUES: [list or "none"]
ISSUES_CAUGHT: [numbered list or "none"]
```

**Append to gate file.**

#### Step 3: Gemini Review (runs second)

Call `mcp__gemini__ask-gemini`:

```text
Working directory: [pwd]

Review the implementation code for quality and security.

Read: src/ files, tests/, .claude/temp/spec.md

Also read Codex's review in .claude/temp/gate-2-reviews.md

Check:
1. Code quality
2. Security issues (OWASP top 10)
3. Test coverage
4. Regression status
5. Did Codex miss anything?

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
CODEX_MISSED: [issues Codex didn't catch, or "none"]
EXECUTION_CHECK: [YES|NO - tests pass?]
REGRESSION_CHECK: [YES|NO - warnings increased?]
CODE_QUALITY: [assessment]
SECURITY_ISSUES: [list or "none"]
ISSUES_CAUGHT: [numbered list or "none"]
```

**Append to gate file.**

#### SMOKE_TEST

Run platform-specific smoke test:

```bash
npm test 2>&1 | tee /tmp/smoke.txt
echo "Warnings: $(grep -ci warn /tmp/smoke.txt || echo 0)"
```

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

#### BLOCKING: Verify Gate 2 Review File

```bash
echo "=== Gate 2 Review File Verification ==="
cat .claude/temp/gate-2-reviews.md
echo ""
grep -c "REVIEWER:" .claude/temp/gate-2-reviews.md | xargs -I {} test {} -ge 2 && echo "✓ Both reviewers recorded" || echo "✗ MISSING REVIEWERS"
```

#### Gate 2 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 2 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ CodeSmell: [PASS (all ≥60) | FAIL]          │
│ Codex:     [APPROVED|NEEDS_WORK]            │
│ Gemini:    [APPROVED|NEEDS_WORK]            │
├─────────────────────────────────────────────┤
│ SMOKE_TEST: [PASS|FAIL]                     │
│ REGRESSION_DELTA: [SAFE|REGRESSION]         │
├─────────────────────────────────────────────┤
│ Review file verified: [YES|NO]              │
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-2-reviews.md │
└─────────────────────────────────────────────┘
```

**All must pass: CodeSmell ≥60 + Codex APPROVED + Gemini APPROVED + SMOKE_TEST PASS + REGRESSION_DELTA SAFE**

---

### Phase 9: COMPLETION

Only output completion if ALL conditions met:

- [ ] BASELINE_BLOCK captured at start
- [ ] EXECUTION_BLOCK shows EXIT_CODE=0
- [ ] REGRESSION_DELTA shows SAFE
- [ ] SMOKE_TEST shows PASS
- [ ] CodeSmell all files ≥60
- [ ] Codex APPROVED at both gates
- [ ] Gemini APPROVED at both gates
- [ ] Both gate files exist with 2 reviewers each

#### BLOCKING: Verify Gate Files

```bash
echo "=== Gate File Verification ==="
echo ""
echo "Gate 1:"
ls -la .claude/temp/gate-1-reviews.md 2>/dev/null && echo "✓ EXISTS" || echo "✗ MISSING"
echo "Reviewers: $(grep -c 'REVIEWER:' .claude/temp/gate-1-reviews.md 2>/dev/null || echo 0)"
echo ""
echo "Gate 2:"
ls -la .claude/temp/gate-2-reviews.md 2>/dev/null && echo "✓ EXISTS" || echo "✗ MISSING"
echo "Reviewers: $(grep -c 'REVIEWER:' .claude/temp/gate-2-reviews.md 2>/dev/null || echo 0)"
```

#### Completion Checklist

```text
┌─────────────────────────────────────────────┐
│ COMPLETION CHECKLIST                        │
├─────────────────────────────────────────────┤
│ [x] Baseline captured                       │
│ [x] Tests pass (EXECUTION_BLOCK shown)      │
│ [x] No regression (REGRESSION_DELTA=SAFE)   │
│ [x] Warnings stable (before/after same)     │
│ [x] Smoke test pass (SMOKE_TEST shown)      │
│ [x] CodeSmell all ≥60                       │
│ [x] All reviews passed (2 gates × 2 each)   │
│ VERDICT: COMPLETE                           │
└─────────────────────────────────────────────┘
```

#### WF7_RESULT Block

```text
┌─────────────────────────────────────────────┐
│ WF7_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: SUCCESS                             │
│ Artifacts: [files created/modified]         │
│ Tests: [N passed, 0 failed]                 │
│ Regression: SAFE                            │
│ Token savings vs wf6: ~75%                  │
│ Reviewers used: 4 (was 12 in wf6)           │
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
| REGRESSION_DELTA = REGRESSION | STOP. Fix regression first |
| Warnings increased | STOP. Fix warnings first |
| CodeSmell < 60 | STOP. Refactor before continuing |
| Same error 2x | STOP. Escalate to user |
| Tests fail 5x | STOP. "MANUAL INTERVENTION REQUIRED" |
| Review fails 3x (any gate) | STOP. "REVIEW LOOP EXCEEDED" |
| SMOKE_TEST FAIL | STOP. Cannot claim done |
| Gate file missing | STOP. Re-run gate reviewers |

Output format:

```text
⚠️ CIRCUIT BREAKER ACTIVATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trigger: [which]
Attempts: [N/max]
Last error: [paste]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Options:
  a) git reset --hard [baseline SHA]
  b) User provides context
  c) Different approach

Awaiting user decision...
```

**Then output WF7_RESULT block with Status: FAILURE:**

```text
┌─────────────────────────────────────────────┐
│ WF7_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: FAILURE                             │
│ Artifacts: [files created/modified so far]  │
│ Tests: [N passed, M failed]                 │
│ Regression: [SAFE|DETECTED]                 │
│ Gate reached: [1|2]                         │
│ Blocker: [specific reason for failure]      │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

---

## Anti-Sycophancy Oath

```text
I will NOT claim "done" to end a frustrating session.
I will NOT describe tests I didn't actually run.
I will NOT assume my fix works without verification.
I will NOT ignore warnings or regressions.
I will show PROOF or admit I cannot verify.
User frustration with honest "not done" > false "done".
```

---

## 2-Gate Summary

| Gate | Phase | What's Reviewed | Reviewers |
|------|-------|-----------------|-----------|
| GATE 1 | Phase 4 | Plan (spec + architecture) | Codex → Gemini |
| GATE 2 | Phase 8 | Code + CodeSmell + REGRESSION_DELTA | CodeSmell → Codex → Gemini |

---

## Comparison: wf7 vs wf6

| Aspect | wf6 | wf7 |
|--------|-----|-----|
| Gates | 3 | 2 |
| Reviewers per gate | 4 | 2-3 |
| Total reviewer calls | 12 | 4 |
| Test writing | 1 coder | Orchestrator + Codex |
| Test review gate | Yes (4 reviewers) | No (parallel write) |
| CodeSmell | No | Yes |
| Token usage | Baseline | ~75% reduction |

---

## User's Task

$ARGUMENTS
