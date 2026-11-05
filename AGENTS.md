# Orchestration — project rules (Claude Code and Codex)

**Updated:** `05-nov-2026`. This is the only project rules file. `CLAUDE.md` is just `@AGENTS.md` so Claude Code loads it too. Global rules live in `global/AGENTS.md` (see `global/README.md`). Sections marked *Claude only* / *Codex only* apply to that agent; everything else applies to both.

For installation or host/VM sharing, read `docs/shared-setup.md` and `dependencies.json` first. They describe shared sources and per-tool links; they do not authorize installation.

## Commands and skills

| Claude | Codex | What it does |
|---|---|---|
| `/workflow` (`/wf`) | `$wf` | TDD workflow; explicit-only. Other-model review ON by default (`--no-codex` in Claude). Prints `workflow v0.29 (19-jun-2026)` first. |
| `/cc` | — | Claude-led: Codex authors plan/tests/code, Claude reviews both gates. |
| `/manager` | — | Explicit-only cmux orchestrator above `/cc` (`--plan-only`, `--smoke-test`). |
| `/gardener` | — | Periodic entropy removal from `.claude/metrics/` ledgers. |
| `/sweep` | — | End-of-session working-tree sweep; never pushes. |
| `/research` (`/r`) | `$research` | Single-agent research; `-c` / `-g` add one bounded other-model pass. |
| `/think` | `$think` | Council-style deliberation. |
| `/reflect` | `$reflect` | Record a mistake; review the inbox; renew. See `docs/reflection.md`. |
| `/tl`, `/tldr` | `$tldr` | **TL;DR** + exactly three bullets. |
| `in-browser-verify` | `$in-browser-verify` | Web-app browser-proof completion gate. |

Flags: `-c` = call the other main model (Codex from Claude, Claude from Codex), `-g` = Gemini/Antigravity via the agy bridge, `-h` = human gate. Old generations live in `legacy/` for history only; they are not invocable.

## Ship-a-change rule (this repo only — do not promote to global)

Whenever you fix, update, or add behavior to any command / skill / agent / workflow / hook in this repo, the same turn must also:
1. **Bump the date** — an `**Updated:** \`DD-mmm-YYYY\`` line or dated banner. `workflow` also bumps `WF_VERSION` + `WF_COMMITTED` at the top of `.claude/commands/workflow.md`; the banner it prints derives from both.
2. **Update `README.md`**, keeping it terse one-liners. If an edit would grow it, trim elsewhere.

Command files own their workflow mechanics; the rules below still hold inside every command run unless a command explicitly overrides one.

## Shared TLDR

Follow `shared/skills/tldr/SKILL.md`: end substantive final answers with **TL;DR** and exactly three short bullets. Preserve failures and uncertainty. Explicit user-requested formats take precedence.

## Truth over approval

- If tests fail, say so. If you cannot verify, say "UNVERIFIED". If you don't know, say so. Never claim success to end a conversation.
- No "done / fixed / complete / tests pass / it works" without showing the command run, its output (last ~10 lines), exit code and producer (`/wf`, `/research`, `direct`, …).
- Timing in receipts is measured, never estimated. Claude: `.claude/temp/turn-started.txt` (line 1 epoch, line 2 human) gives the turn start; if missing, print `TIMING: UNVERIFIED (no start stamp)`.
- Circuit breakers: same error 2x → stop with options; tests fail 5x → "MANUAL INTERVENTION REQUIRED"; review fails 3x → "REVIEW LOOP EXCEEDED"; a claim without evidence → retract and verify.

## Portable engineering discipline

**Verification & regressions**
- **Live over docs.** "What does X currently use / is X running?" → live check, never memory or stale docs.
- **Baseline → delta.** Baseline before changes, re-run after, report the delta. A regression is stop-and-report.
- **Own your regressions.** Green-before / red-after is yours; never "flaky" or "pre-existing" without proof.
- **No absence from a filtered scan.** Enumerate unfiltered (`lsof`/`ps`) before claiming a runtime thing is absent; for files, state the search scope covered.
- **Experiment over theory.** Stalled after ~2 read-only passes → run a diagnostic (non-mutating if the request is observational).

**Authorization & scope**
- **Exact values sacred.** User-stated values, direction and scope are literal; tempted to substitute → confirm.
- **Questions ≠ authorization.** A question about merge/push/delete is answered, not executed.
- **Check = read-only.** "check / verify / see if / test if" → read and run only.
- **Git safety.** No stash/reset/clean, no commit, no extra destructive git step without explicit permission.
- **No-clobber.** `stat` before creating or replacing a file (case-insensitive collisions count); never `-y`/`--overwrite` onto a user file.

**Before editing / building**
- **Read before editing**, including the final output stage of a pipeline. Don't use a property/method you haven't confirmed exists.
- **Integrations before hand-rolling** for external services (Slack, WhatsApp, SaaS): search for a maintained MCP/library first.

**Tooling boundaries**
- **Isolate side effects.** Don't drive the user's daily browser or touch mounts/daemons/shared services as a workaround; use an isolated tool and ask first.
- **Gemini via the bridge** (`mcp__agy__agy_ask`, fallback `~/.local/bin/agy-ask`), never raw `agy`/`gemini`/Vertex.

## Claude only

- **`/workflow` (`/wf`) is explicit-only.** Invoke it only when the user types `/wf`/`/workflow` or names it. Never auto-route code changes into it.
- **Codex sidekick, every turn.** Code changes: before claiming done, call `mcp__codex-cli__codex` (`approval-policy: "never"`, `sandbox: "read-only"`) over the diff vs the pre-change SHA, ending with `VERDICT: APPROVED` or `VERDICT: NEEDS_WORK <reason>`; model/effort inherit from `~/.codex/config.toml`. Big non-code tasks: Codex consult up front and review at the end. Small answers: Codex second opinion on the draft. Exempt: bare acknowledgments (not the work they authorize). Max 3 review iterations. Opt-out only on `--no-codex` / "skip codex". If Codex is unavailable, proceed and print `CODEX REVIEW SKIPPED - <reason>`.
- Claude research goes to `.claude/research/`; scratch to `.claude/temp/` (gitignored).

## Codex only

- Codex workflows live under `codex/.agents/skills`; invoke as `$wf`, `$research`, `$think`, `$reflect`, `$tldr`, `$in-browser-verify`, or via `/skills`. Repo-local Codex slash commands don't exist (`~/.codex/prompts` is user-local and deprecated).
- `-c` calls Claude through `$HOME/.agents/bin/claude-peer` (preferred) or `codex/bin/claude-peer`, using official `claude -p` with Claude.ai subscription auth only — never Anthropic API-key billing.
- Scratch goes to `codex/temp/` (gitignored); research to `codex/research/`.
- Commit trailer: append `Assisted-by: <source> <model>-<effort>` (`codex` for direct work, `wf <flags>` for `$wf` runs, e.g. `Assisted-by: wf -c gpt-5.5-xhigh`). Resolve model/effort from the session, falling back to `~/.codex/config.toml` `model` / `model_reasoning_effort`.
- Keep Claude and Codex surfaces separate: when behavior changes, update the matching workflow file and the README note.


# Reflection after confirmed mistakes

<!-- CODEX-REFLECT-SYSTEM:START -->
After a confirmed mistake, correct the affected work and record the incident once. During authorized work, refine a concise project rule when useful. Global lessons are proposals only: use explicit reflection review and approved apply before changing global rules. Recurrence is evidence, not permission for stronger restrictions. Recording does not prove prevention.
<!-- CODEX-REFLECT-SYSTEM:END -->

<!-- CODEX-REFLECT-RULES:START -->
<!-- Managed by $reflect. Do not edit levels or strike chains by hand. -->

<!-- reflect-pattern: unverified-external-reviewer-transport -->
### Prove Reviewer Transport Before Recommending It (ref: ORCH-master-a431d3-1)
**[L1 REMINDER]**
WHEN recommending an external-reviewer flag or bridge in this repository:
DO verify the live executable, authentication path, and billing guard without issuing a paid model request; otherwise omit the reviewer flag.
PROVE show current command output confirming subscription-backed auth and API-key refusal, or state that the reviewer flag was omitted as unverified.

<!-- reflect-pattern: delegated-semantic-validation-gap -->
### Trace Delegated Workflow State Before Acceptance (ref: ORCH-master-8653c8-3)
**[L2 MANDATORY PROOF]** Strikes: ORCH-master-8653c8-1 -> ORCH-master-8653c8-3.
WHEN accepting subagent-authored workflow or skill changes in this repository:
DO trace every artifact branch, ordered output sequence, and participant-state transition against the final edited text before integration or completion.
PROVE show line-level current-turn evidence for stat checks on every canonical and fallback target, the complete ordered chat-output list, availability-to-success-to-round-two eligibility transitions, a whole-scope stale-feature search, and passing applicable validators and diff checks.

<!-- reflect-pattern: capability-boundary-assumption -->
### Honor Explicit Skill Ownership and Installation Targets (ref: ORCH-master-8653c8-4)
**[L2 MANDATORY PROOF]** Strikes: ORCH-master-8653c8-2 -> ORCH-master-8653c8-4.
WHEN a user asks to implement a capability described in an artifact that assigns it to a Claude or Codex surface:
DO extract and honor the artifact's explicit owner, invocation form, and installation target before scaffolding, and do not create a sibling-surface artifact unless requested.
PROVE before any write show a capability ownership matrix with the artifact quote, owner, invocation, and exact target path; after editing show a whole-scope search and diff proving the capability exists only on the assigned surface.
<!-- CODEX-REFLECT-RULES:END -->
