# /ddr2 - Divide Delegate Reflect v2 (Autonomous)

**DDR2** is a fully autonomous meta-orchestrator. No human gates, delegates to `/wf8-gc`, auto-commits.

**PM Folder**: `.claude/pm/`

---

## Config

```yaml
LOC_THRESHOLD: 50
MAX_WF8_ATTEMPTS: 2
SPLIT_RANGE: [2, 5]          # Dynamic, not fixed 3
MAX_DEPTH: 2
MAX_TOTAL_COMMITS: 10        # Circuit breaker
MAX_TOTAL_LOC: 500           # Circuit breaker
```

---

## Flow (No Human Gates)

```
/ddr2 <card> [--depth N]
     │
     ▼
┌──────────────────┐
│ PREFLIGHT        │ Check clean workspace, read CLAUDE.md
└────────┬─────────┘
         ▼
┌──────────────────┐
│ DETECT_ENV       │ Detect test command from CLAUDE.md
└────────┬─────────┘
         ▼
┌──────────────────┐
│ CARD_INTAKE      │ Infer context (no questions)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ LOC_ESTIMATE     │
└────────┬─────────┘
    ┌────┴────┐
   ≤50       >50
    ▼         ▼
 DELEGATE   AUTO-DECOMPOSE
 to /wf8-gc    into 2-5 subtasks
    │              │
┌───┴───┐     Sub1→Sub2→...→SubN
OK    FAIL         │
│       │          ▼
▼       ▼     (context inherited)
DONE ← REFLECT → SPLIT → RECURSE (depth+1)
         │
    [MANUAL_INTERVENTION from wf8?]
         │
         ▼
    STOP immediately
```

---

## Phases

### 0. PREFLIGHT (Required)

**Check workspace is clean before starting.**

```bash
# Verify clean workspace
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: Workspace not clean. Commit or stash changes first."
  exit 1
fi
echo "✓ Workspace clean"
```

**Read project CLAUDE.md for context:**

```bash
# Store project root
PROJECT_ROOT=$(pwd)
echo "PROJECT_ROOT=$PROJECT_ROOT" > .claude/temp/ddr2-env.txt

# Check for CLAUDE.md
if [ -f "CLAUDE.md" ]; then
  echo "✓ Found CLAUDE.md"
elif [ -f ".claude/CLAUDE.md" ]; then
  echo "✓ Found .claude/CLAUDE.md"
else
  echo "⚠ No CLAUDE.md found - will infer test command"
fi
```

---

### 1. DETECT_ENV

**Detect test command from CLAUDE.md - do NOT let wf8 guess.**

```bash
# Try to find test command in CLAUDE.md
TEST_CMD=""

if [ -f "CLAUDE.md" ]; then
  TEST_CMD=$(grep -E "dotnet test|npm test|cargo test|pytest|go test" CLAUDE.md | head -1 | sed 's/.*`\([^`]*\)`.*/\1/')
elif [ -f ".claude/CLAUDE.md" ]; then
  TEST_CMD=$(grep -E "dotnet test|npm test|cargo test|pytest|go test" .claude/CLAUDE.md | head -1 | sed 's/.*`\([^`]*\)`.*/\1/')
fi

# Fallback detection
if [ -z "$TEST_CMD" ]; then
  if [ -f "package.json" ]; then
    TEST_CMD="npm test"
  elif [ -f "Cargo.toml" ]; then
    TEST_CMD="cargo test"
  elif [ -f "*.csproj" ] || [ -d "Tests" ]; then
    TEST_CMD="dotnet test"
  elif [ -f "pytest.ini" ] || [ -f "setup.py" ]; then
    TEST_CMD="pytest"
  else
    TEST_CMD="npm test"  # default fallback
  fi
fi

echo "TEST_CMD=$TEST_CMD" >> .claude/temp/ddr2-env.txt
echo "✓ Test command: $TEST_CMD"
```

**Pass TEST_CMD explicitly to wf8** - never let it guess.

---

### 2. CARD_INTAKE (Autonomous)

Infer from codebase. No user questions.

Write task to `.claude/temp/ddr2-task.md`.

---

### 3. LOC_ESTIMATE

- `≤50` → Delegate to /wf8-gc
- `>50` → Decompose into 2-5 subtasks (dynamic based on analysis)

---

### 4A. DELEGATE

**Pass test command explicitly to wf8:**

```bash
source .claude/temp/ddr2-env.txt
claude -p "Execute /wf8-gc: $(cat .claude/temp/ddr2-task.md)

IMPORTANT: Use this test command (do NOT infer):
TEST_CMD=$TEST_CMD

Read CLAUDE.md for project conventions." --print
```

---

### 4B. DECOMPOSE (Dynamic Split)

**Analyze task to determine optimal split (2-5 subtasks):**

```text
DECOMPOSITION RULES:
- 2 subtasks: Simple refactors, renames, config changes
- 3 subtasks: Standard features (foundation → core → integration)
- 4 subtasks: Complex features with separate test/validation phase
- 5 subtasks: Multi-system changes with explicit boundaries

DO NOT force 3-split on everything.
```

**Write subtasks to `.claude/temp/ddr2-subtasks.md`:**

```markdown
## Subtask 1: [Foundation]
LOC estimate: X
Dependencies: none

## Subtask 2: [Core]
LOC estimate: Y
Dependencies: Subtask 1

## Subtask 3: [Integration] (if needed)
LOC estimate: Z
Dependencies: Subtask 1, 2
```

**Create shared context file for inheritance:**

```bash
echo "# DDR2 Shared Context" > .claude/temp/ddr2-context.md
echo "Created: $(date)" >> .claude/temp/ddr2-context.md
echo "" >> .claude/temp/ddr2-context.md
echo "## Architectural Decisions" >> .claude/temp/ddr2-context.md
echo "(Updated by each subtask)" >> .claude/temp/ddr2-context.md
```

**Execute subtasks sequentially with context inheritance:**

```bash
for subtask in subtasks; do
  source .claude/temp/ddr2-env.txt

  claude -p "Execute /wf8-gc: $subtask

  IMPORTANT:
  - Test command: $TEST_CMD
  - Read .claude/temp/ddr2-context.md for previous subtask decisions
  - APPEND your architectural decisions to .claude/temp/ddr2-context.md
  - Read CLAUDE.md for project conventions" --print

  # Check for MANUAL_INTERVENTION signal
  if [ $? -ne 0 ]; then
    echo "Subtask failed - checking if recoverable..."
    # Check wf8 output for MANUAL_INTERVENTION
    break
  fi
done
```

---

### 5. REFLECT_SPLIT (On Failure)

**If WF8 fails, check failure type before recursing:**

```text
FAILURE TRIAGE:
1. MANUAL_INTERVENTION signal from wf8 → STOP immediately (don't recurse)
2. Same failure signature twice → STOP (circuit breaker)
3. Missing dependency/tooling → STOP (can't fix by splitting)
4. Test failure → Reflect and split smaller
5. Merge conflict → STOP (needs human resolution)
```

**If recoverable, recurse with explicit depth:**

```bash
CURRENT_DEPTH=${DEPTH:-0}
NEXT_DEPTH=$((CURRENT_DEPTH + 1))

if [ $NEXT_DEPTH -gt 2 ]; then
  echo "MAX_DEPTH reached. MANUAL INTERVENTION REQUIRED."
  exit 1
fi

# Recurse with incremented depth
claude -p "/ddr2 --depth $NEXT_DEPTH: $smaller_task" --print
```

---

### 6. DDR2_RESULT

```text
┌─────────────────────────────────────────────┐
│ DDR2_RESULT                                 │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Status: [SUCCESS|FAILURE|MANUAL_REQUIRED]   │
│ Commits: [SHAs]                             │
│ Depth reached: [0-2]                        │
│ Subtasks completed: [N/M]                   │
│ Human gates: 0                              │
│ Test command used: [TEST_CMD]               │
└─────────────────────────────────────────────┘
```

---

## Git (Safe Failure Mode)

**SUCCESS**: Auto-commit (done by wf8)

**FAILURE**: Preserve work for debugging

```bash
# DON'T destroy work - stash it for human inspection
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
git stash push -m "ddr2-failed-$TIMESTAMP"
echo "Failed work saved to: git stash show stash@{0}"
echo "To recover: git stash pop"
echo "To discard: git stash drop"
```

**Alternative**: Create failed branch instead of stash

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
git checkout -b "ddr2-failed-$TIMESTAMP"
git add -A
git commit -m "WIP: DDR2 failed state for debugging"
git checkout -  # Return to original branch
echo "Failed work saved to branch: ddr2-failed-$TIMESTAMP"
```

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| Workspace not clean | STOP before starting |
| wf8 returns MANUAL_INTERVENTION | STOP immediately |
| Same failure signature 2x | STOP, don't recurse |
| MAX_DEPTH (2) exceeded | STOP |
| MAX_TOTAL_COMMITS (10) exceeded | STOP |
| MAX_TOTAL_LOC (500) exceeded | STOP |
| Missing tooling/dependency | STOP (can't fix by splitting) |

---

## DDR vs DDR2

| Aspect | DDR | DDR2 |
|--------|-----|------|
| Delegates to | /wf3-gh | /wf8-gc |
| Human gates | 2 | **0** |
| Commits | Manual | **Auto** |
| Split factor | Fixed 3 | **Dynamic 2-5** |
| Failure mode | Reset hard | **Git stash (safe)** |
| Test command | Inferred | **Explicit from CLAUDE.md** |
| Context sharing | None | **ddr2-context.md** |
| Depth tracking | Implicit | **Explicit --depth** |

---

## User's Card

$ARGUMENTS
