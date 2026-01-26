# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

| Command | Version | Agents | Description |
|---------|---------|--------|-------------|
| `/o1` | v1 | `*-v1` | 8-phase workflow, Gemini review, orchestrator implements |
| `/o2` | v2 | `*-v2` | 10-phase workflow, 3-gate dual-review, isolated coder |
| `/o3` | v3 | `*-v3` | 10-phase, 3-gate, isolated coder + anti-regression (BASELINE, SMOKE_TEST) |

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
│   ├── o1.md             # v1 workflow
│   ├── o2.md             # v2 workflow
│   └── o3.md             # v3 anti-regression workflow
├── agents/
│   ├── *-v1.md           # Agents for o1
│   └── *-v3.md           # Agents for o3
└── settings.local.json   # Hooks configuration
```

**Temporary (gitignored):**

```text
.claude/temp/             # Generated during orchestration
├── spec.md               # Requirements specification
├── architecture.md       # Technical design
├── plan-review.md        # Plan review output
├── test-review.md        # Test review output
└── code-review.md        # Code review output
```

---

## Notes

- Each command file is self-contained with its full workflow
- Do NOT merge instructions from CLAUDE.md with command files
- Follow ONLY the command file when a command is invoked
