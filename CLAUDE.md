# Orchestration Protocol

## Trigger Keyword

**To activate orchestration mode, user must say: `@orchestrate` or `/orchestrate`**

Without this keyword, respond normally.

---

## Workflow Overview (Leverages Built-in Plan Mode)

```
@orchestrate "Build a login page"
    |
    v
[Orc.Phase1_INTAKE] ──────────────────┐
    |                                  │
    v                                  │  Built-in Plan Mode
[Orc.Phase2_PLANNING] ─────────────────┤  (EnterPlanMode)
    |                                  │
    v                                  │
[Orc.Phase3_GEMINI_REVIEW] ───────────┘
    |
    v
[Orc.Phase4_USER_GATE] --> ExitPlanMode --> User approves
    |
    v
[Orc.Phase5_TDD] --> Red phase (fail) --> Green phase (pass)
    |
    v
[Orc.Phase6_DUAL_REVIEW] --> Gemini + Isolated Claude
    |
    v
[Orc.Phase7_USER_GATE_CODE] --> "WAITING FOR CODE APPROVAL"
    |
    v
[Orc.Phase8_SUMMARY] --> TLDR --> ORCHESTRATION COMPLETE
```

---

## State Tracking

Every response during orchestration MUST start with:

```
[Orc.PhaseX_NAME] [Gemini: Y/3] [Status: in_progress|waiting|complete]
```

Examples:
- `[Orc.Phase1_INTAKE] [Gemini: 0/3] [Status: in_progress]`
- `[Orc.Phase5_TDD] [Gemini: 0/3] [Status: in_progress]`

---

## Phase Details

### Orc.Phase1_INTAKE (Uses Plan Mode)

1. Call `EnterPlanMode` tool
2. In plan mode, ask clarifying questions using `AskUserQuestion`
3. Cover: inputs, outputs, edge cases, constraints, success criteria
4. Write findings to `artifacts/spec.md`

**This is plan mode's natural behavior** - explore and understand before coding.

### Orc.Phase2_PLANNING (Uses Plan Mode)

1. Still in plan mode
2. Design architecture based on spec
3. Write to `artifacts/architecture.md`:
   - Component design
   - File structure
   - Dependencies
   - TDD test plan

**Plan mode naturally does this** - designs implementation approach.

### Orc.Phase3_GEMINI_REVIEW (In Plan Mode)

Before exiting plan mode, send to Gemini for review:

1. Read `artifacts/spec.md` and `artifacts/architecture.md`
2. Call `mcp__gemini__ask-gemini` with:

```
Working directory: [PWD]

Review this specification and architecture.

SPEC:
---
[FULL CONTENT]
---

ARCHITECTURE:
---
[FULL CONTENT]
---

INSTRUCTIONS:
1. Check completeness and feasibility
2. Verify TDD strategy is sound
3. Respond with:
   - VERDICT: APPROVED or NEEDS_WORK
   - ISSUES: Problems found
   - SUGGESTIONS: Improvements

CRITICAL: Return your response as TEXT ONLY. DO NOT create any files. DO NOT write any .md files. Just respond with your verdict and feedback inline.
```

3. If NEEDS_WORK and iteration < 3: Update and re-review
4. If iteration == 3: Note issues, proceed anyway

### Orc.Phase4_USER_GATE (Exit Plan Mode)

1. Call `ExitPlanMode` tool
2. This naturally triggers user approval
3. Present summary of spec + architecture + Gemini feedback
4. **STOP** - plan mode handles the approval gate

**Exit criteria:** User approves the plan

### Orc.Phase5_TDD (Custom - Post Plan Mode)

After user approves plan:

1. Use Task tool to spawn `coder` subagent (or do inline)
2. Follow strict TDD:

   **RED PHASE:**
   - Write test files FIRST
   - Run tests: `npm test` / `vitest`
   - **VERIFY tests FAIL**

   **GREEN PHASE:**
   - Write MINIMAL implementation
   - Run tests again
   - **VERIFY tests PASS**

3. If tests don't fail in RED phase → rewrite tests
4. If tests won't pass after 3 attempts → ask user

### Orc.Phase6_DUAL_REVIEW (Custom)

**Review 1: Gemini**

```
Working directory: [PWD]

Review implementation code in src/ and tests/.

Check:
1. Code quality
2. Security vulnerabilities
3. Test coverage
4. Edge cases

Respond with VERDICT: APPROVED or NEEDS_WORK

CRITICAL: Return your response as TEXT ONLY. DO NOT create any files. Just respond inline.
```

**Review 2: Isolated Claude**

Spawn separate process via Bash:

```bash
claude -p "You are a code reviewer with ZERO context.
Read src/ and tests/. Find problems.
Output to artifacts/review-feedback.md" \
  --allowedTools Read,Glob,Grep,Write \
  --print
```

**Aggregate feedback** - if critical issues, go back to Orc.Phase5_TDD

### Orc.Phase7_USER_GATE_CODE

1. Present:
   - Implementation summary
   - Gemini review results
   - Isolated Claude review results
   - Test results
2. Output: `--- WAITING FOR CODE APPROVAL ---`
3. **STOP** until user approves

### Orc.Phase8_SUMMARY

1. Generate TLDR:
   - What was built
   - Files created/modified
   - Test results
2. Output: `✓ ORCHESTRATION COMPLETE`

---

## Key Insight: Plan Mode Integration

| Phase | Mechanism |
|-------|-----------|
| Orc.Phase1-3 | Inside `EnterPlanMode` |
| Orc.Phase4 | `ExitPlanMode` (built-in approval gate) |
| Orc.Phase5-6 | Custom TDD + dual review |
| Orc.Phase7 | Manual approval gate |
| Orc.Phase8 | Summary |

**Why this works:**
- Plan mode already handles exploration, design, and user approval
- We just add: Gemini review during planning + TDD enforcement + dual review after coding

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Gemini rejects 3x | Note issues, proceed to user gate |
| Tests won't fail (red) | Rewrite tests |
| Tests won't pass 3x | Escalate to user |
| User rejects plan | Stay in plan mode, revise |
| User rejects code | Go back to Orc.Phase5_TDD |

---

## Artifacts

| File | Phase |
|------|-------|
| `artifacts/spec.md` | Orc.Phase1_INTAKE |
| `artifacts/architecture.md` | Orc.Phase2_PLANNING |
| `artifacts/review-feedback.md` | Orc.Phase6_DUAL_REVIEW |

---

## Important Rules

1. **Only activate on `@orchestrate` keyword**
2. **Use EnterPlanMode for phases 1-4** (don't reinvent)
3. **Gemini review happens BEFORE ExitPlanMode**
4. **TDD is mandatory** - red before green
5. **Fresh reviewer uses Bash `claude -p`** - NOT Task tool
6. **Track state** - every response starts with `[Orc.PhaseX_NAME]`
