# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

Run `/wf` for quick reference table.

### Current

| Command | Description |
|---------|-------------|
| `/wf` | The workflow. Fast TDD on modern primitives (Agent + worktree + tier-auto). Prints `wf v16 (2026-05-26)` as its first line on every invocation. |
| `/sc-audit` | Smart contract audit (6 parallel reviewers + LP scorecard) |
| `/research` (`/r`) | Multi-agent research (codebase + Antigravity + Codex) |
| `/reflect` | Turn failures into rules with escalation ladder |

### Legacy (in `.claude/commands/legacy/`, invoked as `/legacy:<name>`)

`/legacy:wf1-gh` … `/legacy:wf12`, `/legacy:wf14`, `/legacy:wf15`, `/legacy:boris1-h`, `/legacy:boris2`, `/legacy:ddr`, `/legacy:ddr2`. Still runnable; superseded by `/wf`. Don't add new functionality here — promote any keeper to the current set instead.

### Bumping the `/wf` version banner

When the workflow body in `.claude/commands/wf.md` changes meaningfully, update **both** lines at the top of the file:
- `**WF_VERSION:** \`v17\`` (bump from v16)
- `**WF_COMMITTED:** \`YYYY-MM-DD\`` (today's date in ISO)

The mandatory first-line banner the workflow prints is derived from these two values. If they drift apart, the rule fails.

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
│   ├── wf.md             # The workflow (was wf16). Prints version banner on invocation.
│   ├── sc-audit.md       # Smart contract audit
│   ├── r.md, reflect.md  # Research + reflection utilities
│   └── legacy/           # Archived: wf1-wf12, wf14, wf15, boris1-h, boris2, ddr, ddr2
├── agents/
│   ├── simplicity-cop.md, coherence-cop.md, coverage-cop.md   # 3 cops (used by /wf)
│   ├── code-simplifier.md, plan-reviewer.md, verify-app.md    # Used by legacy:boris2
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
