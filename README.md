# Orchestration Workflows

Development workflows that extend Claude Code with external review, TDD enforcement, and anti-regression guarantees.

---

## Why Workflows?

Claude Code has two default modes: **Plan** (design approach, get approval) and **Execute** (write code). This works but has blind spots.

**The Problem**: Claude reviews its own work. It knows why it wrote the code, so it's biased toward believing it works. Tests can be self-fulfilling (written to pass, not to verify). Warnings get ignored. "Done" gets claimed without proof.

**The Solution**: Add external reviewers who have zero context:
- **Gemini** reviews artifacts via MCP tool
- **Fresh Claude** subprocess (`claude -p`) reviews code without knowing implementation history

This catches what the original author misses.

Workflows also enforce:
- **TDD** - Write failing tests first, then implement
- **Proof blocks** - EXECUTION_BLOCK, REGRESSION_DELTA required before completion claims
- **Gates** - Multiple review checkpoints that must pass

---

## Available Workflows

| Command | Description | Best For |
|---------|-------------|----------|
| `/wf1` | Basic workflow with Gemini review | Simple features, learning the system |
| `/wf2` | Dual review + isolated coder | Production code, team standards |
| `/wf3` | Full anti-regression with smoke tests | Critical fixes, zero-tolerance for breakage |
| `/ddr` | Meta-workflow for PM cards | Large features, backlog processing |

---

## Quick Start

```bash
# Run workflow 3 with a task
/wf3 Add user authentication with JWT tokens

# Run DDR on a PM card
/ddr 02-auth-system
```

---

## Workflow Details

### /wf1 - Basic Workflow (8 phases)

The simplest workflow. Orchestrator does the implementation directly.

**Flow**:
1. Intake - Gather requirements, write spec.md
2. Planning - Design architecture.md
3. Gemini Review - External validation of plan
4. User Approval - Gate before coding
5. TDD Red - Write failing tests
6. TDD Green - Implement to pass tests
7. Final Review - Gemini reviews code
8. Completion - With EXECUTION_BLOCK proof

**When to use**: Learning the system, simple features, quick fixes.

**Agents**: `intake-v1`, `planner-v1`, `coder-v1`, `fresh-reviewer-v1`

```bash
/wf1 Add a logout button to the header
```

---

### /wf2 - Dual Review Workflow (10 phases)

Adds isolated coder and dual reviewers at each gate.

**Key difference from wf1**: The coder is spawned via `claude -p` subprocess with ZERO context from planning. It only reads spec.md and architecture.md. This prevents the coder from implementing rejected ideas or getting confused by planning discussions.

**Flow**:
1. Intake - Gather requirements
2. Planning - Design architecture
3. **GATE 1: Plan Review** - Gemini + Isolated Claude review plan
4. User Approval - Present both review verdicts
5. TDD Red - Write failing tests (isolated coder)
6. **GATE 2: Test Review** - Gemini + Isolated Claude validate tests
7. TDD Green - Implement (isolated coder, tests read-only)
8. **GATE 3: Code Review** - Gemini + Isolated Claude review code
9. User Acceptance - Final verification
10. Completion

**When to use**: Production code, anything that needs multiple perspectives.

**Note**: Uses inline prompts, not separate agent files.

```bash
/wf2 Implement rate limiting for API endpoints
```

---

### /wf3 - Anti-Regression Workflow (10 phases, 3 gates)

The most rigorous workflow. Everything from wf2 plus anti-regression tracking.

**Key additions**:
- **BASELINE_BLOCK** - Captured BEFORE any changes (test count, warning count, git SHA)
- **REGRESSION_DELTA** - Compared AFTER every change (must show SAFE)
- **SMOKE_TEST** - Platform-specific verification beyond unit tests
- **WARNING_COUNT** - Any increase in warnings blocks completion

**The Five Sins it prevents**:

| Sin | What it is | How wf3 prevents it |
|-----|------------|---------------------|
| 1 | Claiming "done" without testing | EXECUTION_BLOCK required |
| 2 | No actual play-testing | SMOKE_TEST required |
| 3 | Self-fulfilling tests | BASELINE comparison |
| 4 | Fix-break cycle | REGRESSION_DELTA tracking |
| 5 | Ignoring warnings | WARNING_COUNT must not increase |

**Flow**:
1. **Baseline Capture** - Run tests, count warnings, record git SHA
2. Intake - Gather requirements (includes baseline in spec)
3. Planning - Architecture with regression checkpoints
4. **GATE 1: Plan Review** - Both reviewers check regression strategy
5. User Approval - Full plan summary shown
6. TDD Red - Isolated coder writes failing tests
7. **GATE 2: Test Review** - Validate tests FAIL correctly (RED phase)
8. TDD Green - Isolated coder implements (tests read-only)
9. **GATE 3: Code Review + Smoke** - Both reviewers + REGRESSION_DELTA + SMOKE_TEST
10. Completion - With WF3_RESULT block

**Agents**: `intake-v3`, `planner-v3`, `coder-v3`, `fresh-reviewer-v3`

**Circuit breakers**:
- Same error 2x → STOP, escalate
- Tests fail 5x → MANUAL INTERVENTION REQUIRED
- Review fails 3x → REVIEW LOOP EXCEEDED
- REGRESSION detected → STOP, fix regression first
- Warnings increased → STOP, fix warnings first

```bash
/wf3 Fix the authentication bypass vulnerability in login flow
```

---

### /ddr - Divide Delegate Reflect

A meta-workflow for processing PM cards. It doesn't implement directly - it orchestrates /wf3.

**How it works**:

1. **Read PM Card** - Load card from `.claude/pm/` folder
2. **Estimate LOC** - How many lines of code needed?
3. **Decision**:
   - If LOC ≤ 50 → Delegate directly to /wf3
   - If LOC > 50 → Decompose into 3 subtasks
4. **On failure** → Reflect on what went wrong, split differently, recurse

**PM Card Format** (in `.claude/pm/`):

```markdown
# 02: Auth System

## Goal
User authentication with JWT tokens

## Requirements
- Login endpoint
- Token refresh
- Logout invalidation

## Technical
Use bcrypt for passwords, jsonwebtoken for JWT

## Test
1. Login returns valid JWT
2. Expired token gets 401
3. Refresh extends session
```

**Running DDR**:

```bash
# List available cards
/ddr

# Work on specific card
/ddr 02-auth-system

# DDR will:
# 1. Read the card
# 2. Ask clarifying questions (DoD, scope)
# 3. Estimate complexity
# 4. Either delegate to /wf3 or decompose
```

**Decomposition example**:

If `02-auth-system` estimates 150 LOC, DDR creates:
- `02-auth-system-sub1.md` - User model + password hashing
- `02-auth-system-sub2.md` - JWT generation + validation
- `02-auth-system-sub3.md` - Endpoints + middleware integration

Each subtask runs through /wf3 independently. Sub2 waits for Sub1's artifacts.

**Limits**:
- Max depth: 5 (nested decompositions)
- Max subtasks: 15 total
- WF3 failures: 2 per card before reflect+split

---

## Comparison Table

| Feature | wf1 | wf2 | wf3 | ddr |
|---------|-----|-----|-----|-----|
| Phases | 8 | 10 | 10 | Recursive |
| Review gates | 1 | 3 | 3 | Uses wf3 |
| Gemini review | Yes | Yes | Yes | Yes |
| Isolated coder | No | Yes | Yes | Yes |
| Dual reviewers | No | Yes | Yes | Yes |
| Baseline capture | No | No | Yes | Yes |
| Regression tracking | No | No | Yes | Yes |
| Smoke testing | No | No | Yes | Yes |
| Warning tracking | No | No | Yes | Yes |
| Auto-decomposition | No | No | No | Yes |
| PM card support | No | No | No | Yes |

---

## File Structure

```
.claude/
├── commands/
│   ├── wf1.md            # Basic workflow
│   ├── wf2.md            # Dual review workflow
│   ├── wf3.md            # Anti-regression workflow
│   └── ddr.md            # Meta-orchestrator
├── agents/
│   ├── intake-v1.md      # Requirements (wf1)
│   ├── planner-v1.md     # Architecture (wf1)
│   ├── coder-v1.md       # TDD implementation (wf1)
│   ├── fresh-reviewer-v1.md  # Code review (wf1)
│   ├── intake-v3.md      # Requirements + baseline (wf3)
│   ├── planner-v3.md     # Architecture + regression strategy (wf3)
│   ├── coder-v3.md       # TDD + regression tracking (wf3)
│   └── fresh-reviewer-v3.md  # Review + regression check (wf3)
├── pm/                   # PM cards for DDR
│   ├── 01-feature.md
│   └── 02-auth-system.md
└── temp/                 # Generated during execution (gitignored)
    ├── spec.md
    ├── architecture.md
    ├── plan-review.md
    ├── test-review.md
    └── code-review.md
```

---

## Proof Blocks

All workflows require proof before completion claims.

**EXECUTION_BLOCK** (all workflows):
```
┌─────────────────────────────────────────────┐
│ EXECUTION_BLOCK                             │
├─────────────────────────────────────────────┤
│ $ npm test                                  │
│ [actual output - last 10+ lines]            │
│ EXIT_CODE: 0                                │
│ TIMESTAMP: 2024-01-26 14:30:00              │
└─────────────────────────────────────────────┘
```

**REGRESSION_DELTA** (wf3 only):
```
┌─────────────────────────────────────────────┐
│ REGRESSION_DELTA                            │
├─────────────────────────────────────────────┤
│ Tests: 45 passed (was 42) [+3]              │
│ Warnings: 2 (was 2) [+0]                    │
│ VERDICT: SAFE                               │
└─────────────────────────────────────────────┘
```

**WF3_RESULT** (wf3 completion):
```
┌─────────────────────────────────────────────┐
│ WF3_RESULT                                  │
├─────────────────────────────────────────────┤
│ Task: Add JWT authentication                │
│ Status: SUCCESS                             │
│ Artifacts: src/auth.ts, tests/auth.test.ts  │
│ Tests: 12 passed, 0 failed                  │
│ Regression: SAFE                            │
│ Reflection: TDD approach caught edge case   │
│ Blocker: none                               │
│ TIMESTAMP: 2024-01-26 14:30:00              │
└─────────────────────────────────────────────┘
```

---

## Forbidden Phrases

These words are BLOCKED without preceding proof blocks:

- "Done" / "Fixed" / "Complete"
- "Tests pass" / "Should work"
- "I verified" / "I tested"
- "The issue is resolved"

Replace with: "Running verification now..." then show actual output.

---

## Version Policy

- **wf1, wf2** - Frozen, never modified
- **wf3** - Current experimental version
- **Future** - New features become wf4, wf5, etc.

This ensures reproducibility. A workflow that worked yesterday works the same today.
