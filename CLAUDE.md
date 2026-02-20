# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

Run `/wf` for quick reference table.

| Command | Suffix | Description |
|---------|--------|-------------|
| `/boris1-h` | `-h` | Boris's original workflow (human plan iteration) |
| `/boris2` | — | Boris + Agent Teams (autonomous) |
| `/wf1-gh` | `-gh` | v1: Gemini + human gate |
| `/wf2-gh` | `-gh` | v2: Dual review + isolated coder + human gate |
| `/wf3-gh` | `-gh` | v3: Anti-regression + human gate |
| `/wf4-gc` | `-gc` | v4: Gemini + Codex (autonomous) |
| `/wf5-gch` | `-gch` | v5: Triple review + human gate |
| `/wf6-gch` | `-gch` | v6: Quad review + human gate |
| `/wf7-gch` | `-gch` | v7: Token-optimized + human gate |
| `/wf8-gc` | `-gc` | v8: Autonomous + auto-commit |
| `/wf9-gc` | `-gc` | v9: MCP tools + auto-commit |
| `/wf10-gc` | `-gc` | v10: wf9 + optional `-h` flag for human gate |
| `/ddr` | — | Meta-orchestrator (uses wf3-gh) |
| `/ddr2` | — | Autonomous DDR (uses wf8-gc) |

**Suffix legend:** `g`=Gemini, `c`=Codex, `h`=human gate

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
│   ├── boris1-h.md       # Boris's original (human plan iteration)
│   ├── boris2.md         # Boris + Agent Teams (autonomous)
│   ├── wf1-gh.md         # v1 (Gemini + human)
│   ├── wf2-gh.md         # v2 (Gemini + human)
│   ├── wf3-gh.md         # v3 anti-regression
│   ├── wf4-gc.md         # v4 autonomous
│   ├── wf5-gch.md        # v5 triple review
│   ├── wf6-gch.md        # v6 quad review
│   ├── wf7-gch.md        # v7 token-optimized
│   ├── wf8-gc.md         # v8 autonomous
│   ├── wf9-gc.md         # v9 MCP tools
│   ├── wf10-gc.md        # v10 (wf9 + optional -h flag)
│   ├── wf.md             # Quick reference table
│   ├── ddr.md            # Meta-orchestrator
│   └── ddr2.md           # Autonomous DDR
├── agents/
│   ├── *-v1.md           # Agents for wf1
│   ├── *-v3.md           # Agents for wf3
│   └── *-v4.md           # Agents for wf4
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

## Notes

- Each command file is self-contained with its full workflow
- Do NOT merge instructions from CLAUDE.md with command files
- Follow ONLY the command file when a command is invoked
