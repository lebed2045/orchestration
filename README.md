# Orchestration Workflows

Development workflows that extend Claude Code with external review, TDD enforcement, and anti-regression guarantees.

---

## Quick Install (Set It and Forget It)

Open Claude Code in your project and paste:

```
Check the repo https://github.com/lebed2045/orchestration - adopt it for my workflow, review all files in my project and this repo, interview me with questions, install globally (~/.claude/)
```

Claude will:
1. Review this repo and your project structure
2. Ask clarifying questions about your preferences
3. Install workflows globally to `~/.claude/commands/`

---

## What's In This Repository

| Component | What It Does |
|-----------|--------------|
| **Workflows (wf1-wf9)** | Multi-phase pipelines with review gates, TDD enforcement, proof blocks |
| **External Reviewers** | Gemini, Codex, isolated Claude — zero-context reviewers catch what author misses |
| **Clean Context Agents** | Coders spawned via `claude -p` with ZERO planning context — only see spec |
| **TDD Enforcement** | RED phase (tests fail) → GREEN phase (tests pass) — no skipping |
| **Project Manager (DDR/DDR2)** | Meta-orchestrator that recursively splits tasks, delegates to workflows, and if it fails — splits into smaller subtasks and tries again |

---

## Why Workflows?

Claude Code has two default modes: **Plan** (design approach, get approval) and **Execute** (write code). This works but has blind spots.

**The Problem**: Claude reviews its own work. It knows why it wrote the code, so it's biased toward believing it works. Tests can be self-fulfilling (written to pass, not to verify). Warnings get ignored. "Done" gets claimed without proof.

**The Solution**: Add external reviewers who have zero context:
- **Gemini** reviews artifacts via MCP tool
- **Codex** reviews via MCP tool
- **Fresh Claude** subprocess (`claude -p`) reviews code without knowing implementation history

This catches what the original author misses.

Workflows also enforce:
- **TDD** - Write failing tests first, then implement
- **Proof blocks** - EXECUTION_BLOCK, REGRESSION_DELTA required before completion claims
- **Gates** - Multiple review checkpoints that must pass

---

## Available Workflows

| Command | Phases | Gates | Human Gates | Reviewers | Description |
|---------|--------|-------|-------------|-----------|-------------|
| `/wf1-gh` | 8 | 1 | 1 | Gemini | Basic workflow, orchestrator implements |
| `/wf2-gh` | 10 | 3 | 2 | Gemini + Claude | Dual review + isolated coder |
| `/wf3-gh` | 10 | 3 | 1 | Gemini + Claude | Anti-regression (baseline, smoke test) |
| `/wf4-gc` | 8 | 2 | 0 | Gemini + Codex + Claude | Autonomous (infer, auto-fix, triple review) |
| `/wf5-gch` | 10 | 3 | 1 | Gemini + Codex + Claude | wf3 + Codex (triple review in Gate 1) |
| `/wf6-gch` | 10 | 3 | 1 | Gemini + Codex + Opus + Sonnet | Quad review + retrospective analysis |
| `/wf7-gch` | 9 | 2 | 1 | Codex + Gemini | Token-optimized, parallel reviews |
| `/wf8-gc` | 8 | 2 | **0** | Codex + Gemini | Fully autonomous wf7, auto-commits |
| `/wf9-gc` | 10 | 2 | 0 | Codex + Gemini + Agent Teams | Boris Mode + Reflections log |
| `/wf10-gc` | 10 | 2 | 0-1 | Codex + Gemini | wf9 + optional `-h` flag |
| `/boris1-h` | - | 0 | 1 | — | Boris's original (plan iteration) |
| `/boris2` | 10 | 2 | 0 | 2×Opus | Boris + Agent Teams (auto) |
| `/ddr` | - | - | 2 | uses wf3-gh | Meta-orchestrator for PM cards |
| `/ddr2` | - | - | **0** | uses wf8-gc | Autonomous DDR, auto-splits, auto-commits |

---

## Quick Start

```bash
# Run workflow 3 with a task
/wf3-gh Add user authentication with JWT tokens

# Run DDR on a PM card
/ddr 02-auth-system
```

---

## Workflow Details

### /wf1-gh - Basic Workflow (8 phases)

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
/wf1-gh Add a logout button to the header
```

---

### /wf2-gh - Dual Review Workflow (10 phases)

Adds isolated coder and dual reviewers at each gate.

**Key difference from wf1-gh**: The coder is spawned via `claude -p` subprocess with ZERO context from planning. It only reads spec.md and architecture.md. This prevents the coder from implementing rejected ideas or getting confused by planning discussions.

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
/wf2-gh Implement rate limiting for API endpoints
```

---

### /wf3-gh - Anti-Regression Workflow (10 phases, 3 gates)

The most rigorous workflow. Everything from wf2-gh plus anti-regression tracking.

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
/wf3-gh Fix the authentication bypass vulnerability in login flow
```

---

### /wf4-gc - Autonomous Workflow (8 phases, 2 gates)

Maximum autonomy. Infers requirements from codebase, auto-fixes on review feedback.

**Philosophy**:

| Old Behavior (wf1-3-gh) | New Behavior (wf4-gc) |
|----------------------|-------------------|
| Ask about inputs/outputs/edge cases | Infer from codebase + task |
| "Should I update the plan?" | Just update it |
| "Should I proceed?" | Proceed unless blocked |
| Wait for approval at every gate | Auto-approve after triple review |

**Key features**:
- **Triple review**: Gemini + Codex + Isolated Claude
- **Auto-fix loops**: On NEEDS_WORK, update and re-run reviewers (no asking)
- **Inferred requirements**: Reads codebase patterns instead of asking questions
- **0-1 human interactions** typical (vs 3-5 in wf3-gh)

**Human involvement only for**:
1. Multiple valid approaches with significant trade-offs
2. Destructive operations (delete files, breaking changes)
3. Ambiguity that cannot be resolved from codebase
4. Circuit breaker activated (2x same error)

**Flow**:
1. Baseline Capture
2. Autonomous Intake - Infer requirements, document assumptions
3. Autonomous Planning - Design architecture
4. **GATE 1: Triple Review Plan** - Gemini + Codex + Claude (auto-fix loop)
5. TDD Red - Write failing tests
6. TDD Green - Implement
7. **GATE 2: Triple Review Code** - Gemini + Codex + Claude (auto-fix loop)
8. Completion

**Agents**: `intake-v4`, `planner-v4`, `coder-v4`, `fresh-reviewer-v4`

```bash
/wf4-gc Add caching to the API endpoints
```

---

### /wf5-gch - Triple Review Workflow (10 phases, 3 gates)

Based on wf3-gh with Codex added as third reviewer in Gate 1 (Plan review).

**Key difference from wf3-gh**: Adds Codex reviewer to Gate 1 for triple review of the plan. Gates 2 and 3 remain dual review.

**Flow**: Same as wf3-gh, but Phase 4 has three reviewers:
- Gemini reviews spec + architecture
- Codex reviews spec + architecture
- Isolated Claude reviews spec + architecture

All three must return APPROVED before proceeding to user approval.

**When to use**: When you want wf3-gh's rigor but with an additional AI perspective on the plan.

**Agents**: Uses `*-v3` agents (same as wf3)

```bash
/wf5-gch Implement OAuth2 flow with refresh tokens
```

---

### /wf6-gch - Quad Review Workflow (10 phases, 3 gates)

The most thorough review workflow with 4 reviewers at each gate plus retrospective analysis.

**Key features**:
- **Quad review**: Gemini + Codex + Opus + Sonnet at each gate
- **Retrospective analysis**: After completion, analyzes which reviewers caught what
- **High token cost**: Use for critical code where review quality > token efficiency

**Reviewers**:
| Reviewer | Strengths |
|----------|-----------|
| Gemini | Fast, catches structural issues |
| Codex | Thorough, catches subtle bugs |
| Opus | Deep reasoning, architectural concerns |
| Sonnet | Quick sanity check, obvious errors |

**Flow**: Same as wf3-gh, but each gate has 4 reviewers instead of 2.

**When to use**: Security-critical code, complex refactors, anything where getting it right matters more than speed.

```bash
/wf6-gch Implement payment processing with PCI compliance
```

---

### /wf7-gch - Token-Optimized Workflow (9 phases, 2 gates)

Optimized for token efficiency with parallel test writing.

**Key features**:
- **Parallel TDD_RED**: Orchestrator + Codex write tests independently, then merge
- **No test review gate**: Same prompt = no review needed
- **CodeSmell + Codex** for code review
- **75% fewer reviewer calls** than wf6 (3 vs 12)

**Reviewers per gate**:
| Phase | wf7 | wf6 | Savings |
|-------|-----|-----|---------|
| Gate 1 (Plan) | 2 (Codex+Gemini) | 4 | 50% |
| Gate 2 (Tests) | 0 (no review) | 4 | 100% |
| Gate 3 (Code) | 1 (Codex) + CodeSmell | 4 | 75% |
| **Total** | **3** | **12** | **75%** |

**When to use**: Budget-conscious projects, rapid iteration, prototypes.

```bash
/wf7-gch Add logging middleware to API
```

---

### /wf8-gc - Fully Autonomous Workflow (8 phases, 2 gates)

wf7-gch without human gates. Fully autonomous with auto-commit.

**Key features**:
- **0 human gates**: Runs to completion without user interaction
- **Auto-commit**: Commits each successful change automatically
- **Infer requirements**: Like wf4, reads codebase instead of asking
- **Auto-fix on feedback**: On NEEDS_WORK, updates and re-runs reviewers
- **Like wf4-gc**: Reads codebase instead of asking

**Human involvement only for**:
1. MANUAL_INTERVENTION signal from circuit breaker
2. Missing tooling/dependency that can't be inferred
3. Destructive operations requiring explicit approval

**When to use**: Chores, isolated tasks, batch processing multiple small changes.

```bash
/wf8-gc Fix the typo in the README
```

---

### /wf9-gc - Boris Mode + Agent Teams (10 phases, 2 gates)

Based on Boris Cherny's (Claude Code creator) actual workflow patterns + Agent Teams for parallel execution.

**Philosophy**: *"A good plan is really important"* + *"Give Claude a way to verify its work — quality improves 2-3x"*

**Key features**:
- **Plan Mode iteration**: Go back and forth until plan is solid (Boris pattern)
- **DETECT_ENV phase**: Reads CLAUDE.md for test/build commands (no hardcoded `npm test`)
- **Agent Teams**: Spawn parallel teammates for TDD_RED with file ownership
- **code-simplifier**: Post-implementation cleanup (Boris subagent pattern)
- **verify-app**: Full E2E verification before completion
- **Reflections log**: On failure/success, logs to `.claude/reflections.md` (human-readable)
- **0 human gates**: Fully autonomous (like wf8-gc)

**Agent Team spawn example**:
```text
Create a team for TDD_RED:
- Teammate 1: tests/unit/auth.test.ts
- Teammate 2: tests/unit/api.test.ts
- Teammate 3: tests/integration/
All must show EXECUTION_BLOCK with EXIT_CODE≠0
```

**Boris prompting patterns baked in**:
- "Grill me on these changes"
- "Prove to me this works"
- "Knowing everything you know now, implement the elegant solution"

**When to use**: Complex features needing parallel exploration, projects with specific CLAUDE.md rules, when plan quality matters.

```bash
/wf9-gc Implement OAuth2 flow with parallel test exploration
```

---

### /ddr - Divide Delegate Reflect

A meta-workflow for processing PM cards. It doesn't implement directly - it orchestrates /wf3-gh.

**How it works**:

1. **Read PM Card** - Load card from `.claude/pm/` folder
2. **Estimate LOC** - How many lines of code needed?
3. **Decision**:
   - If LOC ≤ 50 → Delegate directly to /wf3-gh
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
# 4. Either delegate to /wf3-gh or decompose
```

**Decomposition example**:

If `02-auth-system` estimates 150 LOC, DDR creates:
- `02-auth-system-sub1.md` - User model + password hashing
- `02-auth-system-sub2.md` - JWT generation + validation
- `02-auth-system-sub3.md` - Endpoints + middleware integration

Each subtask runs through /wf3-gh independently. Sub2 waits for Sub1's artifacts.

**Limits**:
- Max depth: 5 (nested decompositions)
- Max subtasks: 15 total
- WF3 failures: 2 per card before reflect+split

---

### /ddr2 - Autonomous DDR

Fully autonomous meta-orchestrator. No human gates, delegates to /wf8-gc.

**Key differences from DDR**:

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

**Flow**:
1. **PREFLIGHT** - Check clean workspace, read CLAUDE.md
2. **DETECT_ENV** - Detect test command from CLAUDE.md (don't let wf8-gc guess)
3. **CARD_INTAKE** - Infer context (no questions)
4. **LOC_ESTIMATE** - Decide delegate or decompose
5. **DELEGATE** or **DECOMPOSE** with context inheritance
6. **REFLECT_SPLIT** on failure (safe mode: git stash)

**Circuit breakers**:
- Workspace not clean → STOP
- wf8-gc returns MANUAL_INTERVENTION → STOP immediately
- Same failure signature 2x → STOP
- MAX_DEPTH (2) exceeded → STOP
- MAX_TOTAL_COMMITS (10) exceeded → STOP
- MAX_TOTAL_LOC (500) exceeded → STOP

```bash
/ddr2 02-auth-system
```

---

## Comparison Table

| Feature | wf1 | wf2 | wf3 | wf4 | wf5 | wf6 | wf7 | wf8 | wf9 |
|---------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| Phases | 8 | 10 | 10 | 8 | 10 | 10 | 9 | 8 | 10 |
| Review gates | 1 | 3 | 3 | 2 | 3 | 3 | 2 | 2 | 2 |
| Human gates | 1 | 1 | 1 | 0 | 1 | 1 | 1 | **0** | 1 |
| Auto-commit | No | No | No | No | No | No | No | **Yes** | No |
| Gemini review | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Codex review | No | No | No | Yes | Gate 1 only | Yes | Yes | Yes | Yes |
| Isolated coder | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Agent Teams** | No | No | No | No | No | No | No | No | **Yes** |
| Reviewers per gate | 1 | 2 | 2 | 3 | 3/2/2 | 4 | 2/0/2 | 2/0/2 | 2/0/2 |
| Baseline capture | No | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Regression tracking | No | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Smoke testing | No | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Auto-fix on feedback | No | No | No | Yes | No | No | No | Yes | No |
| **Plan iteration** | No | No | No | No | No | No | No | No | **Yes** |
| **code-simplifier** | No | No | No | No | No | No | No | No | **Yes** |
| **verify-app** | No | No | No | No | No | No | No | No | **Yes** |
| **Reflections log** | No | No | No | No | No | No | No | No | **Yes** |
| Human interactions | Many | 3-5 | 3-5 | 0-1 | 3-5 | 3-5 | 2-3 | **0** | 1-2 |
| Token cost | Low | Med | Med | High | High | **Very High** | **Low** | **Low** | Med |
| Autonomy level | Low | Medium | Medium | Maximum | Medium | Medium | Medium | **Full** | High |

---

## File Structure

```
.claude/
├── commands/
│   ├── wf1-gh.md         # Basic workflow (8 phases, Gemini + human gate)
│   ├── wf2-gh.md         # Dual review workflow (10 phases)
│   ├── wf3-gh.md         # Anti-regression workflow (10 phases)
│   ├── wf4-gc.md         # Autonomous workflow (Gemini + Codex)
│   ├── wf5-gch.md        # Triple review workflow
│   ├── wf6-gch.md        # Quad review + retrospective
│   ├── wf7-gch.md        # Token-optimized
│   ├── wf8-gc.md         # Fully autonomous (auto-commit)
│   ├── wf9-gc.md         # Boris Mode + Agent Teams
│   ├── wf10-gc.md        # wf9 + optional -h flag
│   ├── boris1-h.md       # Boris's original (human plan iteration)
│   ├── boris2.md         # Boris + Agent Teams (autonomous)
│   ├── ddr.md            # Meta-orchestrator (uses wf3-gh)
│   └── ddr2.md           # Autonomous DDR (uses wf8-gc)
├── agents/
│   ├── *-v1.md           # Agents for wf1
│   ├── *-v3.md           # Agents for wf3, wf5, wf6
│   └── *-v4.md           # Agents for wf4 (autonomous)
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

**REGRESSION_DELTA** (wf3+):
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

- **wf1, wf2, wf3** - Stable, rarely modified
- **wf4** - Autonomous workflow with triple review (Gemini + Codex + Claude)
- **wf5** - wf3 + Codex in Gate 1 (triple review for planning)
- **wf6** - Quad review + retrospective (highest review coverage)
- **wf7** - Token-optimized (75% fewer tokens than wf6)
- **wf8** - Fully autonomous wf7 (no human gates, auto-commit)

This ensures reproducibility. A workflow that worked yesterday works the same today.

---

## License

MIT
