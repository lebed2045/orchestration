# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

| Command | Version | Agents | Description |
|---------|---------|--------|-------------|
| `/wf1` | v1 | `*-v1` | 8-phase workflow, Gemini review, orchestrator implements |
| `/wf2` | v2 | inline | 10-phase workflow, 3-gate dual-review, isolated coder |
| `/wf3` | v3 | `*-v3` | 10-phase, 3-gate, isolated coder + anti-regression |
| `/wf4` | v4 | `*-v4` | 8-phase, 2-gate, autonomous (infer, auto-fix, triple review) |
| `/wf5` | v5 | `*-v3` | 10-phase, 3-gate, wf3 + Codex (triple review in Gate 1) |
| `/wf6` | v6 | `*-v3` | 10-phase, 3-gate, quad review (Gemini+Codex+Opus+Sonnet) + retrospective |
| `/wf7` | v7 | inline | 9-phase, 2-gate, token-optimized (Codex+Gemini+CodeSmell), 75% less tokens |
| `/ddr` | - | uses wf3 | Meta-orchestrator: Divide, Delegate, Reflect |

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
│   ├── wf1.md            # v1 workflow
│   ├── wf2.md            # v2 workflow (inline prompts)
│   ├── wf3.md            # v3 anti-regression workflow
│   ├── wf4.md            # v4 autonomous workflow
│   ├── wf5.md            # v5 triple review workflow
│   ├── wf6.md            # v6 quad review + retrospective
│   ├── wf7.md            # v7 token-optimized (Codex+Gemini+CodeSmell)
│   └── ddr.md            # Meta-orchestrator
├── agents/
│   ├── *-v1.md           # Agents for wf1
│   ├── *-v3.md           # Agents for wf3
│   └── *-v4.md           # Agents for wf4 (autonomous)
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
