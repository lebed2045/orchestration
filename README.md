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

## Why Workflows?

**The Problem**: Claude reviews its own work. It knows why it wrote the code, so it's biased toward believing it works. Tests can be self-fulfilling. "Done" gets claimed without proof.

**The Solution**: External reviewers with zero context:
- **Gemini** and **Codex** review via MCP tools
- **Fresh Claude** subprocess reviews without implementation history

Plus enforcement of:
- **TDD** - Write failing tests first, then implement
- **Proof blocks** - EXECUTION_BLOCK, REGRESSION_DELTA required
- **Gates** - Review checkpoints that must pass

---

## Choosing a Workflow

| If You Need | Use | Why |
|-------------|-----|-----|
| Maximum safety | `/wf3` | Anti-regression, smoke tests, baseline tracking |
| Fastest execution | `/wf8` | Fully autonomous, auto-commits, no human gates |
| Budget-friendly | `/wf7` | 75% fewer tokens than wf6, parallel reviews |
| Most thorough review | `/wf6` | Quad review (4 reviewers) + retrospective |
| Large features | `/ddr2` | Auto-splits into subtasks, recursive execution |
| Learning the system | `/wf1` | Simplest, orchestrator implements directly |

---

## Available Workflows

| Command | Phases | Gates | Human Gates | Reviewers | Key Feature |
|---------|--------|-------|-------------|-----------|-------------|
| `/wf1` | 8 | 1 | 1 | Gemini | Basic, orchestrator implements |
| `/wf2` | 10 | 3 | 1 | Gemini + Claude | Isolated coder |
| `/wf3` | 10 | 3 | 1 | Gemini + Claude | Anti-regression baseline |
| `/wf4` | 8 | 2 | **0** | Gemini + Codex + Claude | Autonomous, auto-fix |
| `/wf5` | 10 | 3 | 1 | Gemini + Codex + Claude | Triple review Gate 1 |
| `/wf6` | 10 | 3 | 1 | Gemini + Codex + Opus + Sonnet | Quad review + retrospective |
| `/wf7` | 9 | 2 | 1 | Codex + Gemini | Token-optimized (75% less) |
| `/wf8` | 8 | 2 | **0** | Codex + Gemini | Fully autonomous, auto-commit |
| `/ddr` | meta | - | 2 | uses wf3 | PM card orchestrator |
| `/ddr2` | meta | - | **0** | uses wf8 | Autonomous DDR, auto-splits |

---

## Workflow Families

### Standard (Human-in-the-Loop)

**wf1** → **wf2** → **wf3**: Progressive rigor

| Feature | wf1 | wf2 | wf3 |
|---------|-----|-----|-----|
| Isolated coder | No | Yes | Yes |
| Dual review | No | Yes | Yes |
| Baseline capture | No | No | Yes |
| Regression tracking | No | No | Yes |
| Smoke testing | No | No | Yes |

**Use wf3** for production code. It prevents the "five sins":
1. Claiming "done" without testing
2. No actual play-testing
3. Self-fulfilling tests
4. Fix-break cycle
5. Ignoring warnings

### High-Assurance (Heavy Review)

**wf5** and **wf6**: More reviewers catch more issues

| Feature | wf5 | wf6 |
|---------|-----|-----|
| Plan reviewers | 3 (Gemini + Codex + Claude) | 4 (+ Opus + Sonnet) |
| Test reviewers | 2 | 4 |
| Code reviewers | 2 | 4 |
| Retrospective | No | Yes |
| Token cost | High | Very High |

**Use wf6** when getting it right matters more than speed.

### Autonomous / Fast

**wf4**, **wf7**, **wf8**: Minimal human interaction

| Feature | wf4 | wf7 | wf8 |
|---------|-----|-----|-----|
| Human gates | 0 | 1 | **0** |
| Auto-commit | No | No | **Yes** |
| Token usage | High | **Low** | **Low** |
| Infer requirements | Yes | No | Yes |
| Auto-fix on feedback | Yes | No | Yes |

**Use wf8** for chores, prototypes, or isolated tasks.
**Use wf7** when you want review but need to save tokens.

### Meta-Orchestrators (DDR)

For large features that need decomposition.

| Feature | /ddr | /ddr2 |
|---------|------|-------|
| Delegates to | wf3 | wf8 |
| Human gates | 2 | **0** |
| Auto-commit | No | **Yes** |
| Split factor | Fixed 3 | Dynamic 2-5 |
| Failure mode | Manual | Safe (git stash) |
| Context sharing | None | ddr2-context.md |

**DDR flow**:
1. Read PM card from `.claude/pm/`
2. Estimate LOC
3. If ≤50 LOC → delegate to workflow
4. If >50 LOC → decompose into subtasks
5. On failure → reflect, split smaller, recurse

---

## Quick Start

```bash
# Basic task
/wf3 Add user authentication with JWT tokens

# Autonomous task
/wf8 Fix the typo in the README

# Large feature via DDR
/ddr2 02-auth-system
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

---

## File Structure

```
.claude/
├── commands/
│   ├── wf1.md            # Basic workflow
│   ├── wf2.md            # Dual review
│   ├── wf3.md            # Anti-regression
│   ├── wf4.md            # Autonomous
│   ├── wf5.md            # Triple review
│   ├── wf6.md            # Quad review + retrospective
│   ├── wf7.md            # Token-optimized
│   ├── wf8.md            # Fully autonomous
│   ├── ddr.md            # Meta-orchestrator
│   └── ddr2.md           # Autonomous DDR
├── agents/
│   ├── *-v1.md           # Agents for wf1
│   ├── *-v3.md           # Agents for wf3, wf5, wf6
│   └── *-v4.md           # Agents for wf4
├── pm/                   # PM cards for DDR
└── temp/                 # Generated during execution (gitignored)
```

---

## Forbidden Phrases

These words are BLOCKED without preceding proof blocks:

- "Done" / "Fixed" / "Complete"
- "Tests pass" / "Should work"
- "I verified" / "I tested"

Replace with: "Running verification now..." then show actual output.

---

## Full Comparison

| Feature | wf1 | wf2 | wf3 | wf4 | wf5 | wf6 | wf7 | wf8 |
|---------|-----|-----|-----|-----|-----|-----|-----|-----|
| **Phases** | 8 | 10 | 10 | 8 | 10 | 10 | 9 | 8 |
| **Gates** | 1 | 3 | 3 | 2 | 3 | 3 | 2 | 2 |
| **Human gates** | 1 | 1 | 1 | 0 | 1 | 1 | 1 | **0** |
| **Auto-commit** | No | No | No | No | No | No | No | **Yes** |
| Isolated coder | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Baseline capture | No | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Regression tracking | No | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Smoke testing | No | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Gemini review | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Codex review | No | No | No | Yes | G1 | Yes | Yes | Yes |
| Auto-fix on feedback | No | No | No | Yes | No | No | No | Yes |
| Infer requirements | No | No | No | Yes | No | No | No | Yes |
| **Token cost** | Low | Med | Med | High | High | **Very High** | **Low** | **Low** |
| **Autonomy** | Low | Med | Med | High | Med | Med | Med | **Full** |

---

## License

MIT
