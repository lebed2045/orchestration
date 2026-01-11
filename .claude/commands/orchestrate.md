# /orchestrate - Orchestrated Development Workflow

Activate the 8-phase orchestrated development workflow with TDD, Gemini review, and dual code review.

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
4. Write spec to `artifacts/spec.md`

**Orc.Phase2_PLANNING** - Design architecture (still in plan mode)
1. Design architecture based on spec
2. Write to `artifacts/architecture.md`:
   - Component design
   - File structure
   - Dependencies
   - TDD test plan

**Orc.Phase3_GEMINI_REVIEW** - Send to Gemini (still in plan mode)
1. Read `artifacts/spec.md` and `artifacts/architecture.md`
2. Call `mcp__gemini__ask-gemini` with FULL content:
```
Working directory: $PWD

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

DON'T EDIT FILES!!!
```
3. If NEEDS_WORK and iteration < 3: Update and re-review
4. Max 3 iterations

**Orc.Phase4_USER_GATE** - Exit plan mode for approval
1. Call `ExitPlanMode` tool
2. Present summary + Gemini feedback
3. Wait for user approval

**Orc.Phase5_TDD** - Test-driven development
1. Write test files FIRST
2. Run tests - VERIFY they FAIL (red phase)
3. Write MINIMAL implementation
4. Run tests - VERIFY they PASS (green phase)
5. If tests don't fail initially, rewrite them

**Orc.Phase6_DUAL_REVIEW** - Two independent reviewers
1. Call `mcp__gemini__ask-gemini` to review code
2. Spawn isolated Claude via Bash:
```bash
claude -p "You are a code reviewer with ZERO context.
Read src/ and tests/. Find problems.
Output to artifacts/review-feedback.md" \
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
