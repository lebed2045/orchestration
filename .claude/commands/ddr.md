# /ddr - Divide Delegate Reflect

**DDR** is a meta-orchestrator for PM cards. Assesses complexity, delegates to `/wf3`, recursively decomposes on failure.

**PM Folder**: `.claude/pm/`

---

## Config

```yaml
LOC_THRESHOLD: 50          # Lines of code - delegate if ≤50, decompose if >50
MAX_WF3_ATTEMPTS: 2
SPLIT_FACTOR: 3
MAX_DEPTH: 2               # Prefer wide over deep (industry best practice)
LOG_DIR: .claude/temp      # Persistent logs
```

---

## Naming Convention (WBS Standard)

**Format**: `[epic]-[N].[name]-[N].[name].md`

- Dash (`-`) before sequence numbers
- Dot (`.`) before names
- Full ancestry in filename (self-documenting)

**Folder Structure**:
```
.claude/pm/
└── ecom/
    ├── ecom.md                          ← Epic overview
    ├── ecom-1.user-mgmt.md              ← L1: Feature 1
    ├── ecom-1.user-mgmt-1.model.md      ← L2: Subtask 1.1
    ├── ecom-1.user-mgmt-2.auth.md       ← L2: Subtask 1.2
    ├── ecom-1.user-mgmt-3.profile.md    ← L2: Subtask 1.3
    ├── ecom-2.products.md               ← L1: Feature 2
    ├── ecom-3.cart.md                   ← L1: Feature 3
    └── ecom-4.checkout.md               ← L1: Feature 4
```

**Reading**: `ecom-1.user-mgmt-2.auth` = ecom → L1:1 (user-mgmt) → L2:2 (auth)

---

## Git Behavior

**On SUCCESS**: Commit immediately (preserves work)
```bash
git add -A && git commit -m "WIP: [card-name]"
```

**On FAILURE**: Rollback uncommitted changes
```bash
git reset --hard HEAD
```

**Commit messages**:
- Subtask: `WIP: ecom-1.user-mgmt-1.model`
- Feature complete: `feat: ecom-1.user-mgmt complete`

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
│ 2. LOC_ESTIMATE  │ Estimate lines of code needed
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
   ≤50       >50
    │         │
    ▼         ▼
┌────────┐  ┌──────────────┐
│DELEGATE│  │DESIGN SUB1   │ ← Just-in-Time (not waterfall)
│ to /wf3 │  │Execute Sub1  │
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

## Phase 2: LOC_ESTIMATE

Estimate total lines of code needed (new + modified + tests).

**Be conservative** — this is for testing recursive decomposition.

```text
┌─────────────────────────────────────────────┐
│ LOC_ESTIMATE                                │
├─────────────────────────────────────────────┤
│ New code: ~[N] lines                        │
│ Modifications: ~[N] lines                   │
│ Tests: ~[N] lines                           │
│ ─────────────────────────────               │
│ TOTAL: ~[N] lines                           │
│ THRESHOLD: 50 lines                         │
│ DECISION: [DELEGATE|DECOMPOSE]              │
└─────────────────────────────────────────────┘
```

**Decision logic:**
- `TOTAL ≤ 50` → DELEGATE to /wf3
- `TOTAL > 50` → DECOMPOSE into 3 subtasks

---

## Phase 3A: DELEGATE (LOC ≤ 50)

**3A.1 Prepare**

Write `.claude/temp/ddr-task.md` with enriched context.

**3A.2 Call /wf3 (Isolated)**

Try subprocess first, fallback to Task agent if it fails:

```bash
# Primary: subprocess (preferred for isolation)
claude -p "Execute this task following /wf3 workflow:
$(cat .claude/temp/ddr-task.md)

When done, output WF3_RESULT block." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

If subprocess fails (API error, VSCode bug), use Task agent:

```text
Task tool with subagent_type="general-purpose":
- Read .claude/temp/ddr-task.md
- Execute TDD workflow
- Output DDR_RESULT block when done
```

**3A.3 Parse Result**

Look for:
- `ORCHESTRATION COMPLETE` → SUCCESS
- `CIRCUIT BREAKER` → FAILURE + reflection

Proceed to Phase 5 (DDR_RESULT).

---

## Phase 3B: DECOMPOSE (LOC > 50)

**Design all 3 subtasks upfront, get user validation, then execute sequentially.**

**3B.1 Design All 3 Subtasks**

| Subtask | Purpose |
|---------|---------|
| Sub1 | Foundation — independently testable, unblocks Sub2 |
| Sub2 | Core logic — builds on Sub1 artifacts |
| Sub3 | Integration — connects components, final tests |

**3B.2 Clarify Uncertainties**

If ANY aspect of the decomposition is unclear, ask the user via `AskUserQuestion`.

**Clarification depth by subtask:**

| Subtask | Depth | What to clarify |
|---------|-------|-----------------|
| Sub1 | **Detailed** | Requirements, edge cases, file locations, naming, test strategy |
| Sub2 | Light | High-level approach, dependencies on Sub1 output |
| Sub3 | Light | Integration points, final acceptance criteria |

Example questions:
- Sub1: "Should User model include email validation? Where should it live?"
- Sub2: "Sub2 will use bcrypt - any preference on salt rounds?"
- Sub3: "Sub3 integrates middleware - should it also add rate limiting?"

**Skip clarification if:**
- Card requirements are explicit and unambiguous
- Technical decisions are standard (use card's ## Technical section)

**3B.3 Present Decomposition Plan**

Output for user validation:

```text
┌─────────────────────────────────────────────┐
│ DECOMPOSITION PLAN                          │
├─────────────────────────────────────────────┤
│ Parent Card: [name]                         │
│ Estimated LOC: [N] (threshold: 50)          │
├─────────────────────────────────────────────┤
│ SUB1: [title]                               │
│ Goal: [atomic goal]                         │
│ LOC estimate: ~[N]                          │
│ Produces: [artifacts for Sub2]              │
├─────────────────────────────────────────────┤
│ SUB2: [title]                               │
│ Goal: [atomic goal]                         │
│ Requires: [artifacts from Sub1]             │
│ LOC estimate: ~[N]                          │
│ Produces: [artifacts for Sub3]              │
├─────────────────────────────────────────────┤
│ SUB3: [title]                               │
│ Goal: [atomic goal]                         │
│ Requires: [artifacts from Sub2]             │
│ LOC estimate: ~[N]                          │
│ Produces: [final deliverables]              │
└─────────────────────────────────────────────┘
```

Output: `--- WAITING FOR DECOMPOSITION APPROVAL ---`

Wait for user approval before proceeding.

**3B.4 Write All Subtask Cards**

After approval, create all 3 cards using naming convention:

If parent is `ecom-1.user-mgmt.md`, children are:
- `ecom-1.user-mgmt-1.model.md`
- `ecom-1.user-mgmt-2.auth.md`
- `ecom-1.user-mgmt-3.profile.md`

Card template:

```markdown
# ecom-1.user-mgmt-1.model

## Parent
ecom-1.user-mgmt

## Goal
[Atomic goal]

## Requirements
- [specific]

## Test
1. [verification]

## Produces (for -2.auth)
- [artifact 1]
- [artifact 2]
```

**3B.5 Execute Sub1 (Isolated)**

```bash
claude -p "Run /ddr workflow on: .claude/pm/[epic]/[card]-1.[name].md
Output DDR_RESULT when done." \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  --print
```

**On SUCCESS**: Commit immediately
```bash
git add -A && git commit -m "WIP: [card]-1.[name]"
```

**On FAILURE**: Rollback
```bash
git reset --hard HEAD
```

**3B.6 PRECONDITION_CHECK for Sub2**

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

**3B.7 Execute Sub2, then Sub3**

Repeat 3B.5-3B.6 for Sub2, then Sub3.

---

## Phase 4: REFLECT_SPLIT (WF3 Failed)

**4.1 Capture Reflection**

```text
┌─────────────────────────────────────────────┐
│ FAILURE_REFLECTION                          │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Attempts: [N]                               │
│ Reason: [from WF3]                           │
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

## Phase 6: LOGGING (Required)

**Every DDR execution MUST log and update the card.**

**6.1 Write Log File**

Create `.claude/temp/ddr-[card].log` with full execution trace:

```bash
# Log file structure
mkdir -p .claude/temp
cat >> .claude/temp/ddr-[card].log << 'EOF'
================================================================================
DDR EXECUTION: [card]
STARTED: [timestamp]
DEPTH: [N]
================================================================================

[CONTEXT_SCAN output]
[COMPLEXITY_SCORE output]
[DECISION: DELEGATE or DECOMPOSE]

--- EXECUTION ---
[All tool calls and outputs]
[WF3_RESULT or subtask results]

--- RESULT ---
[DDR_RESULT block]

FINISHED: [timestamp]
================================================================================
EOF
```

**6.2 Append to Card**

Append execution summary to the original card:

```bash
cat >> .claude/pm/[card].md << 'EOF'

---

## Execution Log

| Run | Date | Status | Artifacts |
|-----|------|--------|-----------|
| 1 | [date] | [SUCCESS/FAILURE] | [files] |

### How to Verify
```bash
[test command, e.g., npm test]
```

### Reflection
[What was learned, issues encountered]
EOF
```

**6.3 Final User Output**

After completion, ALWAYS output:

```text
┌─────────────────────────────────────────────┐
│ DDR COMPLETE                                │
├─────────────────────────────────────────────┤
│ Card: [name]                                │
│ Status: [SUCCESS|FAILURE]                   │
│ Log: .claude/temp/ddr-[card].log            │
├─────────────────────────────────────────────┤
│ HOW TO VERIFY:                              │
│ $ [test command]                            │
│ $ [additional commands if needed]           │
├─────────────────────────────────────────────┤
│ ARTIFACTS CREATED:                          │
│ • [file 1]                                  │
│ • [file 2]                                  │
└─────────────────────────────────────────────┘
```

---

## State Tracking

Every response starts with:

```text
[DDR] Card: [name] | Depth: [N] | LOC: [N] | Status: [phase]
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
| Max depth | 2 | STOP - scope too big, ask user to split epic |
| Max subtasks | 9 | STOP, too complex (3×3 max) |
| WF3 failures | 2 per card | Reflect + split |

**Why max depth 2?** Industry best practice (NASA, PMI) recommends 3-5 WBS levels. L0=Epic, L1=Feature, L2=Subtask. If L2 needs splitting, the original card scope was too ambitious.

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No PM folder | Create `.claude/pm/[epic]/` |
| Card not found | List available |
| Depth > 2 | STOP - "Scope too large, split epic first" |
| WF3 fails 2x | Reflect + split |
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
