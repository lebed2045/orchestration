# /wf1 - Workflow v1

**Version 1**: 8-phase workflow with Gemini review. Orchestrator writes code directly.

Uses agents: `coder-v1`, `planner-v1`, `intake-v1`, `fresh-reviewer-v1`

---

## VSCODE COMPATIBILITY (CRITICAL)

**VSCode plugin has a bug with parallel tool calls. To avoid "API Error: 400":**

1. **DO NOT use Task tool with Explore agent** - It makes parallel calls that crash
2. **Explore manually** - Use Read, Grep, Glob directly, ONE AT A TIME
3. **Sequential tool calls only** - Never batch multiple tool calls in one response during exploration
4. **Wait for each result** - Before making next tool call

This applies to ALL phases, especially INTAKE when understanding the codebase.

---

## Git Staging Discipline

**Tests get staged after test review. Implementation requires user permission.**

| Phase | Action | Git Staging |
|-------|--------|-------------|
| TDD (write tests) | Write tests | Not staged yet |
| TDD (test review) | Review tests | **Auto-stage tests** after APPROVED |
| TDD (implement) | Write implementation | Not staged yet |
| CODE_REVIEW | Review code | **Ask user** before staging |
| Completion | Done | **Never auto-commit** |

**After test review approval:**

```bash
git add tests/  # or specific test files
echo "✓ Tests staged after test review approval"
```

**After code review, ask user:**

```text
Tests are staged. Implementation is ready.
- Stage implementation? [y/n]
- Commit all? [y/n]
```

---

## Instructions

You are now in **Orchestration Mode**. Follow this workflow exactly:

### State Tracking

Every response MUST start with:
```
[Orc.PhaseX_NAME] [Gemini: Y/3] [Status: in_progress|waiting|complete]
```

### Phase Flow

**Orc.Phase1_INTAKE** - Enter plan mode, ask clarifying questions
1. Call `EnterPlanMode` tool
2. Ask clarifying questions using `AskUserQuestion`
3. Cover: inputs, outputs, edge cases, constraints, success criteria
4. Write spec to `.claude/temp/spec.md`

**Orc.Phase2_PLANNING** - Design architecture (still in plan mode)
1. Design architecture based on spec
2. Write to `.claude/temp/architecture.md`:
   - Component design
   - File structure
   - Dependencies
   - TDD test plan

**Orc.Phase3_GEMINI_REVIEW** - Send to Gemini (still in plan mode)
1. Read `.claude/temp/spec.md` and `.claude/temp/architecture.md`
2. Call `mcp__gemini__ask-gemini` with FULL content:
```
Review this specification and architecture.

SPEC:
---
[FULL CONTENT OF spec.md]
---

ARCHITECTURE:
---
[FULL CONTENT OF architecture.md]
---

Check completeness, feasibility, TDD strategy.
Respond with VERDICT: APPROVED or NEEDS_WORK

CRITICAL: Return your response as TEXT ONLY. DO NOT create any files. DO NOT write any .md files. Just respond with your verdict and feedback inline.
```
3. If NEEDS_WORK and iteration < 3: Update and re-review
4. Max 3 iterations

**Orc.Phase4_USER_GATE** - Exit plan mode for approval
1. Call `ExitPlanMode` tool
2. **MUST PRESENT** (not just "should I proceed?"):
   - **Artifact paths**: Show full paths to spec.md and architecture.md
   - **Spec summary**: Key requirements (3-5 bullet points)
   - **Architecture summary**: Components, files to create/modify
   - **TDD plan**: What tests will be written
   - **Gemini verdict**: APPROVED or NEEDS_WORK with feedback
3. Output format:
```text
┌─────────────────────────────────────────────┐
│ PLAN SUMMARY                                │
├─────────────────────────────────────────────┤
│ Spec: .claude/temp/spec.md                  │
│ Architecture: .claude/temp/architecture.md  │
├─────────────────────────────────────────────┤
│ REQUIREMENTS:                               │
│ • [requirement 1]                           │
│ • [requirement 2]                           │
│ • ...                                       │
├─────────────────────────────────────────────┤
│ FILES TO CREATE/MODIFY:                     │
│ • [file1] - [purpose]                       │
│ • [file2] - [purpose]                       │
├─────────────────────────────────────────────┤
│ TDD PLAN:                                   │
│ • [test 1]                                  │
│ • [test 2]                                  │
├─────────────────────────────────────────────┤
│ GEMINI VERDICT: [APPROVED|NEEDS_WORK]       │
│ [feedback if any]                           │
└─────────────────────────────────────────────┘
```
4. Output: `--- WAITING FOR PLAN APPROVAL ---`
5. Wait for user approval

**Orc.Phase5_TDD_RED** - Write failing tests
1. Write test files FIRST
2. Run tests - VERIFY they FAIL (red phase)
3. If tests don't fail initially, rewrite them

**Orc.Phase5b_TEST_REVIEW** - Review tests before implementation

Call `mcp__gemini__ask-gemini` to review tests:

```text
Review the test files for quality and falsifiability.

Validate:
1. COVERAGE: Tests cover ALL requirements in spec
2. RED_PHASE: Tests are currently FAILING (no implementation)
3. FALSIFIABILITY: Tests CANNOT pass with trivial implementation like 'return true'

FALSIFIABILITY examples:
- BAD: expect(login()).toBeTruthy() - passes with 'return true'
- GOOD: expect(login('user','pass')).toEqual({token: expect.any(String), userId: 'user'})

Output:
VERDICT: APPROVED or NEEDS_WORK
COVERAGE_CHECK: YES/NO
RED_PHASE_CHECK: YES/NO
FALSIFIABILITY_CHECK: YES/NO
ISSUES: [list]
```

**After APPROVED:**

```bash
git add tests/  # Auto-stage tests
echo "✓ Tests staged after review approval"
```

**Orc.Phase5c_TDD_GREEN** - Implement to pass tests
1. Write MINIMAL implementation
2. Run tests - VERIFY they PASS (green phase)
3. Test files are READ-ONLY at this point

**Orc.Phase6_DUAL_REVIEW** - Two independent reviewers
1. Call `mcp__gemini__ask-gemini` to review code:
```
Review the implementation code for quality and security.
Check: code quality, security, test coverage, edge cases.
Respond with VERDICT: APPROVED or NEEDS_WORK

CRITICAL: Return your response as TEXT ONLY. DO NOT create any files. DO NOT write any .md files. Just respond inline.
```
2. Spawn isolated Claude via Bash:
```bash
claude -p "You are a code reviewer with ZERO context.
Read src/ and tests/. Find problems.
Output to .claude/temp/review-feedback.md" \
  --allowedTools Read,Glob,Grep,Write \
  --print
```
3. Aggregate feedback

**Orc.Phase7_USER_GATE_CODE** - Code approval
1. Present implementation + both reviews
2. Output: `--- WAITING FOR CODE APPROVAL ---`
3. Wait for user approval

**Orc.Phase8_SUMMARY** - Complete
1. Generate TLDR of what was built
2. Output: `✓ ORCHESTRATION COMPLETE`

---

## User's Task

$ARGUMENTS
