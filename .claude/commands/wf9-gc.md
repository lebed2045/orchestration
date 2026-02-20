# /wf9-gc - Workflow v9 (Specialized MCP Tools)

**Version 9**: wf8 + specialized MCP tools for better planning and code review.

**Core improvements over wf8**:
1. `mcp__gemini__brainstorm` with design-thinking for architecture planning
2. `mcp__codex-cli__review` with `uncommitted: true` for surgical code review
3. Fixed CodeSmell scope to include all uncommitted files

Based on wf8: Parallel reviews, CodeSmell, autonomous, auto-commit.

---

## ⛔ CRITICAL: NO PRE-EXISTING TEST FAILURES ⛔

**READ THIS BEFORE EVERY PHASE. THERE ARE NEVER PRE-EXISTING TEST FAILURES.**

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ ⛔ ABSOLUTE RULE: NO PRE-EXISTING TEST FAILURES ⛔                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. The baseline has 100% passing tests. ALWAYS.                         │
│ 2. If tests fail, YOU broke them. Not "pre-existing."                   │
│ 3. TDD_RED tests fail BY DESIGN — that's not "pre-existing."            │
│ 4. You MUST fix what YOU broke before claiming completion.              │
│ 5. You CANNOT commit if ANY test fails.                                 │
│ 6. "Pre-existing failure" is NOT a valid excuse. EVER.                  │
│                                                                         │
│ FORBIDDEN PHRASES:                                                      │
│ - "pre-existing test failures"                                          │
│ - "tests were already failing"                                          │
│ - "baseline had failures"                                               │
│ - "inherited test failures"                                             │
│                                                                         │
│ IF YOU CATCH YOURSELF SAYING THESE: STOP. FIX THE TESTS.                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why this rule exists:**
- User's codebase starts with ALL TESTS PASSING
- Any test failure after Phase 1 is YOUR responsibility
- TDD_RED intentionally writes failing tests — but TDD_GREEN MUST make them pass
- Completion = EXIT_CODE=0 with ALL tests passing

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
[WF9.PhaseX] [Baseline: SET|UNSET] [Regression: SAFE|DETECTED|UNKNOWN] [Status: in_progress|blocked|complete]
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

**⛔ REMINDER: Baseline tests MUST be 100% passing. If not, STOP and ask user — do NOT proceed with failing baseline.**

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

### Phase 3: PLANNING (Design-Thinking Brainstorm)

**NEW in wf9**: Use `mcp__gemini__brainstorm` for architecture exploration.

#### Step 1: Brainstorm Architecture Approaches

Call `mcp__gemini__brainstorm`:

| Parameter | Value |
|-----------|-------|
| prompt | "Architecture approaches for: [task summary from spec]" |
| domain | "software" |
| methodology | "design-thinking" |
| constraints | "[from CLAUDE.md and spec.md - e.g., 'no external deps', 'Vanilla CSS']" |
| ideaCount | 3 |
| includeAnalysis | true |

**Extract from brainstorm output:**
- Alternative approaches considered
- Recommended approach with rationale
- High-risk zones needing dedicated tests

#### Step 2: Write Architecture Document

Write to `.claude/temp/architecture.md`:
- **Design Exploration** (from brainstorm - alternatives considered)
- Component design (recommended approach)
- File structure
- Dependencies
- TDD test plan
- Regression checkpoints
- High-risk zones (from brainstorm)
- Smoke test plan

VERIFY: Show `cat .claude/temp/architecture.md | head -40` output

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
3. Design exploration - were alternatives considered?
4. TDD strategy - are tests well-planned?
5. High-risk zones identified for dedicated tests?

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
3. Design exploration quality (were alternatives considered?)
4. TDD strategy adequacy
5. High-risk zones coverage

Output format:
REVIEWER: Gemini
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES_CAUGHT: [numbered list or "none"]
SUGGESTIONS: [numbered list or "none"]
```

**IMPORTANT: Both tools MUST be called in the SAME message. After BOTH return, append outputs to gate file.**

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

1. Feed feedback back into `mcp__gemini__brainstorm` with refined constraints
2. Update spec/architecture
3. Re-run BOTH reviewers

---

### Phase 5: TDD_RED — ISOLATED CODER

**Spawn isolated coder subprocess to write failing tests.**

```bash
claude -p "You are a TDD test writer with ZERO prior context.

Read ONLY:
- .claude/temp/spec.md
- .claude/temp/architecture.md (especially High-Risk Zones section)

Write RED tests:
- At least 1 test per requirement in spec
- EXTRA tests for High-Risk Zones identified in architecture
- Tests MUST FAIL (no implementation exists)
- Tests must be FALSIFIABLE (cannot pass with trivial 'return true')

After writing tests, run them to verify they fail:
\`\`\`bash
npm test 2>&1 | tee /tmp/tdd-red.txt
echo \"EXIT_CODE: \$?\"
\`\`\`

Output EXECUTION_BLOCK showing EXIT_CODE≠0 (tests failing)." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: Coder output shows EXECUTION_BLOCK with EXIT_CODE≠0.

#### Auto-stage tests

```bash
git add tests/  # or test files location
echo "✓ Tests staged after TDD_RED"
```

---

### Phase 6: TDD_GREEN — ISOLATED CODER

**Spawn isolated coder subprocess to implement code.**

```bash
claude -p "You are a TDD implementer with ZERO prior context.

Read:
- .claude/temp/spec.md
- .claude/temp/architecture.md
- Test files
- /tmp/baseline.txt (baseline metrics)

CRITICAL: Test files are READ-ONLY. Only edit src/ files.
CRITICAL: After EVERY change, check REGRESSION_DELTA against baseline.

LOOP (max 5): Fix one error at a time until tests pass.

After tests pass, output:
1. EXECUTION_BLOCK showing EXIT_CODE=0
2. REGRESSION_DELTA comparing to baseline" \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: Coder output shows:
- EXECUTION_BLOCK with EXIT_CODE=0
- REGRESSION_DELTA with VERDICT=SAFE

**SECURITY**: If coder edits test files, reject and re-spawn.

**⛔ REMINDER: ALL tests MUST pass after TDD_GREEN. No exceptions. No "pre-existing failures." YOU wrote these tests in TDD_RED — YOU must make the CODE pass them. Tests are READ-ONLY; fix the IMPLEMENTATION.**

---

### Phase 7: GATE 2/2 - CODE_REVIEW (CodeSmell → Codex Review + Gemini in PARALLEL)

**NEW in wf9**: Use specialized `mcp__codex-cli__review` for surgical diff review.

Initialize gate review file:

```bash
echo "# Gate 2/2: Code Review" > .claude/temp/gate-2-reviews.md
echo "Generated: $(date)" >> .claude/temp/gate-2-reviews.md
echo "" >> .claude/temp/gate-2-reviews.md
echo "## Git State" >> .claude/temp/gate-2-reviews.md
git status --porcelain >> .claude/temp/gate-2-reviews.md
git diff --stat >> .claude/temp/gate-2-reviews.md
```

#### Step 1: CodeSmell Check (runs first, blocking)

**FIXED in wf9**: Check ALL uncommitted files (not just staged) to match Codex review scope.

```bash
# Run on ALL uncommitted files (staged + unstaged + untracked)
for file in $(git status --porcelain | awk '{print $2}'); do
  if [[ -f "$file" && "$file" =~ \.(ts|js|tsx|jsx|py|go|rs)$ ]]; then
    echo "Checking: $file"
    ./Tools/code-smell.sh "$file" --gemini 2>&1 | tee -a /tmp/codesmell.txt
  fi
done
echo ""
echo "=== CodeSmell Results ==="
grep -E "Score:|PASS|FAIL" /tmp/codesmell.txt
```

**If any file scores < 60, refactor and re-check (no user approval needed).**

#### Step 2: Codex Review + Gemini (run in PARALLEL)

**After CodeSmell passes, MUST call BOTH tools in a single message for parallel execution.**

**Tool 1: Codex** - Call `mcp__codex-cli__review` (SPECIALIZED):

| Parameter | Value |
|-----------|-------|
| uncommitted | true |
| workingDirectory | Project root |
| title | "WF9 Gate 2/2 Code Review" |

**NOTE**: `uncommitted: true` cannot take custom `prompt` - Codex handles the review format.

**Tool 2: Gemini** - Call `mcp__gemini__ask-gemini` (structured checklist, since Codex review has no custom prompt):

```text
Working directory: [pwd]

You are the STRUCTURED REVIEWER for Gate 2/2. Codex is doing diff-focused review.
Your job: checklist validation against spec.

Read:
- .claude/temp/spec.md (requirements)
- .claude/temp/architecture.md (design + high-risk zones)
- src/ files (implementation)
- tests/ files

Validate CHECKLIST:
1. SPEC_MATCH: Does implementation satisfy ALL requirements in spec.md?
2. SECURITY: Any OWASP top 10 issues?
3. HIGH_RISK_ZONES: Are zones from architecture.md adequately tested?
4. REGRESSION: Any breaking changes to existing functionality?
5. CODE_QUALITY: Follows project conventions?

Output format:
REVIEWER: Gemini (Structured)
SPEC_MATCH: [YES|NO - list missing requirements if NO]
SECURITY: [OK|ISSUE - list issues]
HIGH_RISK_COVERAGE: [OK|ISSUE - list uncovered zones]
REGRESSION_RISK: [LOW|MEDIUM|HIGH]
CODE_QUALITY: [OK|ISSUE]
VERDICT: [APPROVED|NEEDS_WORK]
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

#### Gate 2/2 Checkpoint

```text
┌─────────────────────────────────────────────┐
│ GATE 2/2 CHECKPOINT (Code Review)           │
├─────────────────────────────────────────────┤
│ CodeSmell:       [PASS (all ≥60) | FAIL]    │
│ Codex (review):  [from uncommitted review]  │
│ Gemini (struct): [APPROVED|NEEDS_WORK]      │
├─────────────────────────────────────────────┤
│ SMOKE_TEST: [PASS|FAIL]                     │
│ REGRESSION_DELTA: [SAFE|REGRESSION]         │
├─────────────────────────────────────────────┤
│ Review file verified: [YES|NO]              │
│ GATE STATUS: [PASS|BLOCKED]                 │
│ Review file: .claude/temp/gate-2-reviews.md │
└─────────────────────────────────────────────┘
```

**All must pass: CodeSmell ≥60 + Codex review clean + Gemini APPROVED + SMOKE_TEST PASS + REGRESSION_DELTA SAFE**

**If ANY check fails (max 3 iterations):**
1. Fix issues (no user approval needed)
2. Re-run failed checks

---

### Phase 8: COMPLETION + AUTO_COMMIT

**⛔ FINAL CHECK BEFORE COMPLETION:**
```text
┌─────────────────────────────────────────────────────────────────────────┐
│ ⛔ PRE-COMMIT VERIFICATION ⛔                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ □ Did you run tests? (not assume, ACTUALLY RUN)                         │
│ □ Did ALL tests pass? (EXIT_CODE=0)                                     │
│ □ Are there ANY failing tests? If YES → STOP, FIX THE CODE              │
│ □ "Pre-existing failures" is NOT valid. EVER.                           │
│                                                                         │
│ If tests fail:                                                          │
│   → FIX THE IMPLEMENTATION (tests are reviewed & correct)               │
│   → Tests are READ-ONLY after TDD_RED                                   │
│   → NEVER claim "pre-existing"                                          │
│   → NEVER modify tests to make them pass                                │
└─────────────────────────────────────────────────────────────────────────┘
```

Only proceed if ALL conditions met:

- [ ] BASELINE_BLOCK captured at start
- [ ] EXECUTION_BLOCK shows EXIT_CODE=0
- [ ] REGRESSION_DELTA shows SAFE
- [ ] SMOKE_TEST shows PASS
- [ ] CodeSmell all files ≥60
- [ ] Codex review clean
- [ ] Gemini APPROVED at both gates
- [ ] Both gate files exist with reviewers

#### Completion Checklist

```text
┌─────────────────────────────────────────────┐
│ COMPLETION CHECKLIST                        │
├─────────────────────────────────────────────┤
│ [x] Baseline captured                       │
│ [x] Design-thinking brainstorm done         │
│ [x] Tests pass (EXECUTION_BLOCK shown)      │
│ [x] No regression (REGRESSION_DELTA=SAFE)   │
│ [x] Warnings stable (before/after same)     │
│ [x] Smoke test pass (SMOKE_TEST shown)      │
│ [x] CodeSmell all ≥60                       │
│ [x] Codex review (uncommitted) clean        │
│ [x] Gemini structured review passed         │
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

- Planning: design-thinking brainstorm (3 alternatives explored)
- Tests: all passing
- CodeSmell: ≥60 on all files
- Reviews: Codex (uncommitted) + Gemini (structured) approved
- Regression: SAFE

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo "✓ Auto-committed"
git log -1 --oneline
```

#### WF9_RESULT Block

```text
┌─────────────────────────────────────────────┐
│ WF9_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: SUCCESS                             │
│ Commit: [SHA]                               │
│ Artifacts: [files created/modified]         │
│ Tests: [N passed, 0 failed]                 │
│ Brainstorm: design-thinking, 3 alternatives │
│ Regression: SAFE                            │
│ Human gates: 0                              │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

Output: `✓ ORCHESTRATION COMPLETE (wf9 - specialized tools)`

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
| Review fails 3x (any gate) | Re-brainstorm with feedback, then escalate |
| SMOKE_TEST FAIL | STOP. Cannot commit |
| Gate file missing | STOP. Re-run gate reviewers |
| **Claim "pre-existing failures"** | **⛔ RETRACT IMMEDIATELY. Fix the CODE.** |
| **Tests fail at completion** | **⛔ CANNOT COMPLETE. Fix the CODE first.** |

---

## Anti-Sycophancy Oath

```text
I will NOT claim "done" to end a frustrating session.
I will NOT describe tests I didn't actually run.
I will NOT assume my fix works without verification.
I will NOT ignore warnings or regressions.
I will show PROOF or admit I cannot verify.
User frustration with honest "not done" > false "done".

⛔ ADDITIONAL OATH FOR WF9:
I will NEVER claim "pre-existing test failures."
I will NEVER blame the baseline for test failures.
I will NEVER commit with failing tests.
If tests fail, I will FIX THE CODE (tests are READ-ONLY).
The baseline is ALWAYS 100% passing.
```

---

## Comparison: wf9 vs wf8

| Aspect | wf8 | wf9 |
|--------|-----|-----|
| Planning | Generic Gemini prompt | `mcp__gemini__brainstorm` (design-thinking) |
| Code Review (Codex) | Generic prompt | `mcp__codex-cli__review --uncommitted` |
| Code Review (Gemini) | Generic prompt | Structured checklist (spec-match, security) |
| CodeSmell scope | Staged only | All uncommitted (matches Codex scope) |
| Gate 1 feedback | Discard | Feed back into brainstorm |
| Architecture doc | Basic | Includes Design Exploration section |
| Alternatives explored | 0 | 3 (from brainstorm) |

---

## When to Use wf9 vs wf8

| Use Case | Best Choice |
|----------|-------------|
| Quick fix, trusted change | wf8 (simpler) |
| Architecture decisions matter | **wf9** (design-thinking) |
| Need surgical diff review | **wf9** (Codex review tool) |
| Multiple valid approaches | **wf9** (explores alternatives) |
| High-risk zones in codebase | **wf9** (identifies + tests them) |

---

## User's Task

$ARGUMENTS
