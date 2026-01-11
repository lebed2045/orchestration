# Orchestration Protocol

This project uses an automated orchestration workflow for complex tasks.

## Initialization (CRITICAL)

Before ANY task, discover available agents:

1. Run: `ls .claude/agents/`
2. Read each agent file to understand capabilities
3. Map: intake.md -> requirements, planner.md -> design, coder.md -> TDD

## Workflow Overview

```
User Task
    |
    v
[Phase 1: INTAKE] --> Ask questions --> artifacts/spec.md
    |
    v
[Phase 2: PLANNING] --> Design architecture --> artifacts/architecture.md
    |
    v
[Phase 3: GEMINI REVIEW] --> mcp__gemini__ask-gemini (max 3x)
    |
    v
[Phase 4: USER GATE] --> "WAITING FOR APPROVAL" --> STOP
    |
    v (user approves)
[Phase 5: TDD] --> Red phase (fail) --> Green phase (pass)
    |
    v
[Phase 6: DUAL REVIEW] --> Gemini + Isolated Claude
    |
    v
[Phase 7: USER GATE] --> "WAITING FOR CODE APPROVAL" --> STOP
    |
    v (user approves)
[Phase 8: SUMMARY] --> TLDR --> TASK COMPLETE
```

---

## Phase Details

### Phase 1: INTAKE

1. Use Task tool to spawn `intake` subagent
2. Subagent asks clarifying questions via AskUserQuestion
3. Wait for `artifacts/spec.md` to be created
4. DO NOT proceed until spec is complete and comprehensive

### Phase 2: PLANNING

1. Use Task tool to spawn `planner` subagent
2. Planner reads `artifacts/spec.md`
3. Creates `artifacts/architecture.md` with:
   - Component design
   - File structure
   - Dependencies
   - Test strategy (TDD)
4. Wait for architecture.md to be complete

### Phase 3: GEMINI REVIEW (max 3 iterations)

1. Read `artifacts/spec.md` and `artifacts/architecture.md` completely
2. Call `mcp__gemini__ask-gemini` with this prompt:

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
   - If iteration == 3: CIRCUIT BREAKER -> escalate to user

### Phase 4: USER GATE (SPEC)

1. Present to user:
   - Summary of spec
   - Summary of architecture
   - Gemini's feedback
2. Output exactly: `--- WAITING FOR APPROVAL ---`
3. **STOP** - do not proceed until user says "approved", "continue", or "go"

### Phase 5: TDD IMPLEMENTATION (strict sequence)

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

3. If tests don't fail in RED phase -> reject tests, instruct coder to rewrite
4. If tests won't pass after 3 attempts -> escalate to user

### Phase 6: DUAL REVIEW (parallel)

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
- If critical issues found -> go back to Phase 5

### Phase 7: USER GATE (CODE)

1. Present to user:
   - Summary of implementation
   - Gemini review results
   - Isolated Claude review results
   - Test results
2. Output exactly: `--- WAITING FOR CODE APPROVAL ---`
3. **STOP** - do not proceed until user approves

### Phase 8: SUMMARY

1. Generate TLDR including:
   - What was built (feature summary)
   - Files created/modified
   - Test results (all passing)
   - Any notes or caveats
2. Output: `TASK COMPLETE`

---

## State Tracking

Every response MUST start with status line:

```
[Phase: X/8] [Gemini iterations: Y/3] [Status: in_progress|waiting|complete]
```

Example: `[Phase: 3/8] [Gemini iterations: 2/3] [Status: in_progress]`

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Gemini rejects 3 times | Escalate to USER GATE with all feedback |
| Tests won't fail (red phase) | Reject tests, ask coder to write proper failing tests |
| Tests won't pass after 3 attempts | Escalate to user with error details |
| User rejects at any gate | Return to appropriate phase based on feedback |

---

## Artifacts Directory

All intermediate outputs go to `artifacts/`:

- `spec.md` - Requirements specification
- `architecture.md` - Technical design
- `review-feedback.md` - Combined review results
- `test-results.md` - Test execution logs (optional)

---

## Important Rules

1. **Never skip phases** - follow the workflow exactly
2. **Never proceed past USER GATE without approval**
3. **Always pass FULL content to Gemini** - it cannot see your conversation
4. **Fresh reviewer MUST use Bash claude command** - NOT Task tool
5. **TDD is mandatory** - tests must fail before implementation
6. **Track state** - every response starts with status line
