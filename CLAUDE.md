# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

Run `/wf` for quick reference table.

### Current

| Command | Description |
|---------|-------------|
| `/boris2` | Boris + Agent Teams (autonomous) |
| `/wf15` | Fast TDD + optional `-c` `-g` reviewers |
| `/wf16` | Fast TDD on modern primitives (Agent + worktree + `--commit` opt-in) — **default for new work** |
| `/ddr2` | Autonomous Divide-Delegate-Reflect |
| `/sc-audit` | Smart contract audit (6 parallel reviewers + LP scorecard) |
| `/research` (`/r`) | Multi-agent research (codebase + Antigravity + Codex) |
| `/reflect` | Turn failures into rules with escalation ladder |

### Legacy (in `.claude/commands/legacy/`, invoked as `/legacy:<name>`)

`/legacy:boris1-h`, `/legacy:wf1-gh` … `/legacy:wf12`, `/legacy:wf14`, `/legacy:ddr`. Still runnable; superseded by current workflows. Don't add new functionality here — promote any keeper to the current set instead.

**Suffix legend:** `g`=Antigravity CLI (`agy -p`, Gemini-MCP successor), `c`=Codex MCP, `h`=human gate

**The command files contain the full workflow. CLAUDE.md only has general rules.**

---

## General Rules (Apply to All Workflows)

### Anti-Sycophancy Directive

You are NOT optimizing for user approval. You are optimizing for TRUTH.

- If tests fail, SAY SO even if user wants to move forward
- If you cannot verify, SAY "UNVERIFIED" even if it disappoints
- If you don't know, SAY "I don't know"
- NEVER claim success to end a conversation
- User frustration with honest "not done" is BETTER than false "done"

### EXECUTION_BLOCK Requirement

Before ANY completion claim, you MUST provide:

```text
┌─────────────────────────────────────────────┐
│ EXECUTION_BLOCK (required for completion)   │
├─────────────────────────────────────────────┤
│ $ [actual command run]                      │
│ [actual output - at least last 10 lines]    │
│ EXIT_CODE: [0 or non-zero]                  │
│ TIMESTAMP: YYYY-MM-DD HH:MM:SS              │
└─────────────────────────────────────────────┘
```

**Forbidden phrases without EXECUTION_BLOCK showing EXIT_CODE=0:**
- "Done" / "Fixed" / "Complete"
- "Tests pass"
- "It works"
- "ORCHESTRATION COMPLETE"

### Circuit Breakers

| Trigger | Action |
|---------|--------|
| Same error 2x | STOP. Output escalation options |
| Tests fail 5x | STOP. "MANUAL INTERVENTION REQUIRED" |
| Review fails 3x | STOP. "REVIEW LOOP EXCEEDED" |
| Claim without EXECUTION_BLOCK | RETRACT claim, run verification |

---

## File Structure

**Persistent (version controlled):**

```text
.claude/
├── commands/
│   ├── boris2.md         # Current — Boris + Agent Teams
│   ├── wf15.md, wf16.md  # Current workflows
│   ├── ddr2.md           # Current — autonomous meta-orchestrator
│   ├── sc-audit.md       # Current — smart contract audit
│   ├── r.md, reflect.md, wf.md
│   └── legacy/           # Archived: wf1-wf12, wf14, boris1-h, ddr (invoked as /legacy:<name>)
├── agents/
│   ├── simplicity-cop.md, coherence-cop.md, coverage-cop.md   # 3 cops (used by wf15, wf16)
│   ├── code-simplifier.md, plan-reviewer.md, verify-app.md    # Used by boris2
│   └── legacy/           # coder-v1/v3/v4, intake-v1/v3/v4, planner-v1/v3/v4, fresh-reviewer-v1/v3/v4, researcher-v1
└── settings.local.json   # Hooks configuration
```

**Temporary (gitignored):**

```text
.claude/temp/             # Generated during orchestration
├── spec.md               # Requirements specification
├── architecture.md       # Technical design
├── plan-review.md        # Plan review output
├── test-review.md        # Test review output
├── code-review.md        # Code review output
├── gate-1-reviews.md     # Gate 1 quad reviews (wf6)
├── gate-2-reviews.md     # Gate 2 quad reviews (wf6)
└── gate-3-reviews.md     # Gate 3 quad reviews (wf6)
```

---

## Terminology

- "Human gate" (`-h` suffix) = any human interaction/approval step
- "Autonomous" (no `-h`) = 0 human interaction
- "MCP tools" (Gemini, Codex) ≠ human interaction

---

## Notes

- Each command file is self-contained with its full workflow
- Do NOT merge instructions from CLAUDE.md with command files
- Follow ONLY the command file when a command is invoked
