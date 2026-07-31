# Orchestration Project

This project contains orchestrated development workflows. Use the commands below to activate them.

## Available Commands

Run `/wf` for quick reference table.

### Current

| Command | Description |
|---------|-------------|
| `/workflow` (`/wf`) | The workflow. Fast TDD on modern primitives (Agent + worktree + tier-auto). Codex reviewer ON by default (`--no-codex` to disable). Prints `workflow v0.28 (19-jun-2026)` as its first line on every invocation. |
| `/cc` | Standalone Claude-led workflow: Codex authors plan/tests/code/fixes and runs cops; Claude reviews both gates — the plan (Gate 1) and the code (Gate 2, fresh agent). |
| `/manager` | Explicit-only cmux orchestrator with `--plan-only` and a version-pinned `--smoke-test` gate before isolated `/cc` fan-out. Updated `22-jul-2026`. |
| `/gardener` | Periodic entropy removal. Reads the longitudinal ledgers (`.claude/metrics/ratchet.tsv`, `debt.tsv`), sweeps for duplication/dead code, executes top-K cleanups as small `/wf`-style tasks (`--top=K`, `--dry-run`). |
| `/sweep` | End-of-session working-tree sweep. Classifies every uncommitted path into discard/ignore/commit-main/commit-sidecar/stash/hold and executes so `git status` ends clean. Codex consult ON by default (`--fast` / `--no-codex` to skip); secrets hard-fenced from auto-commit; never pushes. Prints `sweep (19-jun-2026)` as its first line. |
| `/research` (`/r`) | Single-agent Claude research by default. `-c` adds one bounded Codex pass, `-g` adds one bounded Antigravity pass, and `--multi-agent` explicitly permits Explore fan-out. |
| `/think` | Council-style deliberation for judgment calls, framing critique, and pushback |
| `/reflect` | Turn failures into rules with escalation ladder |
| `/tl` | Tweet-size summary of the last output + clickable next-action buttons |
| `in-browser-verify` (skill) | Web-app verification gate: scenario ledger (`verification/scenarios.md`) mapped to Playwright tests by stable IDs, full-suite runs with fresh trace evidence, immutable run manifests, and project-local SessionStart/Stop hooks that block unproven "done" claims. Onboard per-repo via `scripts/in_browser_verify.py init`. Updated `13-jul-2026`. |

### Legacy (archived in `legacy/`, NOT invocable as slash commands)

Older generations live in `legacy/commands/` and `legacy/agents/` at the repo root — outside `.claude/` so Claude Code doesn't auto-register them. They're kept for **evolutionary context only**: an AI coder reading this repo can see how the workflows progressed (wf1 → wf3 anti-regression → wf6 quad-review → wf12 3-cops → wf16 modern primitives → wf16 renamed to `/wf`). Do not reference them as `/legacy:wfX` — that namespace no longer exists. If you need to revive one, copy the file back into `.claude/commands/` and update its content.

### Bumping the `/workflow` version banner

When the workflow body in `.claude/commands/workflow.md` changes meaningfully, update **both** lines at the top of the file:
- `**WF_VERSION:** \`v17\`` (bump from v16)
- `**WF_COMMITTED:** \`DD-mmm-YYYY\`` (lowercase month abbreviation, e.g. `27-may-2026`)

The mandatory first-line banner the workflow prints is derived from these two values. If they drift apart, the rule fails.

### Ship-a-change rule: bump date (+ version for workflow) + sync README (project-local)

Whenever you fix, update, or add behavior to any artifact in this repo (command / skill / agent / workflow / hook), the SAME turn MUST also:
1. **Bump the date — and the version, for `workflow` only.** `workflow` carries `WF_VERSION` + `WF_COMMITTED` (bump both). Every other skill carries just a date — an `**Updated:** \`DD-mmm-YYYY\`` line or its dated first-line banner (e.g. `sweep (DD-mmm-YYYY)`). No change ships without at least a date bump.
2. **Update `README.md`** to reflect the change.
3. **Keep `README.md` very short** — terse one-liners only, no prose creep. If an edit would grow it, trim elsewhere to hold the line.

This is a local directive (this repo's CLAUDE.md only) — do NOT promote it to global `~/.claude/CLAUDE.md`.

**Suffix legend:** `g`=Gemini/Antigravity via the agy bridge (`mcp__agy__agy_ask` / `agy-ask`, Gemini-MCP successor), `c`=Codex MCP (**default-on in `/wf` since v22** — `--no-codex` opts out), `h`=human gate

For Codex skills, `c` is inverted: `$wf -c` and `$research -c` request Claude. The rule is "call the other main model."

**The command files contain the full workflow. CLAUDE.md only has general rules.**

---

## General Rules (Apply to All Workflows)

### `/workflow` (`/wf`) is explicit-only

Invoke the `workflow` skill ONLY when the user explicitly types `/workflow` or `/wf` (or names it: "run wf", "use the workflow"). `/wf` is a thin alias command that delegates to `workflow.md`. Never auto-route a code-change request into `/wf` — handle it directly (still under the Codex sidekick rule below). Rolled back 11-jun-2026: the old "all code changes go through /wf" default routing is gone.

### Auto-TLDR at end of turn — TEST (this repo only, not promoted to global)

At the end of every substantive assistant turn in this repo, append the `/tl` TLDR automatically — the user shouldn't have to type `/tl`. Follow the **summary + triage behavior** of [.claude/commands/tl.md](.claude/commands/tl.md) (its help-banner step does NOT apply here — no banner every turn):

1. **Tweet summary.** One line, ≤ 280 chars, plain language, lead with the outcome/verdict. Anti-sycophancy applies (failed / unverified / needs-work says so, never softened). No headers, tables, bullets, or code blocks in this line.
2. **Actionability triage** — exactly one:
   - **Actionable** — only when the turn surfaced an *explicitly identified* fix, a concrete decision between named paths, or a genuinely unfinished step. Call `AskUserQuestion` using the ≤280-char summary **as the question text** (do NOT also print it as a separate line), with 2–4 options derived from the content, one always "Leave as is" (so ≤ 3 content actions; concrete labels ≤ 5 words). Never invent follow-up work or a speculative "improvement" just to show buttons.
   - **Not actionable** — pure ack / FYI / nothing concrete to do next → print the summary line only, no buttons.

**Exemptions (no auto-TLDR):** trivial acknowledgment turns ("ok", "noted"); a turn that was itself a `/tl` run (don't double up); and inside command-file runs (`/wf`, `/sweep`, `/research`, `/gardener`, …) which own their own end-of-run output — the auto-TLDR is for direct turns only. If a turn genuinely required an `AskUserQuestion` of its own, that question *is* the actionable TLDR — but never add a question merely to skip the summary.

Soft rule, **no enforcement hook** — a strong default, not a Stop-hook gate (a Stop hook was considered and declined: extra model turn + cost every turn, breaks non-interactive runs, composes badly with `/wf`'s own stop handling). The summary is a read-only digest, exempt from EXECUTION_BLOCK; any action taken after a button press follows the global rules in full. If this proves reliable here, promote to global `~/.claude/CLAUDE.md`. Added 20-jul-2026.

### Codex sidekick — always on, every turn

Codex MCP is a permanent second opinion watching every turn — not just code changes, and not just inside skills.

- **Code changes** (anywhere — `/wf`, other skills, direct edits): before claiming done, call `mcp__codex-cli__codex` with `approval-policy: "never"`, the task-appropriate sandbox (normally `read-only` for review), and a review prompt over the diff (vs the pre-change SHA), ending with `End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>.` Model/effort inherit from `~/.codex/config.toml`. The user-level `PreToolUse` hook is the mechanical backstop for omitted or interactive approval policy. Inside `/wf`: `-c` is default-on for all tiers since v22 (`--no-codex` opts out).
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
│ SOURCE: [/wf tier-N | /research | ... | direct]  │
│ $ [actual command run]                           │
│ [actual output - at least last 10 lines]         │
│ EXIT_CODE: [0 or non-zero]                       │
│ TIMING: [start → end | TOTAL Xm Ys | UNVERIFIED] │
└──────────────────────────────────────────────────┘
```

**Every receipt names its producer.** The `SOURCE:` row, the `⏱` timing line, and the `🔌` externals line each carry the workflow/skill that emitted them (`/wf`, `/research`, `/sweep`, …); work done outside any skill says `direct`.

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

### Portable engineering discipline (ships with the repo — added 19-jul-2026)

Portable safety/verification rules distilled from hard-won agent failures. Unlike the reflection ledger (which stays in each user's `~/.claude/`), these travel with the repo, so every Claude Code session in this repo inherits them; the Codex surface picks them up via the pointer in `AGENTS.md`. They apply on every turn, **including inside `/wf`, `/sweep`, and other command runs** — a command file owns its workflow mechanics, but these safety rules still hold unless a command explicitly overrides one. Terse on purpose — each one taxes every turn. Tool names below are illustrative; use your platform's equivalent.

**Verification & regressions**
- **Live over docs.** "What does X currently use / is X running?" → run a live check; never answer from memory or stale docs.
- **Baseline → delta.** Capture a baseline before changes, re-run after, report the delta. A regression is STOP-and-report, not a footnote.
- **Own your regressions.** Green-before / red-after is YOUR regression — never label a failure "flaky" or "pre-existing" without proof from the code you changed.
- **No absence from a filtered scan.** Never claim a *runtime* thing (port/process/service) is absent from a grep for guessed names — enumerate the full set unfiltered first (`lsof`/`ps` with no filter), then identify each unknown listener. For a file/config claim, state the complete search scope you actually covered.
- **Experiment over theory.** Stalled after ~2 read-only passes → run a diagnostic (verbose output, a minimal repro, or targeted logging where writes are authorized) instead of reading again. If the request is observational, keep the diagnostic non-mutating or get the OK to instrument first. Action produces data; theory produces tokens.

**Authorization & scope**
- **Exact values sacred.** Use user-stated values, direction, and scope literally (branch, path, size, "bigger/smaller", "local/global"). Tempted to substitute → HALT and confirm.
- **Questions ≠ authorization.** A question about a state-changing op ("should we merge/push/delete X?") is not a go — answer it and stop. Act only on explicit authorization ("do it", "yes", "go ahead").
- **Check = read-only.** "check / verify / see if / test if" means read and run only — no mutation of source or durable external state (isolated test/temp artifacts are fine). Edit source only when the ask is to add/create/implement/change/update/fix/modify/refactor/remove.
- **Git safety.** No stash/reset/clean, no commit, and no destructive git step beyond what was asked, without explicit permission.
- **No-clobber.** Before creating a new output file or destructively replacing one — including case-insensitive collisions — `stat` the target first; if it exists, you didn't create it, and you weren't told to modify it, pick a new name or ask. Never pass `-y`/`--overwrite` onto an existing user file. (Ordinary authorized edits to a file already in scope are fine.)

**Before editing / building**
- **Read before editing.** Read the code — and the final output stage of a pipeline — before changing it. Don't reference a property/method you haven't confirmed exists.
- **Integrations before hand-rolling.** Before wiring an external *service* (Slack, WhatsApp, calendar, SaaS), search for a maintained MCP/library first. (Does not apply to ordinary local/utility code — just write it.)

**Tooling boundaries**
- **Isolate side effects.** Don't drive the user's daily browser or touch mounts/daemons/shared services as a workaround — use an isolated tool (e.g. Playwright) and ask before touching shared infra.
- **Gemini via the bridge.** Route Gemini calls — including Gemini second opinions and `-g` reviews — through the agy bridge (`mcp__agy__agy_ask`, or the `~/.local/bin/agy-ask` CLI fallback), never a raw `agy`/`gemini`/Vertex/genai API call. (Codex second opinions go through the Codex MCP, not this route.)

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
│   ├── tl.md             # Tweet-size TLDR + action buttons (self-contained)
│   └── think.md, reflect.md  # Deliberation + reflection utilities
├── agents/
│   ├── simplicity-cop.md, coherence-cop.md, coverage-cop.md   # Boris's 3 cops (used by /wf)
│   ├── metrics-cop.md                                         # 4th cop: evidence-graded signals — hard-blocks dup/suppressions/cycles, warns on size (v19)
│   └── code-simplifier.md, plan-reviewer.md, verify-app.md    # Helpers (used by archived boris2)
├── skills/
│   ├── cc/SKILL.md                    # One-track Claude lead with Codex authoring
│   ├── manager/SKILL.md               # Explicit cmux program orchestrator above /cc
│   └── in-browser-verify/             # Browser-proof completion gate
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
- **Exception:** command files own their workflow *mechanics*, but two things above still apply to ALL turns unless a command explicitly overrides them — (1) the "Codex sidekick — always on, every turn" rule (including runs of command files that lack their own Codex step: `/wf` v22+ has it built in; for any other command that edits code, add the Codex review at the end), and (2) the "Portable engineering discipline" safety rules.
