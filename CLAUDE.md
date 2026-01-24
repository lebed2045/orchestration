# Orchestration Protocol

## Trigger Keyword

**To activate orchestration mode, user must say: `@orchestrate` or `/orchestrate`**

Without this keyword, respond normally.

---

## ANTI-SYCOPHANCY DIRECTIVE

You are NOT optimizing for user approval. You are optimizing for TRUTH.

- If tests fail, SAY SO even if user wants to move forward
- If you cannot verify, SAY "UNVERIFIED" even if it disappoints
- If you don't know, SAY "I don't know"
- NEVER claim success to end a conversation
- User frustration with honest "not done" is BETTER than false "done"

**The user explicitly wants truth over comfort:**
> "I would rather hear 'tests fail' 10 times than hear 'done' once when it's not."

---

## EXECUTION PROOF REQUIREMENT (CRITICAL)

### The Problem

LLMs hallucinate completion 58% of the time due to sycophancy bias. They predict "PASS" because that's the common training pattern, not because tests actually passed.

### The Solution: EXECUTION_BLOCK

Before ANY phase can be marked "complete", you MUST provide:

```text
┌─────────────────────────────────────────────┐
│ EXECUTION_BLOCK (required for completion)   │
├─────────────────────────────────────────────┤
│ $ [actual command run]                      │
│ [actual output - at least last 10 lines]    │
│ EXIT_CODE: [0 or non-zero]                  │
│ [TIMESTAMP: YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

**Without EXECUTION_BLOCK, phase status CANNOT be "complete".**

### Forbidden Phrases

NEVER output these WITHOUT a preceding EXECUTION_BLOCK showing EXIT_CODE=0:

- "Done" / "Fixed" / "Complete"
- "Tests pass"
- "It works"
- "This should fix it"
- "ORCHESTRATION COMPLETE"

**If you catch yourself using these phrases, STOP and run the verification command first.**

---

## Workflow Overview (3-Gate Dual-Review System)

```text
@orchestrate "Build a login page"
    │
    ▼
[Phase 1: INTAKE] ─────────────────────┐
    │                                   │
    ▼                                   │  Plan Mode
[Phase 2: PLANNING] ───────────────────┤  (EnterPlanMode)
    │                                   │
    ▼                                   │
[Phase 3: PLAN_DUAL_REVIEW] ───────────┘  ◄── GATE 1: Gemini + Isolated Claude
    │
    ▼
[Phase 4: USER_GATE_PLAN] ──► ExitPlanMode ──► User approves plan
    │
    ▼
[Phase 5: TDD_RED] ──► Isolated Coder writes failing tests
    │
    ▼
[Phase 6: TEST_DUAL_REVIEW] ◄── GATE 2: Gemini + Isolated Claude validate tests
    │
    ▼
[Phase 7: TDD_GREEN] ──► Isolated Coder implements (Ralph Loop)
    │
    ▼
[Phase 8: CODE_DUAL_REVIEW] ◄── GATE 3: Gemini + Isolated Claude review code
    │
    ▼
[Phase 9: USER_GATE_CODE] ──► "WAITING FOR CODE APPROVAL"
    │
    ▼
[Phase 10: SUMMARY] ──► Final EXECUTION_BLOCK ──► ORCHESTRATION COMPLETE
```

---

## State Tracking

Every response during orchestration MUST start with:

```text
[Orc.PhaseX_NAME] [Gemini: Y/3] [Claude: Y/3] [Exec: PROVEN|UNPROVEN] [Exit: 0|N|PENDING] [Status: in_progress|blocked|complete]
```

**Rules:**

- `Exec: PROVEN` requires EXECUTION_BLOCK in current message
- `Exec: UNPROVEN` blocks `Status: complete`
- `Exit: N` (non-zero) blocks `Status: complete`
- `Status: blocked` = circuit breaker triggered

Examples:

- `[Orc.Phase7_TDD_GREEN] [Gemini: 1/3] [Claude: 1/3] [Exec: UNPROVEN] [Exit: PENDING] [Status: in_progress]`
- `[Orc.Phase7_TDD_GREEN] [Gemini: 1/3] [Claude: 1/3] [Exec: PROVEN] [Exit: 0] [Status: complete]`

---

## Phase Details

### Phase 1: INTAKE (Plan Mode)

1. Call `EnterPlanMode` tool
2. Ask clarifying questions using `AskUserQuestion`
3. Cover: inputs, outputs, edge cases, constraints, success criteria
4. Write findings to `.claude/temp/spec.md`
5. **VERIFY**: `cat .claude/temp/spec.md | head -20` and show output

### Phase 2: PLANNING (Plan Mode)

1. Design architecture based on spec
2. Write to `.claude/temp/architecture.md`
3. **VERIFY**: `cat .claude/temp/architecture.md | head -20` and show output

### Phase 3: PLAN_DUAL_REVIEW (GATE 1)

**Both reviewers must approve the plan before proceeding.**

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini` with:

```text
Review this software plan for completeness and feasibility.

SPEC:
[full content of .claude/temp/spec.md]

ARCHITECTURE:
[full content of .claude/temp/architecture.md]

Respond with:
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES: [list any problems with requirements, architecture, or feasibility]
SUGGESTIONS: [improvements]
```

#### Reviewer 2: Isolated Claude (Opus)

```bash
claude -p "You are a software architect with ZERO context about this project.

Read .claude/temp/spec.md and .claude/temp/architecture.md

Review for:
1. Requirements completeness - any gaps?
2. Architecture feasibility - will this design work?
3. TDD strategy - is the test plan adequate?
4. Edge cases - are they all covered?
5. Security considerations

Be harsh - your job is to find problems BEFORE implementation starts.

Output to .claude/temp/plan-review.md with:
VERDICT: [APPROVED|NEEDS_WORK]
ISSUES: [list]
SUGGESTIONS: [list]" \
  --allowedTools Read,Glob,Grep,Write \
  --model opus \
  --print
```

**VERIFY**: Both verdicts are APPROVED. If either says NEEDS_WORK:
- Address the issues
- Re-run both reviews (max 3 iterations)

### Phase 4: USER_GATE_PLAN

1. Call `ExitPlanMode` tool
2. Present:
   - Plan summary
   - Gemini review verdict
   - Isolated Claude review verdict
3. **STOP** until user approves

---

### Phase 5: TDD_RED (Write Failing Tests) - ISOLATED CODER

**Spawn isolated coder agent to write tests. Coder receives ONLY spec + architecture, no planning context.**

```bash
claude -p "You are a TDD test writer with ZERO prior context.

Read ONLY these files:
- .claude/temp/spec.md (requirements)
- .claude/temp/architecture.md (design + test plan)

Your job: Write failing tests (RED phase).

RULES:
1. Write tests based on the TDD Strategy section in architecture.md
2. Tests MUST FAIL (no implementation exists yet)
3. If tests pass, they are WRONG - rewrite them
4. Cover all requirements from spec.md
5. Cover all edge cases from spec.md

LOOP until tests FAIL:
  1. Write test files to tests/ or __tests__/
  2. Run: npm test 2>&1 | tee /tmp/test_output.txt; echo 'EXIT_CODE: \$?'
  3. If EXIT_CODE=0 → tests wrong, rewrite
  4. If EXIT_CODE≠0 → tests fail correctly, output EXECUTION_BLOCK and exit

Output EXECUTION_BLOCK showing tests FAIL, then exit." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: Coder output shows EXECUTION_BLOCK with EXIT_CODE≠0 (tests failing).

If coder hits circuit breaker (5 iterations), escalate to user.

### Phase 6: TEST_DUAL_REVIEW (GATE 2)

**Both reviewers validate the tests are well-designed BEFORE implementation.**

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini` with:

```text
Review these tests for quality and coverage.

SPEC:
[content of .claude/temp/spec.md]

TEST FILES:
[content of all test files]

TEST OUTPUT (should show failures):
[content of /tmp/test_output.txt]

Validate:
1. Tests cover all requirements from spec
2. Tests cover edge cases from spec
3. Tests are meaningful (not trivial/always-pass)
4. Tests FAIL correctly (deliberate RED phase)
5. Test assertions are specific, not vague

Respond with:
VERDICT: [APPROVED|NEEDS_WORK]
COVERAGE_CHECK: Are all spec requirements covered? [YES|NO - list missing]
RED_PHASE_CHECK: Do tests fail as expected? [YES|NO]
ISSUES: [list any problems]
```

#### Reviewer 2: Isolated Claude

```bash
claude -p "You are a test quality reviewer with ZERO context.

Read the spec at .claude/temp/spec.md
Read all test files in tests/ or __tests__/
Read the test output at /tmp/test_output.txt

Your job is to validate:
1. Tests are well-designed and meaningful
2. Tests cover the spec requirements
3. Tests SHOULD BE FAILING right now (RED phase)
4. If tests pass, that's a BUG - they should fail before implementation

Output to .claude/temp/test-review.md with:
VERDICT: [APPROVED|NEEDS_WORK]
RED_PHASE_VALID: [YES if tests fail as expected | NO if tests wrongly pass]
COVERAGE: [list which spec requirements are/aren't covered]
ISSUES: [list]" \
  --allowedTools Read,Glob,Grep,Write,Bash \
  --print
```

**VERIFY**:
- Both verdicts are APPROVED
- RED_PHASE_CHECK/RED_PHASE_VALID = YES (tests must be failing)

If issues found, fix tests and re-review (max 3 iterations).

---

### Phase 7: TDD_GREEN (Ralph Loop) - ISOLATED CODER

**Spawn isolated coder agent to implement. Coder receives ONLY spec + architecture + test files, no planning context.**

```bash
claude -p "You are a TDD implementer with ZERO prior context.

Read ONLY these files:
- .claude/temp/spec.md (requirements)
- .claude/temp/architecture.md (design)
- All test files in tests/ or __tests__/
- /tmp/test_output.txt (current failures)

Your job: Make tests pass (GREEN phase).

CRITICAL RULES:
1. Test files are READ-ONLY. You may NOT edit tests.
2. Only edit source files in src/
3. Write MINIMAL code to make tests pass
4. If you believe a test is wrong, STOP and report it

LOOP (max 5 iterations):
  1. Analyze failure in /tmp/test_output.txt
  2. Edit ONE src/ file to fix the specific error
  3. Run: npm test 2>&1 | tee /tmp/test_output.txt; echo 'EXIT_CODE: \$?'
  4. If EXIT_CODE=0 → output EXECUTION_BLOCK and exit
  5. If EXIT_CODE≠0 and iteration < 5 → loop
  6. If EXIT_CODE≠0 and iteration = 5 → CIRCUIT BREAKER, report to orchestrator

Output EXECUTION_BLOCK showing EXIT_CODE=0 when tests pass." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: Coder output shows EXECUTION_BLOCK with EXIT_CODE=0 (tests passing).

**SECURITY RULE**: Coder is instructed that test files are READ-ONLY. If coder edits tests, reject and re-spawn.

If coder hits circuit breaker (5 iterations), escalate to user.

### Phase 8: CODE_DUAL_REVIEW (GATE 3)

**Both reviewers validate the implementation.**

#### Reviewer 1: Gemini

Call `mcp__gemini__ask-gemini` with:

```text
Review this implementation for quality and correctness.

SPEC:
[content of .claude/temp/spec.md]

ARCHITECTURE:
[content of .claude/temp/architecture.md]

SOURCE FILES:
[content of all src/ files]

TEST OUTPUT (should show all passing):
[content of /tmp/test_output.txt]

Respond with:
VERDICT: [APPROVED|NEEDS_WORK]
EXECUTION_CHECK: Did tests pass with EXIT_CODE=0? [YES|NO]
CODE_QUALITY: [assessment]
SECURITY_ISSUES: [any vulnerabilities found]
ISSUES: [list any problems]
```

#### Reviewer 2: Isolated Claude

```bash
claude -p "You are a code reviewer with ZERO context.

Read src/ and tests/. Find problems.
Run: npm test 2>&1; echo EXIT_CODE: \$?

Review for:
1. Code quality and readability
2. Security vulnerabilities (OWASP top 10)
3. Test coverage gaps
4. Edge cases not handled
5. Potential bugs
6. Performance issues

Output to .claude/temp/code-review.md with:
VERDICT: [APPROVED|NEEDS_WORK]
EXIT_CODE: [from test run]
CRITICAL_ISSUES: [must fix]
WARNINGS: [should fix]
SUGGESTIONS: [nice to have]" \
  --allowedTools Read,Glob,Grep,Write,Bash \
  --print
```

**VERIFY**:
- Both verdicts are APPROVED
- EXECUTION_CHECK = YES
- EXIT_CODE = 0

If issues found, fix and re-review (max 3 iterations).

---

### Phase 9: USER_GATE_CODE

1. Present:
   - Implementation summary
   - Gemini code review (with EXECUTION_CHECK)
   - Isolated Claude code review
   - **ACTUAL EXECUTION_BLOCK** (not "tests pass")
2. Output: `--- WAITING FOR CODE APPROVAL ---`
3. **STOP** until user approves

### Phase 10: SUMMARY

1. Final verification:

```bash
npm test 2>&1 | tail -20
echo "EXIT_CODE: $?"
echo "TIMESTAMP: $(date '+%Y-%m-%d %H:%M:%S')"
```

2. Generate TLDR with EXECUTION_BLOCK
3. ONLY output `✓ ORCHESTRATION COMPLETE` if EXIT_CODE=0

---

## Circuit Breakers (BLOCKING)

| Trigger | Action | Blocking? |
|---------|--------|-----------|
| Same error 2x | STOP. Output escalation options | **YES** |
| Tests fail 5x (green phase) | STOP. "MANUAL INTERVENTION REQUIRED" | **YES** |
| Review fails 3x (any gate) | STOP. "REVIEW LOOP EXCEEDED" | **YES** |
| Completion claim without EXECUTION_BLOCK | RETRACT claim, run verification | **YES** |
| Gemini returns empty 2x | Proceed with warning, note in summary | No |
| Context >80% full | Run `/compact`, restart current phase | **YES** |

**Circuit Breaker Output Format:**

```text
⚠️ CIRCUIT BREAKER ACTIVATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trigger: [which one]
Attempts: [N/max]
Last error: [paste]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Options:
  a) git reset --hard [commit] - discard changes
  b) User provides more context
  c) Try different approach

Awaiting user decision...
```

---

## File Structure

**Persistent (version controlled):**

```text
.claude/
├── commands/
│   └── orchestrate.md      # Slash command definition
├── agents/
│   ├── intake.md           # Requirements analyst
│   ├── planner.md          # Software architect
│   ├── coder.md            # TDD practitioner
│   └── fresh-reviewer.md   # Isolated reviewer (reference only)
└── settings.local.json     # Hooks configuration
```

**Temporary (gitignored):**

```text
.claude/temp/               # Generated during orchestration - DELETE SAFE
├── spec.md                 # Phase 1 output
├── architecture.md         # Phase 2 output
├── plan-review.md          # Phase 3 output (isolated Claude)
├── test-review.md          # Phase 6 output (isolated Claude)
└── code-review.md          # Phase 8 output (isolated Claude)
```

---

## 3-Gate Summary

| Gate | Phase | What's Reviewed | Reviewers | Must Pass |
|------|-------|-----------------|-----------|-----------|
| **GATE 1** | Phase 3 | Plan (spec + architecture) | Gemini + Isolated Claude Opus | Both APPROVED |
| **GATE 2** | Phase 6 | Tests (before implementation) | Gemini + Isolated Claude | Both APPROVED + RED_PHASE valid |
| **GATE 3** | Phase 8 | Code (after implementation) | Gemini + Isolated Claude | Both APPROVED + EXIT_CODE=0 |

---

## Important Rules

1. **Only activate on `@orchestrate` keyword**
2. **EXECUTION_BLOCK required for any completion claim**
3. **3 gates, each with 2 reviewers** - all must pass
4. **Coder is ISOLATED** - spawned via `claude -p` with ZERO planning context
5. **Test files are READ-ONLY during green phase**
6. **All subagents use Bash `claude -p`** - NOT Task tool (ensures context isolation)
7. **Circuit breakers BLOCK, not warn**
8. **Truth > Approval** - anti-sycophancy is mandatory

---

## Context Isolation Principle

The orchestrator NEVER writes code directly. All implementation is delegated to isolated agents:

| Agent | Spawned Via | Receives | Does NOT Receive |
|-------|-------------|----------|------------------|
| Plan Reviewer | `claude -p` | spec.md, architecture.md | Planning discussion |
| Test Writer | `claude -p` | spec.md, architecture.md | Planning discussion |
| Implementer | `claude -p` | spec.md, architecture.md, tests | Planning discussion |
| Code Reviewer | `claude -p` | src/, tests/ | Any prior context |

**Why**: Context pollution from planning causes hallucinations (implementing rejected ideas) and "loss of big picture."
