# /ddr - Divide Delegate Reflect

**DDR** is a meta-orchestrator for PM cards. Assesses complexity, delegates to `/o3`, recursively decomposes on failure.

**PM Folder**: `.claude/pm/`

---

## Config

```yaml
COMPLEXITY_THRESHOLD: 3    # Score 1-5, delegate if ≤3
MAX_O3_ATTEMPTS: 2
SPLIT_FACTOR: 3
MAX_DEPTH: 5
```

---

## Card Format

```markdown
# NN: Title

## Goal
[Single sentence]

## Requirements
- [Criterion 1]
- [Criterion 2]

## Technical (optional)
[Code hints]

## Test
1. [Step 1]
2. [Step 2]
```

---

## Flow

```
/ddr <card>
     │
     ▼
┌──────────────────┐
│ 1. CARD_INTAKE   │ Read card, ask user DoD, scan context
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. COMPLEXITY    │ Score 1-5 (not LOC)
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
   ≤3        >3
    │         │
    ▼         ▼
┌────────┐  ┌──────────────┐
│DELEGATE│  │DESIGN SUB1   │ ← Just-in-Time (not waterfall)
│ to /o3 │  │Execute Sub1  │
└───┬────┘  │Verify → Sub2 │
    │       └──────┬───────┘
┌───┴───┐          │
│       │          │
OK    FAIL         │
│       │          │
▼       ▼          ▼
DDR_RESULT ← REFLECT → SPLIT → RECURSE (isolated)
```

---

## Phase 1: CARD_INTAKE

**1.1 Load Card**

```bash
ls .claude/pm/*.md 2>/dev/null || echo "Create .claude/pm/ first"
```

If no argument, list cards and ask user to select.

**1.2 Clarify with User**

Ask via `AskUserQuestion`:
- Scope confirmation
- Definition of Done
- Constraints
- Dependencies

**1.3 Context Scan**

Use specific tools:

```bash
# Find affected files
rg -l "<keyword>" --type ts --type js | head -20

# Count existing related code
wc -l $(rg -l "<keyword>" --type ts) 2>/dev/null | tail -1
```

Output:

```text
┌─────────────────────────────────────────────┐
│ CONTEXT_SCAN                                │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Goal: [from card]                           │
│ Files affected: [N files]                   │
│ New dependencies: [list or "none"]          │
│ Unknowns: [list or "none"]                  │
│ DoD: [user confirmed]                       │
└─────────────────────────────────────────────┘
```

---

## Phase 2: COMPLEXITY_SCORE

**NOT LOC.** Score based on concrete factors:

| Factor | Weight | Score 1-5 |
|--------|--------|-----------|
| Files to touch | High | 1=1-2, 2=3-5, 3=6-10, 4=11-20, 5=>20 |
| New dependencies | Medium | 1=0, 2=1, 3=2, 4=3-4, 5=>4 |
| Unknowns/risks | High | 1=0, 2=1, 3=2, 4=3, 5=>3 |
| Cross-cutting | Medium | 1=isolated, 3=2 systems, 5=many |

**Formula**: `(files*2 + deps + unknowns*2 + cross) / 6`

```text
┌─────────────────────────────────────────────┐
│ COMPLEXITY_SCORE                            │
├─────────────────────────────────────────────┤
│ Files to touch: [N] → score [1-5]           │
│ New dependencies: [N] → score [1-5]         │
│ Unknowns: [N] → score [1-5]                 │
│ Cross-cutting: [desc] → score [1-5]         │
│ ─────────────────────────────               │
│ WEIGHTED SCORE: [1-5]                       │
│ THRESHOLD: 3                                │
│ DECISION: [DELEGATE|DECOMPOSE]              │
└─────────────────────────────────────────────┘
```

---

## Phase 3A: DELEGATE (Score ≤ 3)

**3A.1 Prepare**

Write `.claude/temp/ddr-task.md` with enriched context.

**3A.2 Call /o3 (Isolated)**

Spawn subprocess for context isolation:

```bash
claude -p "Execute this task following /o3 workflow:
$(cat .claude/temp/ddr-task.md)

When done, output DDR_RESULT block with SUCCESS or FAILURE + reflection." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**3A.3 Parse Result**

Look for:
- `ORCHESTRATION COMPLETE` → SUCCESS
- `CIRCUIT BREAKER` → FAILURE + reflection

Proceed to Phase 5 (DDR_RESULT).

---

## Phase 3B: DECOMPOSE (Score > 3) - Just-in-Time

**CRITICAL: Do NOT pre-write all subtask cards. One at a time.**

**3B.1 Design Subtask 1 Only**

| Subtask | Purpose |
|---------|---------|
| Sub1 | Foundation — independently testable, unblocks Sub2 |

Ask user to validate Sub1 design only.

**3B.2 Write Sub1 Card**

Create `.claude/pm/[card]-sub1.md`:

```markdown
# [card]-sub1: [Title]

## Goal
[Atomic goal]

## Requirements
- [specific]

## Parent
Card: .claude/pm/[card].md
Subtask: 1 of 3 (JIT)

## Test
1. [verification]

## Produces (for Sub2)
- [artifact 1]
- [artifact 2]
```

**3B.3 Recurse on Sub1 (Isolated)**

```bash
claude -p "Run /ddr workflow on: .claude/pm/[card]-sub1.md
Output DDR_RESULT when done." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**3B.4 PRECONDITION_CHECK for Sub2**

After Sub1 completes, verify artifacts exist:

```bash
# Check Sub1 produced what it promised
ls [expected_file_1] && ls [expected_file_2]
```

```text
┌─────────────────────────────────────────────┐
│ PRECONDITION_CHECK (Sub2)                   │
├─────────────────────────────────────────────┤
│ Required from Sub1: [list]                  │
│ Found: [list]                               │
│ Missing: [list or "none"]                   │
│ VERDICT: [PROCEED|BLOCKED]                  │
└─────────────────────────────────────────────┘
```

If BLOCKED, return to Sub1 with feedback.

**3B.5 Design & Execute Sub2**

Only NOW design Sub2 based on actual Sub1 output.

Repeat 3B.1-3B.4 for Sub2, then Sub3.

---

## Phase 4: REFLECT_SPLIT (O3 Failed)

**4.1 Capture Reflection**

```text
┌─────────────────────────────────────────────┐
│ FAILURE_REFLECTION                          │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Attempts: [N]                               │
│ Reason: [from O3]                           │
│ Blocker: [specific]                         │
│ Learning: [insight]                         │
└─────────────────────────────────────────────┘
```

**4.2 Informed Split (JIT)**

Use reflection to design Sub1 that addresses the blocker.

Then proceed to Phase 3B (JIT decomposition).

---

## Phase 5: DDR_RESULT (Required)

**Every DDR execution MUST end with this block:**

```text
┌─────────────────────────────────────────────┐
│ DDR_RESULT                                  │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Depth: [N]                                  │
│ Status: [SUCCESS|FAILURE]                   │
│ Subtasks completed: [N/M]                   │
│ Artifacts created: [list]                   │
│ Reflection: [if failed, why]                │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]            │
└─────────────────────────────────────────────┘
```

Parent DDR uses this to validate child DDR success.

---

## State Tracking

Every response starts with:

```text
[DDR] Card: [name] | Depth: [N] | Score: [1-5] | Status: [phase]
```

---

## Context Isolation

**CRITICAL: All recursion uses `claude -p` subprocess.**

This prevents context overflow. Each recursive call:
1. Starts with fresh context
2. Reads only necessary files
3. Returns structured DDR_RESULT

```bash
# Recursive call template
claude -p "Run /ddr on .claude/pm/[card].md
Context: [minimal needed info]
Output: DDR_RESULT block" \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

---

## Limits

| Limit | Value | On Exceed |
|-------|-------|-----------|
| Max depth | 5 | STOP, ask user |
| Max subtasks | 15 | STOP, too complex |
| O3 failures | 2 per card | Reflect + split |

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No PM folder | Create `.claude/pm/` |
| Card not found | List available |
| Depth > 5 | Escalate to user |
| O3 fails 2x | Reflect + split |
| PRECONDITION_CHECK fails | Return to previous subtask |

---

## Usage

```bash
/ddr              # List cards
/ddr feature-x    # Work on card
```

---

## User's Card

$ARGUMENTS
