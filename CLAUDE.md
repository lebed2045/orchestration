# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

Run `/wf` for quick reference table.

### Current

| Command | Description |
|---------|-------------|
| `/workflow` (`/wf`) | The workflow. Fast TDD on modern primitives (Agent + worktree + tier-auto). Codex reviewer ON by default (`--no-codex` to disable). Prints `workflow v0.27 (13-jun-2026)` as its first line on every invocation. |
| `/gardener` | Periodic entropy removal. Reads the longitudinal ledgers (`.claude/metrics/ratchet.tsv`, `debt.tsv`), sweeps for duplication/dead code, executes top-K cleanups as small `/wf`-style tasks (`--top=K`, `--dry-run`). |
| `/sweep` | End-of-session working-tree sweep. Classifies every uncommitted path into discard/ignore/commit-main/commit-sidecar/stash/hold and executes so `git status` ends clean. Codex consult ON by default (`--fast` / `--no-codex` to skip); secrets hard-fenced from auto-commit; never pushes. Prints `sweep v1 (13-jun-2026)` as its first line. |
| `/research` (`/r`) | Multi-agent research (codebase + Antigravity + Codex) |
| `/think` | Council-style deliberation for judgment calls, framing critique, and pushback |
| `/reflect` | Turn failures into rules with escalation ladder |
| `/tl` | Tweet-size summary of the last output + clickable next-action buttons (`tldr` skill) |

### Legacy (archived in `legacy/`, NOT invocable as slash commands)

Older generations live in `legacy/commands/` and `legacy/agents/` at the repo root — outside `.claude/` so Claude Code doesn't auto-register them. They're kept for **evolutionary context only**: an AI coder reading this repo can see how the workflows progressed (wf1 → wf3 anti-regression → wf6 quad-review → wf12 3-cops → wf16 modern primitives → wf16 renamed to `/wf`). Do not reference them as `/legacy:wfX` — that namespace no longer exists. If you need to revive one, copy the file back into `.claude/commands/` and update its content.

### Bumping the `/workflow` version banner

When the workflow body in `.claude/commands/workflow.md` changes meaningfully, update **both** lines at the top of the file:
- `**WF_VERSION:** \`v17\`` (bump from v16)
- `**WF_COMMITTED:** \`DD-mmm-YYYY\`` (lowercase month abbreviation, e.g. `27-may-2026`)

The mandatory first-line banner the workflow prints is derived from these two values. If they drift apart, the rule fails.

**Suffix legend:** `g`=Antigravity CLI (`agy -p`, Gemini-MCP successor), `c`=Codex MCP (**default-on in `/wf` since v22** — `--no-codex` opts out), `h`=human gate

For Codex skills, `c` is inverted: `$wf -c` and `$research -c` request Claude. The rule is "call the other main model."

**The command files contain the full workflow. CLAUDE.md only has general rules.**

---

## General Rules (Apply to All Workflows)

### `/workflow` (`/wf`) is explicit-only

Invoke the `workflow` skill ONLY when the user explicitly types `/workflow` or `/wf` (or names it: "run wf", "use the workflow"). `/wf` is a thin alias command that delegates to `workflow.md`. Never auto-route a code-change request into `/wf` — handle it directly (still under the Codex sidekick rule below). Rolled back 11-jun-2026: the old "all code changes go through /wf" default routing is gone.

### Codex sidekick — always on, every turn

Codex MCP is a permanent second opinion watching every turn — not just code changes, and not just inside skills.

- **Code changes** (anywhere — `/wf`, other skills, direct edits): before claiming done, call `mcp__codex-cli__codex` with a review prompt over the diff (vs the pre-change SHA), ending with `End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>.` Model/effort inherit from `~/.codex/config.toml`. Inside `/wf`: `-c` is default-on for all tiers since v22 (`--no-codex` opts out).
- **Big non-code tasks** (multi-step work, designs, plans, research syntheses): upfront Codex consult on the approach AND a final Codex review of the result.
- **Small turns** (quick questions, short answers): send the draft answer to Codex for a second opinion before delivering, and include its take.
- **Exempt:** trivial acknowledgments ("ok", "thanks", "yes do it") only — but any work an ack authorizes still gets the full Codex treatment above; the exemption covers the ack turn itself, never the task it triggers.
- `NEEDS_WORK` → address findings or report them honestly; max 3 review iterations (existing circuit breaker applies).
- Opt-out: only when the user says `--no-codex` / "skip codex" for that request.
- If the Codex MCP is unavailable: proceed (downgrade allowed) but print `CODEX REVIEW SKIPPED - MCP missing` in the final output. Never silently skip.

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
┌──────────────────────────────────────────────────┐
│ EXECUTION_BLOCK (required for completion)        │
├──────────────────────────────────────────────────┤
│ $ [actual command run]                           │
│ [actual output - at least last 10 lines]         │
│ EXIT_CODE: [0 or non-zero]                       │
│ TIMING: [start → end | TOTAL Xm Ys | UNVERIFIED] │
└──────────────────────────────────────────────────┘
```

**TIMING is measured, never estimated.** The `UserPromptSubmit` hook writes a turn-start stamp to `.claude/temp/turn-started.txt` on every prompt (line 1 = epoch, line 2 = human-readable — same format as the wf ledger). Compute the `TIMING` line with real commands: start = line 2 of the stamp, end from `date`, TOTAL = `$(date +%s)` minus line 1. If the stamp file is missing (hook not active, different repo), print `TIMING: UNVERIFIED (no start stamp)` — never guess. Note: the stamp measures the **current turn** (since the user's last message); `/wf` runs additionally print their whole-run timing receipt from the Phase 1 ledger.

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
│   ├── workflow.md       # The workflow (was wf16, then wf.md). Prints version banner on invocation.
│   ├── wf.md             # Thin alias → workflow.md
│   ├── research.md       # Multi-agent research (canonical)
│   ├── r.md              # Thin alias → research.md
│   ├── tl.md             # Thin alias → tldr skill
│   └── think.md, reflect.md  # Deliberation + reflection utilities
├── agents/
│   ├── simplicity-cop.md, coherence-cop.md, coverage-cop.md   # Boris's 3 cops (used by /wf)
│   ├── metrics-cop.md                                         # 4th cop: evidence-graded signals — hard-blocks dup/suppressions/cycles, warns on size (v19)
│   └── code-simplifier.md, plan-reviewer.md, verify-app.md    # Helpers (used by archived boris2)
├── reference/
│   └── code-quality-metrics.md   # Threshold source-of-truth for metrics-cop
└── settings.local.json   # Hooks configuration

codex/postmortems/              # Incident writeups and corrective actions

legacy/                   # Archived for AI-coder evolutionary context — NOT auto-loaded by Claude Code
├── commands/             # wf1-wf12, wf14, wf15, boris1-h, boris2, ddr, ddr2, sc-audit
└── agents/               # coder-v1/v3/v4, intake-v*, planner-v*, fresh-reviewer-v*, researcher-v1
```

**Codex equivalents:**

```text
codex/
├── .agents/
│   └── skills/
│       ├── wf/
│       ├── research/
│       └── think/
├── bin/                  # Codex helper bridges
├── postmortems/          # Codex incident writeups
├── research/             # Codex research/deliberation outputs
└── temp/                 # Codex scratch, gitignored
```

Codex invokes these as `$wf`, `$research`, and `$think` or through `/skills`. In Codex skills, `-c` requests Claude and `-g` requests Gemini/Antigravity. They are skills rather than repo-local slash commands because Codex custom prompt slash commands live in `~/.codex/prompts` and are deprecated.

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

.claude/research/         # Generated by Claude /research and /think
codex/temp/               # Generated by Codex $wf and $research scratch
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
- **Exception:** the "Codex sidekick — always on, every turn" rule above applies to ALL turns — including runs of command files that lack their own Codex step (`/wf` v22+ has it built in; for any other command that edits code, add the Codex review at the end)
