# Orchestration Protocol

## Trigger Keyword

**To activate orchestration mode, user must say: `@orchestrate` or `/orchestrate`**

When you see this keyword followed by a task description, activate the full 8-phase workflow below.

Without this keyword, respond normally without orchestration.

---

## Workflow Overview

```
@orchestrate "Build a login page"
    |
    v
[OrchestrationPhase1_INTAKE] --> Ask questions --> artifacts/spec.md
    |
    v
[OrchestrationPhase2_PLANNING] --> Design architecture --> artifacts/architecture.md
    |
    v
[OrchestrationPhase3_GEMINI_REVIEW] --> mcp__gemini__ask-gemini (max 3x)
    |
    v
[OrchestrationPhase4_USER_GATE_SPEC] --> "WAITING FOR APPROVAL" --> STOP
    |
    v (user approves)
[OrchestrationPhase5_TDD] --> Red phase (fail) --> Green phase (pass)
    |
    v
[OrchestrationPhase6_DUAL_REVIEW] --> Gemini + Isolated Claude
    |
    v
[OrchestrationPhase7_USER_GATE_CODE] --> "WAITING FOR CODE APPROVAL" --> STOP
    |
    v (user approves)
[OrchestrationPhase8_SUMMARY] --> TLDR --> TASK COMPLETE
```

---

## State Tracking

Every response during orchestration MUST start with:

```
[OrchestrationPhaseX_NAME] [Gemini: Y/3] [Status: in_progress|waiting|complete]
```

Examples:
- `[OrchestrationPhase1_INTAKE] [Gemini: 0/3] [Status: in_progress]`
- `[OrchestrationPhase4_USER_GATE_SPEC] [Gemini: 2/3] [Status: waiting]`

---

## Initialization

When `@orchestrate` is detected:

1. Run: `ls .claude/agents/`
2. Read each agent file to understand capabilities
3. Map: intake.md → requirements, planner.md → design, coder.md → TDD
4. Begin OrchestrationPhase1_INTAKE

---

## Phase Details

### OrchestrationPhase1_INTAKE

1. Use Task tool to spawn `intake` subagent
2. Subagent asks clarifying questions via AskUserQuestion
3. Wait for `artifacts/spec.md` to be created
4. DO NOT proceed until spec is complete and comprehensive

**Exit criteria:** `artifacts/spec.md` exists and is complete

### OrchestrationPhase2_PLANNING

1. Use Task tool to spawn `planner` subagent
2. Planner reads `artifacts/spec.md`
3. Creates `artifacts/architecture.md` with:
   - Component design
   - File structure
   - Dependencies
   - Test strategy (TDD)
4. Wait for architecture.md to be complete

**Exit criteria:** `artifacts/architecture.md` exists and is complete

### OrchestrationPhase3_GEMINI_REVIEW

Max 3 iterations.

1. Read `artifacts/spec.md` and `artifacts/architecture.md` completely
2. Call `mcp__gemini__ask-gemini` with:

```
Working directory: [INSERT PWD]

Review this specification and architecture for a software project.

SPEC:
---
[INSERT FULL CONTENT OF spec.md]
---

ARCHITECTURE:
---
[INSERT FULL CONTENT OF architecture.md]
---

INSTRUCTIONS:
1. Analyze for completeness, correctness, and feasibility
2. Check for missing edge cases
3. Verify TDD strategy is sound
4. Respond with:
   - VERDICT: APPROVED or NEEDS_WORK
   - ISSUES: List any problems found
   - SUGGESTIONS: Improvements to make

DON'T EDIT ANY FILES, REVIEW ONLY!!!
```

3. If VERDICT is NEEDS_WORK:
   - If iteration < 3: Update artifacts based on feedback, re-review
   - If iteration == 3: CIRCUIT BREAKER → proceed to OrchestrationPhase4 with issues noted

**Exit criteria:** Gemini APPROVED or max iterations reached

### OrchestrationPhase4_USER_GATE_SPEC

1. Present to user:
   - Summary of spec
   - Summary of architecture
   - Gemini's feedback (including any unresolved issues)
2. Output exactly: `--- WAITING FOR APPROVAL ---`
3. **STOP** - do not proceed until user says "approved", "continue", or "go"

**Exit criteria:** User approval received

### OrchestrationPhase5_TDD

1. Use Task tool to spawn `coder` subagent
2. Coder MUST follow this exact sequence:

   **RED PHASE:**
   a. Read `artifacts/spec.md` and `artifacts/architecture.md`
   b. Write test file(s) FIRST (before any implementation)
   c. Run tests with `npm test` or `vitest` or appropriate runner
   d. **VERIFY tests FAIL** - if they pass, something is wrong, rewrite tests

   **GREEN PHASE:**
   e. Write MINIMAL implementation code to make tests pass
   f. Run tests again
   g. **VERIFY tests PASS**

3. If tests don't fail in RED phase → reject tests, instruct coder to rewrite
4. If tests won't pass after 3 attempts → escalate to user

**Exit criteria:** All tests passing

### OrchestrationPhase6_DUAL_REVIEW

**Review 1: Gemini**

Call `mcp__gemini__ask-gemini` with:

```
Working directory: [INSERT PWD]

Review this implementation code for quality and security.

Read all files in src/ and tests/ using @ syntax.

INSTRUCTIONS:
1. Check code quality and best practices
2. Look for security vulnerabilities
3. Verify test coverage is adequate
4. Check for edge cases not handled
5. Respond with:
   - VERDICT: APPROVED or NEEDS_WORK
   - ISSUES: List problems found
   - SECURITY: Any security concerns

DON'T EDIT ANY FILES, REVIEW ONLY!!!
```

**Review 2: Isolated Claude (CRITICAL)**

Spawn a SEPARATE Claude process via Bash to ensure NO context pollution:

```bash
claude -p "You are a code reviewer with ZERO prior context about this project.

Read the code in src/ and tests/ directories.
You know NOTHING about why this code was written.

Review for:
1. Code quality and readability
2. Security vulnerabilities
3. Test coverage gaps
4. Edge cases not handled
5. Potential bugs

Output your findings to artifacts/review-feedback.md

Be thorough and harsh - find problems." \
  --allowedTools Read,Glob,Grep,Write \
  --print
```

**Aggregate:**
- Read both review results
- Combine unique issues
- If critical issues found → go back to OrchestrationPhase5_TDD

**Exit criteria:** Both reviewers approve (or issues are minor)

### OrchestrationPhase7_USER_GATE_CODE

1. Present to user:
   - Summary of implementation
   - Gemini review results
   - Isolated Claude review results
   - Test results
2. Output exactly: `--- WAITING FOR CODE APPROVAL ---`
3. **STOP** - do not proceed until user approves

**Exit criteria:** User approval received

### OrchestrationPhase8_SUMMARY

1. Generate TLDR including:
   - What was built (feature summary)
   - Files created/modified
   - Test results (all passing)
   - Any notes or caveats
2. Output: `✓ ORCHESTRATION COMPLETE`

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Gemini rejects 3 times | Proceed to USER_GATE with all feedback noted |
| Tests won't fail (red phase) | Reject tests, ask coder to rewrite |
| Tests won't pass after 3 attempts | Escalate to user with error details |
| User rejects at any gate | Return to appropriate phase based on feedback |

---

## Artifacts Directory

All intermediate outputs go to `artifacts/`:

| File | Phase Created |
|------|---------------|
| `spec.md` | OrchestrationPhase1_INTAKE |
| `architecture.md` | OrchestrationPhase2_PLANNING |
| `review-feedback.md` | OrchestrationPhase6_DUAL_REVIEW |

---

## Important Rules

1. **Only activate on `@orchestrate` or `/orchestrate` keyword**
2. **Never skip phases** - follow the workflow exactly
3. **Never proceed past USER GATE without approval**
4. **Always pass FULL content to Gemini** - it cannot see your conversation
5. **Fresh reviewer MUST use Bash claude command** - NOT Task tool
6. **TDD is mandatory** - tests must fail before implementation
7. **Track state** - every response starts with phase status line
