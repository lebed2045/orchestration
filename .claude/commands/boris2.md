# /boris2 - Boris Mode + Agent Teams

**Tag:** `[2-O | 2-gate | teams]` — 2 Opus reviewers (staff eng + code), 2 gates, Agent Teams

Boris Cherny's workflow patterns + Agent Teams for parallel execution + Reflections log.

**Philosophy**: *"A good plan is really important to avoid issues down the line."* + *"Give Claude a way to verify its work — quality improves 2-3x with feedback loops."*

Based on Boris's actual workflow: Plan Mode → iterate → auto-execute, with Agent Teams for parallel TDD.

---

## BORIS'S CORE PRINCIPLES (Baked In)

| Principle | How boris2 Implements It |
|-----------|----------------------|
| Plan Mode first | Phase 2-3: iterate plan until solid |
| Verification is #1 | Every phase requires EXECUTION_BLOCK proof |
| CLAUDE.md is law | Phase 1: Read and obey project CLAUDE.md |
| Subagents for quality | code-simplifier + verify-app patterns |
| PostToolUse hooks | Auto-format after edits |
| Parallel execution | Agent Teams for TDD_RED + exploration |
| Opus 4.6 with thinking | Recommended model for lead agent |

---

## AGENT TEAMS CONFIGURATION

Enable Agent Teams in your settings.json:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**Model:** Run `/model` → select "Opus 4.6" (don't hardcode model IDs).

Or per-session: `claude --teammate-mode in-process`

**Controls:**
- `Shift+Up/Down` — Select teammate
- `Ctrl+T` — Toggle task list
- `Shift+Tab` — Restrict lead to coordination-only

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
│ VERDICT: [SAFE|REGRESSION]                  │
└─────────────────────────────────────────────┘
```

---

## State Tracking

Every response MUST start with:

```text
[boris2.PhaseX] [Baseline: SET|UNSET] [Team: ACTIVE|SOLO] [Status: in_progress|blocked|complete]
```

---

## Phase Flow (10 Phases, 2 Gates, 0 Human Gates — Fully Autonomous)

### Phase 1: DETECT_ENV + BASELINE

**Read project configuration FIRST. Never assume.**

1. Read `CLAUDE.md` (project root and ~/.claude/)
2. Extract:
   - Test command (DO NOT assume `npm test`)
   - Build command
   - Lint/format command
   - Package manager (bun/npm/yarn/pnpm)
   - Platform-specific rules
3. Run existing tests, capture BASELINE_BLOCK
4. Store in `.claude/temp/boris2-env.sh`:

```bash
# Detect from CLAUDE.md or package.json
mkdir -p .claude/temp
cat > .claude/temp/boris2-env.sh << 'EOF'
TEST_CMD="bun test"
BUILD_CMD="bun run build"
FORMAT_CMD="bun run format"
TYPECHECK_CMD="bun run typecheck"  # or "tsc --noEmit" if not in scripts
LINT_CMD="bun run lint"            # optional, leave empty if none
PKG_MGR="bun"
EOF
source .claude/temp/boris2-env.sh
$TEST_CMD 2>&1 | tee .claude/temp/baseline.txt || true
```

**Tip:** Run `/permissions Bash(bun *) --allow` to skip approval prompts for safe commands.

**Do NOT proceed without BASELINE_BLOCK and .claude/temp/boris2-env.sh.**

---

### Phase 2: PLAN_MODE (Iterate Until Solid)

**Boris: "Most sessions start in Plan mode. Go back and forth until I like the plan."**

1. Enter Plan Mode: `Shift+Tab` twice (or natural language)
2. Read user's task/request
3. Explore codebase (files, patterns, existing tests)
4. Draft plan in `.claude/temp/plan-draft.md`:
   - Requirements (inferred from codebase + task)
   - Architecture approach
   - TDD strategy
   - File ownership (which files each teammate will edit)
   - Verification strategy
5. **Self-review plan** — verify completeness and feasibility
6. VERIFY: Show `cat .claude/temp/plan-draft.md | head -40`

**Auto-proceed: Plan complete → move to Phase 3 (no human approval needed).**

---

### Phase 3: SPEC + ARCHITECTURE

Finalize artifacts from approved plan.

1. Write `.claude/temp/spec.md`:
   - Include BASELINE_BLOCK
   - Include .claude/temp/boris2-env.sh contents
   - Requirements (finalized)
2. Write `.claude/temp/architecture.md`:
   - Component design
   - File structure with **ownership assignments**
   - Dependencies
   - TDD test plan
   - Regression checkpoints
3. VERIFY: Both files exist and are complete

---

### Phase 4: GATE 1 - PLAN_REVIEW (Staff Engineer Claude)

**Boris pattern: One Claude writes, another Claude reviews as staff engineer.**

Spawn a second Claude to challenge the plan:

```bash
claude -p "$(cat .claude/agents/plan-reviewer.md)

Review the plan at:
- .claude/temp/spec.md
- .claude/temp/architecture.md

Be critical. Challenge assumptions. Find gaps.
Output PLAN_REVIEW block with APPROVED or NEEDS_WORK." \
  --allowedTools Read,Glob,Grep \
  --print
```

**If NEEDS_WORK: Fix issues and re-review (max 3 iterations).**

---

### Phase 5: TDD_RED — AGENT TEAM (Parallel)

**Spawn Agent Team for parallel test writing.**

Boris: *"5-6 tasks per teammate. Assign different file sets to prevent merge conflicts."*

```text
Create an agent team for TDD_RED phase with file ownership:

Teammate 1 (Test Writer A):
- Owns: tests/unit/[module-a].test.ts
- Task: Write failing tests for [requirements 1-3]
- Read: .claude/temp/spec.md, .claude/temp/architecture.md, CLAUDE.md
- Test command: [from .claude/temp/boris2-env.sh]

Teammate 2 (Test Writer B):
- Owns: tests/unit/[module-b].test.ts
- Task: Write failing tests for [requirements 4-6]
- Same reads as above

Teammate 3 (Integration Test Writer):
- Owns: tests/integration/
- Task: Write integration test skeleton
- Same reads

All teammates must:
1. Write tests that FAIL (no implementation exists)
2. Tests must be FALSIFIABLE (cannot pass with trivial return)
3. Run tests and show EXECUTION_BLOCK with EXIT_CODE≠0
4. Message lead when complete
```

**Lead coordinates:**
- Monitor via `Ctrl+T` (task list)
- Merge test files when all teammates complete
- Run full test suite to verify RED state

**VERIFY**: All tests fail (EXECUTION_BLOCK with EXIT_CODE≠0)

```bash
set -o pipefail
source .claude/temp/boris2-env.sh
$TEST_CMD 2>&1 | tee .claude/temp/tdd-red.txt
echo "EXIT_CODE: ${PIPESTATUS[0]}"
# Must be non-zero (tests should FAIL at this point)
```

**Auto-stage tests:**
```bash
git add tests/
echo "✓ Tests staged after TDD_RED"
```

---

### Phase 6: TDD_GREEN — ISOLATED CODER

**Single isolated coder implements (tests are READ-ONLY).**

```bash
claude -p "You are a TDD implementer with ZERO prior context.

Read:
- CLAUDE.md (project rules - REQUIRED)
- .claude/temp/spec.md
- .claude/temp/architecture.md
- Test files (READ-ONLY - do not edit)
- .claude/temp/boris2-env.sh (commands)

Commands:
$(cat .claude/temp/boris2-env.sh)

CRITICAL: Test files are READ-ONLY. Only edit src/ files.
CRITICAL: Use the correct test command from env file.

LOOP (max 5): Fix one error at a time until tests pass.

After tests pass, output:
1. EXECUTION_BLOCK showing EXIT_CODE=0
2. REGRESSION_DELTA comparing to baseline in spec.md" \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: EXECUTION_BLOCK with EXIT_CODE=0 + REGRESSION_DELTA=SAFE

**SECURITY**: If coder edits test files, reject and re-spawn.

---

### Phase 7: CODE_SIMPLIFY (Boris Pattern)

**Boris uses `code-simplifier` subagent after implementation.**

Uses modular agent definition from `.claude/agents/code-simplifier.md`:

```bash
source .claude/temp/boris2-env.sh

claude -p "$(cat .claude/agents/code-simplifier.md)

Environment commands:
- Format: $FORMAT_CMD
- Test: $TEST_CMD

Read the implementation files that were just created/modified.
Simplify, then verify tests still pass.
Output EXECUTION_BLOCK proving tests pass after simplification." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**VERIFY**: Tests still pass after simplification (EXECUTION_BLOCK with EXIT_CODE=0).

---

### Phase 8: GATE 2 - CODE_REVIEW (Code Reviewer Claude + verify-app)

**Boris pattern: Fresh Claude reviews code + verification loop.**

**Step 1: Code Reviewer Claude**

Spawn fresh Claude to review implementation:

```bash
claude -p "You are a code reviewer with ZERO prior context.

Read:
- CLAUDE.md (project rules)
- .claude/temp/spec.md (requirements)
- .claude/temp/architecture.md (design)
- src/ files (implementation)
- tests/ files

Check:
1. Does implementation match spec?
2. Code quality and style (per CLAUDE.md)
3. Test coverage adequate?
4. Security issues (OWASP top 10)?
5. Any regressions vs baseline?

Be critical. Output:
CODE_REVIEW
-----------
Spec match:    [OK|ISSUE]
Code quality:  [OK|ISSUE]
Test coverage: [OK|ISSUE]
Security:      [OK|ISSUE]
Regressions:   [OK|ISSUE]
-----------
ISSUES: [list or none]
VERDICT: [APPROVED|NEEDS_WORK]" \
  --allowedTools Read,Glob,Grep \
  --print
```

**If NEEDS_WORK: Fix and re-review (max 3 iterations).**

**Step 2: verify-app pattern (Boris's E2E verification)**

Boris: *"Give Claude a way to verify its work. Quality improves 2-3x."*

Uses modular agent definition from `.claude/agents/verify-app.md`:

```bash
# Run full verification suite (enhanced with typecheck + lint)
# Use pipefail to capture actual command exit codes, not tee's
set -o pipefail
source .claude/temp/boris2-env.sh

echo "=== 1. Type Check ==="
if [ -n "$TYPECHECK_CMD" ]; then
  $TYPECHECK_CMD 2>&1 | tee .claude/temp/verify.txt
  TYPE_EXIT=${PIPESTATUS[0]}
else
  echo "SKIPPED: No TYPECHECK_CMD configured"
  TYPE_EXIT=0
fi

echo "=== 2. Lint ==="
if [ -n "$LINT_CMD" ]; then
  $LINT_CMD 2>&1 | tee -a .claude/temp/verify.txt
  LINT_EXIT=${PIPESTATUS[0]}
else
  echo "SKIPPED: No LINT_CMD configured"
  LINT_EXIT=0
fi

echo "=== 3. Tests ==="
$TEST_CMD 2>&1 | tee -a .claude/temp/verify.txt
TEST_EXIT=${PIPESTATUS[0]}

echo "=== 4. Build ==="
$BUILD_CMD 2>&1 | tee -a .claude/temp/verify.txt
BUILD_EXIT=${PIPESTATUS[0]}

echo "=== Verification Summary ==="
echo "Typecheck: EXIT_CODE=$TYPE_EXIT"
echo "Lint: EXIT_CODE=$LINT_EXIT"
echo "Tests: EXIT_CODE=$TEST_EXIT"
echo "Build: EXIT_CODE=$BUILD_EXIT"
WARN_COUNT=$(grep -ci warn .claude/temp/verify.txt 2>/dev/null || echo 0)
echo "Warnings: $WARN_COUNT"
```

**SMOKE_TEST Block:**
```text
┌─────────────────────────────────────────────┐
│ SMOKE_TEST (verify-app)                     │
├─────────────────────────────────────────────┤
│ Typecheck: [PASS|FAIL|SKIP] (EXIT_CODE)     │
│ Lint:      [PASS|FAIL|SKIP] (EXIT_CODE)     │
│ Tests:     [PASS|FAIL] (EXIT_CODE)          │
│ Build:     [PASS|FAIL] (EXIT_CODE)          │
│ Warnings:  [N] (was [M])                    │
│ VERDICT:   [PASS|FAIL]                      │
└─────────────────────────────────────────────┘
```

**Gate 2/2 Checkpoint:**
```text
┌─────────────────────────────────────────────┐
│ GATE 2 CHECKPOINT                           │
├─────────────────────────────────────────────┤
│ Code Review Claude: [APPROVED|NEEDS_WORK]   │
│ verify-app:         [PASS|FAIL]             │
│ REGRESSION_DELTA:   [SAFE|REGRESSION]       │
├─────────────────────────────────────────────┤
│ GATE STATUS: [PASS|BLOCKED]                 │
└─────────────────────────────────────────────┘
```

**All must pass. If NEEDS_WORK: Fix and re-review (max 3 iterations).**

---

### Phase 9: COMPLETION + COMMIT

**Only proceed if ALL conditions met:**

- [ ] BASELINE_BLOCK captured at start
- [ ] Plan approved in Phase 2
- [ ] EXECUTION_BLOCK shows EXIT_CODE=0
- [ ] REGRESSION_DELTA shows SAFE
- [ ] SMOKE_TEST shows PASS
- [ ] Gate 1: Staff Engineer Claude APPROVED plan
- [ ] Gate 2: Code Reviewer Claude APPROVED code
- [ ] Code simplified (Phase 7)

**Completion Checklist:**
```text
┌─────────────────────────────────────────────┐
│ COMPLETION CHECKLIST                        │
├─────────────────────────────────────────────┤
│ [x] Baseline captured                       │
│ [x] Plan iterated and approved              │
│ [x] Staff engineer approved (Gate 1)        │
│ [x] Tests pass (EXECUTION_BLOCK shown)      │
│ [x] No regression (REGRESSION_DELTA=SAFE)   │
│ [x] Code simplified                         │
│ [x] verify-app passed                       │
│ [x] All Claude reviews passed (2 gates)     │
│ VERDICT: COMPLETE                           │
└─────────────────────────────────────────────┘
```

**Auto-stage and auto-commit (fully autonomous):**

```bash
git add -A
git status
```

**Auto-commit (no approval needed):**

```bash
TASK_SUMMARY=$(head -5 .claude/temp/spec.md | grep -v "^#" | head -1)

git commit -m "$(cat <<EOF
feat: ${TASK_SUMMARY}

- TDD: RED→GREEN verified
- Simplified: code-simplifier applied
- Reviews: Staff engineer + code reviewer approved
- Verification: verify-app passed
- Regression: SAFE

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"

git log -1 --oneline
```

**BORIS2_RESULT Block:**
```text
┌─────────────────────────────────────────────┐
│ BORIS2_RESULT                               │
├─────────────────────────────────────────────┤
│ Task: [description from spec]               │
│ Status: SUCCESS                             │
│ Commit: [SHA]                               │
│ Artifacts: [files created/modified]         │
│ Tests: [N passed, 0 failed]                 │
│ Agent Team: [N teammates spawned]           │
│ Regression: SAFE                            │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

Output: `✓ ORCHESTRATION COMPLETE (Boris Mode)`

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No BASELINE_BLOCK | STOP. Capture baseline first |
| No .claude/temp/boris2-env.sh | STOP. Detect env first |
| Claim without EXECUTION_BLOCK | RETRACT. Run verification |
| REGRESSION_DELTA = REGRESSION | **GOTO Phase 10 (REFLECT)** |
| Teammate edits wrong file | STOP. Reassign file ownership |
| Same error 2x | **GOTO Phase 10 (REFLECT)** |
| Tests fail 5x | **GOTO Phase 10 (REFLECT)** |
| Review fails 3x | **GOTO Phase 10 (REFLECT)** |

---

### Phase 10: REFLECT (On Failure OR Success)

**Triggered by: Circuit breaker OR successful completion.**

**Purpose: Log what happened + compound learnings (Boris Tip #5, #16).**

#### 1. Append to `.claude/reflections.md`

```bash
mkdir -p .claude
cat >> .claude/reflections.md << EOF

---
## $(date +%Y-%m-%d\ %H:%M) | $(basename "$PWD")
- **Task**: $(head -1 .claude/temp/spec.md 2>/dev/null || echo "Unknown")
- **Outcome**: [SUCCESS|FAILURE]
- **Phase reached**: [1-9]
- **Trigger**: [Circuit breaker type or "Completion"]
- **What happened**: [1-2 sentence description]
- **Root cause**: [If failure, what went wrong]
- **Rule added**: [If auto-appended to CLAUDE.md]
EOF
```

#### 2. Reflection Entry Format

```markdown
---
## 2026-02-04 02:05 | my-project
- **Task**: Add OAuth2 authentication
- **Outcome**: FAILURE
- **Phase reached**: 6 (TDD_GREEN)
- **Trigger**: Tests fail 5x
- **What happened**: Circular dependency between auth.ts and user.ts
- **Root cause**: Architecture didn't map existing imports
- **Rule added**: "Run `madge --circular` before refactoring core modules"
```

#### 3. CLAUDE.md Update Policy (Compounding Engineering)

**Auto-append allowed (no approval needed):**

- Append to `## Past Mistakes` section
- Add trivial style rules (e.g., "no enums", "prefer type over interface")
- Fix typos in existing rules

```bash
# Auto-append AFTER the ## Past Mistakes header (not EOF)
RULE="- $(date +%Y-%m-%d): [description of mistake and fix]"

if grep -q "## Past Mistakes" CLAUDE.md; then
  # Insert a blank line + rule after the header
  sed -i '' "/## Past Mistakes/a\\
\\
$RULE
" CLAUDE.md
  echo "Auto-appended rule to CLAUDE.md ## Past Mistakes"
else
  # Section doesn't exist - propose adding it
  echo "CLAUDE.md missing '## Past Mistakes' section. Add it first."
fi
```

**Manual approval required:**
- New sections
- Architectural changes
- Removing or modifying existing rules

```text
This change affects CLAUDE.md structure. Approve?
> [proposed change]
[User must explicitly approve]
```

#### 4. Output REFLECT_BLOCK

```text
┌─────────────────────────────────────────────┐
│ REFLECT_BLOCK                               │
├─────────────────────────────────────────────┤
│ Session: [pwd basename]                     │
│ Task: [from spec.md]                        │
│ Outcome: [SUCCESS|FAILURE]                  │
│ Logged to: .claude/reflections.md           │
│ CLAUDE.md proposal: [Yes/No]                │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

---

## Boris Prompting Patterns (Use These)

### Challenge Claude
> "Grill me on these changes and don't make a PR until I pass your test."

### Request Proof
> "Prove to me this works by showing diff main vs feature."

### After Mediocre Solution
> "Knowing everything you know now, scrap this and implement the elegant solution."

### Add to CLAUDE.md
> "@claude add to CLAUDE.md to never use enums, always prefer literal unions"

---

## PostToolUse Hook (Recommended)

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "bun run format || npm run format || true"
      }]
    }]
  }
}
```

---

## Comparison: boris2 vs wf8-gc

| Aspect | wf8-gc | boris2 |
|--------|-----|-----|
| Phases | 8 | 10 |
| Human gates | 0 | 0 (fully autonomous) |
| Agent Teams | No | Yes (TDD_RED) |
| Plan iteration | No | Yes (self-review, auto-proceed) |
| code-simplifier | No | Yes |
| verify-app pattern | No | Yes |
| CLAUDE.md read | Partial | Full (Phase 1) |
| Env detection | Hardcoded | Dynamic |
| Auto-commit | Yes | Yes |

---

## When to Use boris2

- Complex features needing parallel exploration
- Projects with specific CLAUDE.md rules
- When plan quality matters more than speed
- Multi-file changes with clear ownership
- When you want Boris's workflow patterns

---

## User's Task

$ARGUMENTS
