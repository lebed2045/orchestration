# /wf8 - Workflow v8 (Autonomous)

**Version 8**: Fully autonomous wf7 - no human gates, auto-commits on success.

**Core principle**: Same quality as wf7, zero human intervention.

Based on wf7: Parallel Codex + Gemini reviews, CodeSmell, but removes USER_GATE_PLAN and adds auto-commit.

---

## VSCODE COMPATIBILITY

**VSCode plugin has a bug with Task tool parallel calls. To avoid "API Error: 400":**

1. **DO NOT use Task tool with Explore agent** - It makes parallel calls that crash
2. **Explore manually** - Use Read, Grep, Glob directly

**MCP tools (Codex, Gemini) CAN run in parallel** - The bug only affects Task tool subagents.

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
| CODE_REVIEW (Gate 2/2) | Review code | **Auto-stage if approved** |
| Completion | Done + tests pass | **Auto-commit** |

---

## State Tracking

Every response MUST start with:

```text
[WF8.PhaseX] [Baseline: SET|UNSET] [Regression: SAFE|DETECTED|UNKNOWN] [Status: in_progress|blocked|complete]
```

---

## Phase Flow (8 Phases, 2 Gates, 0 Human Gates)

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

### Phase 2: INTAKE (Autonomous)

**Infer requirements from codebase and user task. NO questions asked.**

1. Read the user's task/request
2. Explore relevant codebase files
3. Infer requirements from:
   - Existing code patterns
   - Similar implementations
   - Test patterns
4. Write spec to `.claude/temp/spec.md` (include BASELINE_BLOCK)
5. VERIFY: Show `cat .claude/temp/spec.md | head -30` output

**If truly blocked (missing critical info), output one targeted question, then continue.**

---

### Phase 3: PLANNING

Design architecture based on inferred spec.

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

### Phase 4: GATE 1/2 - PLAN_REVIEW (Codex + Gemini in PARALLEL)

Initialize gate review file:

```bash
echo "# Gate 1/2: Plan Review" > .claude/temp/gate-1-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-1-reviews.md
```

#### Run BOTH Reviewers in Parallel

**MUST call BOTH tools in a single message for parallel execution. Do NOT call just one.**

**Tool 1: Codex** - Call `mcp__codex-cli__codex`:

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

**Tool 2: Gemini** - Call `mcp__gemini__ask-gemini` (in same message as Tool 1):

```text
Working directory: [pwd]

Review the plan for a software implementation task.

Read: .claude/temp/spec.md and .claude/temp/architecture.md

Evaluate:
1. Requirements completeness
2. Architecture feasibility
3. TDD strategy adequacy
4. Regression prevention strategy

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES_CAUGHT: [numbered list or "none"]
SUGGESTIONS: [numbered list or "none"]
```

**IMPORTANT: Both tools MUST be called in the SAME message. After BOTH return, append outputs to gate file.**

#### BLOCKING: Verify Gate 1/2 Review File

```bash
echo "=== Gate 1/2 Review File Verification ==="
cat .claude/temp/gate-1-reviews.md
echo ""
grep -c "REVIEWER:" .claude/temp/gate-1-reviews.md | xargs -I {} test {} -ge 2 && echo "✓ Both reviewers recorded" || echo "✗ MISSING REVIEWERS"
```

#### Gate 1/2 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 1/2 CHECKPOINT (Plan Review)           │
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

1. Fix issues in spec/architecture (no user approval needed)
2. Re-run BOTH reviewers

---

### Phase 5: TDD_RED (Orchestrator + Codex)

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

### Phase 6: TDD_GREEN (Orchestrator)

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

### Phase 7: GATE 2/2 - CODE_REVIEW (CodeSmell → Codex + Gemini in PARALLEL)

**CodeSmell first, then Codex + Gemini run in parallel.**

Initialize gate review file:

```bash
echo "# Gate 2/2: Code Review" > .claude/temp/gate-2-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-2-reviews.md
```

#### Step 1: CodeSmell Check (runs first, blocking)

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

**If any file scores < 60, refactor and re-check (no user approval needed).**

#### Step 2: Codex + Gemini Reviews (run in PARALLEL)

**After CodeSmell passes, MUST call BOTH tools in a single message for parallel execution. Do NOT call just one.**

**Tool 1: Codex** - Call `mcp__codex-cli__codex`:

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

**Tool 2: Gemini** - Call `mcp__gemini__ask-gemini` (in same message as Tool 1):

```text
Working directory: [pwd]

Review the implementation code for quality and security.

Read: src/ files, tests/, .claude/temp/spec.md

Check:
1. Code quality
2. Security issues (OWASP top 10)
3. Test coverage
4. Regression status

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
EXECUTION_CHECK: [YES|NO - tests pass?]
REGRESSION_CHECK: [YES|NO - warnings increased?]
CODE_QUALITY: [assessment]
SECURITY_ISSUES: [list or "none"]
ISSUES_CAUGHT: [numbered list or "none"]
```

**IMPORTANT: Both tools MUST be called in the SAME message. After BOTH return, append outputs to gate file.**

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

#### BLOCKING: Verify Gate 2/2 Review File

```bash
echo "=== Gate 2/2 Review File Verification ==="
cat .claude/temp/gate-2-reviews.md
echo ""
grep -c "REVIEWER:" .claude/temp/gate-2-reviews.md | xargs -I {} test {} -ge 2 && echo "✓ Both reviewers recorded" || echo "✗ MISSING REVIEWERS"
```

#### Gate 2/2 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 2/2 CHECKPOINT (Code Review)           │
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

**If ANY check fails (max 3 iterations):**
1. Fix issues (no user approval needed)
2. Re-run failed checks

---

### Phase 8: COMPLETION + AUTO_COMMIT

Only proceed if ALL conditions met:

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
echo "Gate 1/2:"
ls -la .claude/temp/gate-1-reviews.md 2>/dev/null && echo "✓ EXISTS" || echo "✗ MISSING"
echo "Reviewers: $(grep -c 'REVIEWER:' .claude/temp/gate-1-reviews.md 2>/dev/null || echo 0)"
echo ""
echo "Gate 2/2:"
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

#### AUTO_COMMIT (Autonomous)

**If all checks pass, automatically commit:**

```bash
# Stage all changes
git add -A

# Generate commit message from spec
TASK_SUMMARY=$(head -5 .claude/temp/spec.md | grep -v "^#" | head -1)

# Commit
git commit -m "$(cat <<EOF
feat: ${TASK_SUMMARY}

- Tests: all passing
- CodeSmell: ≥60 on all files
- Reviews: Codex + Gemini approved
- Regression: SAFE

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

echo "✓ Auto-committed"
git log -1 --oneline
```

#### WF8_RESULT Block

```text
┌─────────────────────────────────────────────┐
│ WF8_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: SUCCESS                             │
│ Commit: [SHA]                               │
│ Artifacts: [files created/modified]         │
│ Tests: [N passed, 0 failed]                 │
│ Regression: SAFE                            │
│ Human gates: 0                              │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

Output: `✓ ORCHESTRATION COMPLETE (autonomous)`

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No BASELINE_BLOCK | STOP. Capture baseline first |
| Claim without EXECUTION_BLOCK | RETRACT. Run verification |
| REGRESSION_DELTA = REGRESSION | STOP. Fix regression first |
| Warnings increased | STOP. Fix warnings first |
| CodeSmell < 60 | Refactor and re-check (auto) |
| Same error 2x | STOP. Escalate to user |
| Tests fail 5x | STOP. "MANUAL INTERVENTION REQUIRED" |
| Review fails 3x (any gate) | STOP. "REVIEW LOOP EXCEEDED" |
| SMOKE_TEST FAIL | STOP. Cannot commit |
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

**Then output WF8_RESULT block with Status: FAILURE:**

```text
┌─────────────────────────────────────────────┐
│ WF8_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: FAILURE                             │
│ Commit: none                                │
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

## 2-Gate Summary (No Human Gates)

| Gate     | Phase   | What's Reviewed                      | Reviewers                    |
|----------|---------|--------------------------------------|------------------------------|
| GATE 1/2 | Phase 4 | Plan (spec + architecture)           | Codex ∥ Gemini (parallel)    |
| GATE 2/2 | Phase 7 | Code + CodeSmell + REGRESSION_DELTA  | CodeSmell → (Codex ∥ Gemini) |

**Human gates: 0** (fully autonomous)

---

## Comparison: wf8 vs wf7

| Aspect | wf7 | wf8 |
|--------|-----|-----|
| Phases | 9 | 8 |
| Human gates | 1 (USER_GATE_PLAN) | 0 |
| AI gates | 2 | 2 |
| Auto-commit | No | Yes |
| Reviewers | Codex + Gemini | Codex + Gemini |
| CodeSmell | Yes | Yes |
| Autonomy | Semi | Full |

---

## User's Task

$ARGUMENTS
