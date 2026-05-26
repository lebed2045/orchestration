# /wf10-gc - Workflow v10 (wf9 + Optional Human Gate)

**Version 10**: wf9 + optional `-h` flag for human gate after TDD_RED.

**Usage:**
- `/wf10-gc <task>` — Fully autonomous (same as wf9)
- `/wf10-gc -h <task>` — Human gate after tests written

**Core features** (from wf9):
1. `mcp__gemini__brainstorm` with design-thinking for architecture
2. `mcp__codex-cli__review` with `uncommitted: true` for code review
3. Parallel reviews, CodeSmell, auto-commit

---

## Flag Detection

```bash
HUMAN_GATE=false
TASK="$ARGUMENTS"

if [[ "$ARGUMENTS" == *"-h"* ]]; then
  HUMAN_GATE=true
  TASK="${ARGUMENTS//-h/}"
  TASK="${TASK## }"  # trim leading space
fi

echo "HUMAN_GATE: $HUMAN_GATE"
echo "TASK: $TASK"
```

---

## CRITICAL: NO PRE-EXISTING TEST FAILURES

**The baseline has 100% passing tests. ALWAYS.**

If tests fail, YOU broke them. Not "pre-existing." Fix the implementation.

---

## MANDATORY PROOF BLOCKS

### BASELINE_BLOCK (captured BEFORE any changes)

```text
┌─────────────────────────────────────────────┐
│ BASELINE_BLOCK                              │
├─────────────────────────────────────────────┤
│ Tests passing: [N]                          │
│ Tests failing: [N]                          │
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

---

## Phase Flow (8 Phases, 2 Gates, 0-1 Human Gates)

**If `-h` flag**: Human gate after Phase 5 (TDD_RED)

### Phase 1: BASELINE_CAPTURE

Before touching ANY code:

1. Run existing tests, capture output
2. Record git SHA
3. Output BASELINE_BLOCK

```bash
npm test 2>&1 | tee /tmp/baseline.txt || true
echo "GIT_SHA: $(git rev-parse HEAD)"
```

**Do NOT proceed without BASELINE_BLOCK.**

---

### Phase 2: INTAKE (Autonomous)

Infer requirements from codebase and user task. NO questions asked.

1. Read the user's task/request
2. Explore relevant codebase files
3. Write spec to `.claude/temp/spec.md`
4. VERIFY: Show `cat .claude/temp/spec.md | head -30`

---

### Phase 3: PLANNING (Design-Thinking Brainstorm)

Call `mcp__gemini__brainstorm`:

| Parameter | Value |
|-----------|-------|
| prompt | "Architecture approaches for: [task from spec]" |
| domain | "software" |
| methodology | "design-thinking" |
| ideaCount | 3 |
| includeAnalysis | true |

Write to `.claude/temp/architecture.md`:
- Design Exploration (alternatives considered)
- Component design (recommended)
- File structure
- TDD test plan
- High-risk zones

---

### Phase 4: GATE 1/2 - PLAN_REVIEW (Codex + Gemini PARALLEL)

**MUST call BOTH tools in a single message.**

**Tool 1: Codex** - `mcp__codex-cli__codex`:
```text
Review the plan files.
Read: .claude/temp/spec.md, .claude/temp/architecture.md
Output: VERDICT: [APPROVED|NEEDS_WORK]
```

**Tool 2: Gemini** - `mcp__gemini__ask-gemini`:
```text
Review the plan for implementation.
Read: .claude/temp/spec.md, .claude/temp/architecture.md
Output: VERDICT: [APPROVED|NEEDS_WORK]
```

**If NEEDS_WORK**: Fix and re-review (max 3).

---

### Phase 5: TDD_RED — ISOLATED CODER

Spawn isolated coder to write failing tests:

```bash
claude -p "You are a TDD test writer with ZERO prior context.

Read: .claude/temp/spec.md, .claude/temp/architecture.md

Write RED tests:
- At least 1 test per requirement
- Extra tests for high-risk zones
- Tests MUST FAIL

After writing, run tests to verify they fail.
Output EXECUTION_BLOCK showing EXIT_CODE≠0." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**Auto-stage tests:**
```bash
git add tests/
echo "✓ Tests staged after TDD_RED"
```

---

### HUMAN GATE (Only if `-h` flag)

**If HUMAN_GATE=true, STOP here and display:**

## [Architecture](.claude/temp/architecture.md)

[Read architecture.md and write a comprehensive 3-5 sentence summary of the design: what components are being built, how they interact, key technical decisions made, and the overall approach.]

| Test | Description |
|------|-------------|
| `[testName1]` | [What this test validates - one clear sentence] |
| `[testName2]` | [What this test validates - one clear sentence] |
| `[testName3]` | [What this test validates - one clear sentence] |

Tests staged. Awaiting approval...

**Wait for user approval before proceeding to Phase 6.**

---

### Phase 6: TDD_GREEN — ISOLATED CODER

Spawn isolated coder to implement:

```bash
claude -p "You are a TDD implementer with ZERO prior context.

Read: .claude/temp/spec.md, .claude/temp/architecture.md, test files

CRITICAL: Test files are READ-ONLY. Only edit src/ files.

Fix one error at a time until tests pass.

Output:
1. EXECUTION_BLOCK showing EXIT_CODE=0
2. REGRESSION_DELTA comparing to baseline" \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: EXIT_CODE=0 and REGRESSION_DELTA=SAFE

---

### Phase 7: GATE 2/2 - CODE_REVIEW (CodeSmell + Codex + Gemini)

#### Step 1: CodeSmell Check

```bash
for file in $(git status --porcelain | awk '{print $2}'); do
  if [[ -f "$file" && "$file" =~ \.(ts|js|tsx|jsx|py|go|rs)$ ]]; then
    ./Tools/code-smell.sh "$file" --gemini
  fi
done
```

**If any file < 60, refactor and re-check.**

#### Step 2: Codex + Gemini (PARALLEL)

**Tool 1: Codex** - `mcp__codex-cli__review`:
| Parameter | Value |
|-----------|-------|
| uncommitted | true |
| title | "WF10 Gate 2/2 Code Review" |

**Tool 2: Gemini** - `mcp__gemini__ask-gemini`:
```text
Structured review: spec match, security, high-risk coverage.
VERDICT: [APPROVED|NEEDS_WORK]
```

#### SMOKE_TEST + Gate Checkpoint

All must pass: CodeSmell ≥60 + Codex clean + Gemini APPROVED + SMOKE_TEST PASS

---

### Phase 8: COMPLETION + AUTO_COMMIT

Only proceed if ALL pass:
- BASELINE_BLOCK captured
- EXIT_CODE=0
- REGRESSION_DELTA=SAFE
- All reviews passed

```bash
git add -A
TASK_SUMMARY=$(head -5 .claude/temp/spec.md | grep -v "^#" | head -1)

git commit -m "$(cat <<EOF
feat: ${TASK_SUMMARY}

- Planning: design-thinking brainstorm
- Reviews: Codex + Gemini approved
- Regression: SAFE

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo "✓ Auto-committed"
git log -1 --oneline
```

Output: `✓ ORCHESTRATION COMPLETE (wf10)`

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No BASELINE_BLOCK | STOP |
| REGRESSION_DELTA = REGRESSION | STOP |
| CodeSmell < 60 | Refactor (auto) |
| Tests fail 5x | STOP |
| "Pre-existing failures" claim | RETRACT. Fix the code. |

---

## Comparison: wf10 vs wf9

| Aspect | wf9 | wf10 |
|--------|-----|------|
| Human gates | 0 | 0-1 (optional via `-h` flag) |
| `-h` flag support | No | Yes |
| Human gate location | N/A | After TDD_RED |
| Gate output | N/A | Architecture summary + test table |
| Everything else | Same | Same |

---

## User's Task

$ARGUMENTS
