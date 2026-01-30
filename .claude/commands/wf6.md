# /wf6 - Workflow v6 (Quad Review + Retrospective)

**Version 6**: 4 reviewers per gate (Gemini, Codex, Opus, Sonnet) with retrospective analysis.

**Core principle**: Track which reviewers catch real issues to optimize future workflows.

Uses agents: `coder-v3`, `planner-v3`, `intake-v3`, `fresh-reviewer-v3` (Opus for coder, Quad reviewers at each gate)

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

## FORBIDDEN PHRASES

NEVER output these without preceding PROOF BLOCKS:

- "Done" / "Fixed" / "Complete" / "Finished"
- "Tests pass" / "Should work" / "This fixes it"
- "I verified" / "I tested" / "I confirmed"

**Replace with**: "Running verification now..." [then show actual output]

---

## Git Staging Discipline

| Phase | Action | Git Staging |
|-------|--------|-------------|
| TDD_RED | Write tests | Not staged yet |
| TEST_REVIEW (Gate 2) | Review tests | **Auto-stage tests** after APPROVED |
| TDD_GREEN | Write implementation | Not staged yet |
| CODE_REVIEW (Gate 3) | Review code | **Ask user** before staging |
| Completion | Done | **Never auto-commit** |

---

## State Tracking

Every response MUST start with:

```text
[WF6.PhaseX] [Baseline: SET|UNSET] [Regression: SAFE|DETECTED|UNKNOWN] [Status: in_progress|blocked|complete]
```

---

## Phase Flow (10 Phases, 3 Gates)

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

### Phase 4: QUAD_REVIEW_PLAN (GATE 1)

**ALL FOUR reviewers must approve the plan.**

**IMPORTANT: Exit plan mode FIRST to allow subprocess calls.**

1. Call `ExitPlanMode` tool (temporary - to run reviewers)
2. Initialize gate review file:

```bash
echo "# Gate 1: Plan Review" > .claude/temp/gate-1-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-1-reviews.md
```

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini`:

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

**Append to gate file:**

```bash
echo -e "\n## Gemini\nVERDICT: [X]\nISSUES: [list]" >> .claude/temp/gate-1-reviews.md
```

#### Reviewer 2: Codex

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

**Append to gate file.**

#### Reviewer 3: Opus

```bash
claude -p "You are a software architect with ZERO context.
Read .claude/temp/spec.md and .claude/temp/architecture.md

Review for: requirements completeness, architecture feasibility, TDD strategy, REGRESSION STRATEGY.

Output format:
REVIEWER: Opus
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES_CAUGHT: [numbered list or none]
SUGGESTIONS: [numbered list or none]

Write your review to .claude/temp/gate-1-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit \
  --model opus \
  --print
```

#### Reviewer 4: Sonnet

```bash
claude -p "You are a software architect with ZERO context.
Read .claude/temp/spec.md and .claude/temp/architecture.md

Review for: requirements completeness, architecture feasibility, TDD strategy, REGRESSION STRATEGY.

Output format:
REVIEWER: Sonnet
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES_CAUGHT: [numbered list or none]
SUGGESTIONS: [numbered list or none]

Write your review to .claude/temp/gate-1-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit \
  --model sonnet \
  --print
```

#### Gate 1 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 1 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ Gemini: [APPROVED|NEEDS_WORK]               │
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Opus:   [APPROVED|NEEDS_WORK]               │
│ Sonnet: [APPROVED|NEEDS_WORK]               │
├─────────────────────────────────────────────┤
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-1-reviews.md │
└─────────────────────────────────────────────┘
```

**If ANY reviewer returns NEEDS_WORK (max 3 iterations):**

1. Call `EnterPlanMode` tool
2. Fix issues in spec/architecture
3. Call `ExitPlanMode` tool
4. Re-run ALL FOUR reviewers

---

### Phase 5: USER_GATE_PLAN

Present plan for user approval.

**MUST PRESENT:**

1. Artifact paths: spec.md, architecture.md, gate-1-reviews.md
2. Spec summary: Key requirements (3-5 bullet points)
3. Architecture summary: Components, files to create/modify
4. TDD plan: What tests will be written
5. Regression strategy: How we'll prevent regressions
6. All 4 review verdicts

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
│ REQUIREMENTS:                               │
│ • [requirement 1]                           │
│ • [requirement 2]                           │
├─────────────────────────────────────────────┤
│ FILES TO CREATE/MODIFY:                     │
│ • [file1] - [purpose]                       │
├─────────────────────────────────────────────┤
│ TDD PLAN:                                   │
│ • [test 1]                                  │
├─────────────────────────────────────────────┤
│ QUAD REVIEW VERDICTS:                       │
│ Gemini: [APPROVED|NEEDS_WORK]               │
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Opus:   [APPROVED|NEEDS_WORK]               │
│ Sonnet: [APPROVED|NEEDS_WORK]               │
└─────────────────────────────────────────────┘
```

Output: `--- WAITING FOR PLAN APPROVAL ---`

Wait for user approval.

---

### Phase 6: TDD_RED - ISOLATED CODER

Spawn isolated coder (Opus) to write failing tests.

```bash
claude -p "You are a TDD test writer with ZERO prior context.
Read ONLY: .claude/temp/spec.md and .claude/temp/architecture.md
Write tests that MUST FAIL (no implementation exists).
LOOP until tests fail, then output EXECUTION_BLOCK and exit." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --model opus \
  --print
```

VERIFY: Coder output shows EXECUTION_BLOCK with EXIT_CODE≠0 (tests failing).

---

### Phase 7: QUAD_REVIEW_TESTS (GATE 2)

**ALL FOUR reviewers validate tests BEFORE implementation.**

Initialize gate review file:

```bash
echo "# Gate 2: Test Review" > .claude/temp/gate-2-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-2-reviews.md
```

**Gate 2 validates THREE things:**

1. **COVERAGE** - Tests cover all spec requirements
2. **RED_PHASE** - Tests actually fail (no implementation yet)
3. **FALSIFIABILITY** - Tests cannot pass with trivial implementation (e.g., `return true`)

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini`:

```text
Working directory: [pwd]

Review the test files for quality and falsifiability.

Read: .claude/temp/spec.md and test files

Validate:
1. COVERAGE: Tests cover ALL requirements in spec
2. RED_PHASE: Tests are currently FAILING
3. FALSIFIABILITY: Tests CANNOT pass with trivial implementation

FALSIFIABILITY examples:
- BAD: expect(login()).toBeTruthy() - passes with 'return true'
- GOOD: expect(login('user','pass')).toEqual({token: expect.any(String), userId: 'user'})

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
COVERAGE_CHECK: [YES|NO]
RED_PHASE_CHECK: [YES|NO]
FALSIFIABILITY_CHECK: [YES|NO]
ISSUES_CAUGHT: [numbered list or "none"]
```

**Append to gate file.**

#### Reviewer 2: Codex

Call `mcp__codex-cli__codex`:

| Parameter | Value |
|-----------|-------|
| prompt | See below |
| workingDirectory | Project root |

```text
Review the test files for a software task.

Read the test files and .claude/temp/spec.md

Validate:
1. COVERAGE: Tests cover ALL requirements in spec
2. RED_PHASE: Tests are currently FAILING
3. FALSIFIABILITY: Tests CANNOT pass with trivial implementation like 'return true'

Output format:
REVIEWER: Codex
VERDICT: [APPROVED|NEEDS_WORK]
COVERAGE_CHECK: [YES|NO]
RED_PHASE_CHECK: [YES|NO]
FALSIFIABILITY_CHECK: [YES|NO]
ISSUES_CAUGHT: [numbered list or "none"]
```

**Append to gate file.**

#### Reviewer 3: Opus

```bash
claude -p "You are a test quality reviewer with ZERO context.
Read .claude/temp/spec.md and test files.

Validate:
1. COVERAGE: Tests cover ALL requirements in spec
2. RED_PHASE: Tests are currently FAILING (no implementation)
3. FALSIFIABILITY: Tests CANNOT pass with trivial implementation like 'return true'

Output format:
REVIEWER: Opus
VERDICT: [APPROVED|NEEDS_WORK]
COVERAGE_CHECK: [YES|NO]
RED_PHASE_CHECK: [YES|NO]
FALSIFIABILITY_CHECK: [YES|NO]
ISSUES_CAUGHT: [numbered list or none]

Write your review to .claude/temp/gate-2-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit,Bash \
  --model opus \
  --print
```

#### Reviewer 4: Sonnet

```bash
claude -p "You are a test quality reviewer with ZERO context.
Read .claude/temp/spec.md and test files.

Validate:
1. COVERAGE: Tests cover ALL requirements in spec
2. RED_PHASE: Tests are currently FAILING (no implementation)
3. FALSIFIABILITY: Tests CANNOT pass with trivial implementation like 'return true'

Output format:
REVIEWER: Sonnet
VERDICT: [APPROVED|NEEDS_WORK]
COVERAGE_CHECK: [YES|NO]
RED_PHASE_CHECK: [YES|NO]
FALSIFIABILITY_CHECK: [YES|NO]
ISSUES_CAUGHT: [numbered list or none]

Write your review to .claude/temp/gate-2-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit,Bash \
  --model sonnet \
  --print
```

#### Gate 2 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 2 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ Gemini: [APPROVED|NEEDS_WORK]               │
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Opus:   [APPROVED|NEEDS_WORK]               │
│ Sonnet: [APPROVED|NEEDS_WORK]               │
├─────────────────────────────────────────────┤
│ COVERAGE:      [4/4 YES]                    │
│ RED_PHASE:     [4/4 YES]                    │
│ FALSIFIABILITY:[4/4 YES]                    │
├─────────────────────────────────────────────┤
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-2-reviews.md │
└─────────────────────────────────────────────┘
```

**After Gate 2 APPROVED:**

```bash
git add tests/  # Auto-stage test files
echo "✓ Tests staged after Gate 2 approval"
```

---

### Phase 8: TDD_GREEN - ISOLATED CODER

Spawn isolated coder (Opus) to implement.

```bash
claude -p "You are a TDD implementer with ZERO prior context.
Read: .claude/temp/spec.md, .claude/temp/architecture.md, tests/, /tmp/baseline.txt
CRITICAL: Test files are READ-ONLY. Only edit src/ files.
CRITICAL: After EVERY change, run REGRESSION_DELTA check against baseline.
LOOP (max 5): Fix one error at a time until tests pass.
Output EXECUTION_BLOCK + REGRESSION_DELTA when done." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --model opus \
  --print
```

VERIFY: Coder output shows:
- EXECUTION_BLOCK with EXIT_CODE=0
- REGRESSION_DELTA with VERDICT=SAFE

**SECURITY**: If coder edits test files, reject and re-spawn.

---

### Phase 9: QUAD_REVIEW_CODE (GATE 3)

**ALL FOUR reviewers validate implementation.**

Initialize gate review file:

```bash
echo "# Gate 3: Code Review" > .claude/temp/gate-3-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-3-reviews.md
```

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini`:

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

**Append to gate file.**

#### Reviewer 2: Codex

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

Output format:
REVIEWER: Codex
VERDICT: [APPROVED|NEEDS_WORK]
SPEC_MATCH: [YES|NO]
CODE_QUALITY: [assessment]
ISSUES_CAUGHT: [numbered list or "none"]
```

**Append to gate file.**

#### Reviewer 3: Opus

```bash
claude -p "You are a code reviewer with ZERO context.
Read src/ and tests/. Find problems.
Run: npm test 2>&1 | tee /tmp/final.txt; echo EXIT_CODE: \$?
Compare warnings to baseline: grep -ci warn /tmp/final.txt vs /tmp/baseline.txt

Output format:
REVIEWER: Opus
VERDICT: [APPROVED|NEEDS_WORK]
EXIT_CODE: [N]
REGRESSION_DELTA: [comparison to baseline]
ISSUES_CAUGHT: [numbered list or none]

Write your review to .claude/temp/gate-3-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit,Bash \
  --model opus \
  --print
```

#### Reviewer 4: Sonnet

```bash
claude -p "You are a code reviewer with ZERO context.
Read src/ and tests/. Find problems.

Output format:
REVIEWER: Sonnet
VERDICT: [APPROVED|NEEDS_WORK]
CODE_QUALITY: [assessment]
SECURITY_ISSUES: [list or none]
ISSUES_CAUGHT: [numbered list or none]

Write your review to .claude/temp/gate-3-reviews.md (append)" \
  --allowedTools Read,Glob,Grep,Write,Edit,Bash \
  --model sonnet \
  --print
```

#### SMOKE_TEST

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

#### Gate 3 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 3 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ Gemini: [APPROVED|NEEDS_WORK]               │
│ Codex:  [APPROVED|NEEDS_WORK]               │
│ Opus:   [APPROVED|NEEDS_WORK]               │
│ Sonnet: [APPROVED|NEEDS_WORK]               │
├─────────────────────────────────────────────┤
│ SMOKE_TEST: [PASS|FAIL]                     │
│ REGRESSION_DELTA: [SAFE|REGRESSION]         │
├─────────────────────────────────────────────┤
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-3-reviews.md │
└─────────────────────────────────────────────┘
```

VERIFY: All 4 APPROVED + REGRESSION_DELTA=SAFE + SMOKE_TEST=PASS.

---

### Phase 10: COMPLETION + RETROSPECTIVE

Only output completion if ALL conditions met:

- [ ] BASELINE_BLOCK captured at start
- [ ] EXECUTION_BLOCK shows EXIT_CODE=0
- [ ] REGRESSION_DELTA shows SAFE
- [ ] SMOKE_TEST shows PASS
- [ ] All 4 reviewers APPROVED at all 3 gates

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
│ [x] All reviews passed (3 gates × 4 each)   │
│ VERDICT: COMPLETE                           │
└─────────────────────────────────────────────┘
```

#### REVIEWER_RETROSPECTIVE (REQUIRED)

Parse all gate review files and generate:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ REVIEWER_RETROSPECTIVE                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ GATE 1 (Plan Review):                                                   │
│   Gemini: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Codex:  VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Opus:   VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Sonnet: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│                                                                         │
│ GATE 2 (Test Review):                                                   │
│   Gemini: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Codex:  VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Opus:   VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Sonnet: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│                                                                         │
│ GATE 3 (Code Review):                                                   │
│   Gemini: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Codex:  VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Opus:   VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
│   Sonnet: VERDICT=[X] ISSUES_CAUGHT=[N] UNIQUE=[Y/N] USEFUL=[Y/N]       │
├─────────────────────────────────────────────────────────────────────────┤
│ SUMMARY:                                                                │
│   Total issues caught: [N]                                              │
│   By reviewer: Gemini=[N], Codex=[N], Opus=[N], Sonnet=[N]              │
│   Unique issues (caught by only 1 reviewer):                            │
│     - Gemini: [list or "none"]                                          │
│     - Codex: [list or "none"]                                           │
│     - Opus: [list or "none"]                                            │
│     - Sonnet: [list or "none"]                                          │
│   Redundant reviewers (only repeated others): [list]                    │
├─────────────────────────────────────────────────────────────────────────┤
│ RECOMMENDATION:                                                         │
│   Gate 1: Keep [X], consider removing [Y]                               │
│   Gate 2: Keep [X], consider removing [Y]                               │
│   Gate 3: Keep [X], consider removing [Y]                               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Usefulness criteria:**

| USEFUL=YES | USEFUL=NO |
|------------|-----------|
| Caught a real bug not found by others | Only said "APPROVED" with no feedback |
| Required specific code fix | Repeated exact issue another reviewer found |
| Identified security/logic issue | Generic "looks good" feedback |
| Found edge case in tests | Only stylistic/cosmetic feedback |

#### WF6_RESULT Block

```text
┌─────────────────────────────────────────────┐
│ WF6_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: SUCCESS                             │
│ Artifacts: [files created/modified]         │
│ Tests: [N passed, 0 failed]                 │
│ Regression: SAFE                            │
│ Review stats:                               │
│   Total reviewers invoked: 12               │
│   Useful reviews: [N]                       │
│   Redundant reviews: [N]                    │
│ Reflection: [what worked, what was learned] │
│ Blocker: none                               │
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
| Same error 2x | STOP. Escalate to user |
| Tests fail 5x | STOP. "MANUAL INTERVENTION REQUIRED" |
| Review fails 3x (any gate) | STOP. "REVIEW LOOP EXCEEDED" |
| SMOKE_TEST FAIL | STOP. Cannot claim done |

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

**Then output WF6_RESULT block (required for DDR parsing):**

```text
┌─────────────────────────────────────────────┐
│ WF6_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: FAILURE                             │
│ Artifacts: [files created/modified so far]  │
│ Tests: [N passed, M failed]                 │
│ Regression: [SAFE|DETECTED]                 │
│ Review stats:                               │
│   Reviewers invoked before failure: [N]     │
│   Gate reached: [1|2|3]                     │
│ Reflection: [what was attempted, why stuck] │
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

## 3-Gate Summary

| Gate | Phase | What's Reviewed | Reviewers |
|------|-------|-----------------|-----------|
| GATE 1 | Phase 4 | Plan (spec + architecture + regression strategy) | Gemini + Codex + Opus + Sonnet |
| GATE 2 | Phase 7 | Tests (coverage, RED phase, falsifiability) | Gemini + Codex + Opus + Sonnet |
| GATE 3 | Phase 9 | Code + REGRESSION_DELTA + SMOKE_TEST | Gemini + Codex + Opus + Sonnet |

---

## User's Task

$ARGUMENTS
