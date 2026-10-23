# Codex Project Guidance

This repository contains orchestration workflows for multiple coding agents.

- For installation or host/VM sharing, read `docs/shared-setup.md` and `dependencies.json` first. They describe shared source paths, per-tool discovery links and optional dependency pins; neither authorizes downloading, installing or enabling a component.

- Claude Code workflows live under `.claude/commands` and `.claude/agents`.
- Codex workflows live under `codex/.agents/skills`; invoke them as `$wf`, `$research`, `$think`, `$reflect`, `$tldr`, and `$in-browser-verify`, or select them from `/skills`.
- `$reflect` records each confirmed incident once through the shared recorder; global history is routed into the shared checkout. Rule changes require authorization and a generalized lesson; recording alone does not demonstrate prevention. See `shared/skills/reflect/SKILL.md`.
- `$in-browser-verify` is a standalone web-app verification workflow, not a `$wf` mode. In onboarded web repositories it persists scenarios, runs the full browser gate, requires fresh trace evidence, and uses Codex lifecycle hooks to prevent unsupported completion claims.
- In Claude commands, `-c` means Codex. In Codex skills, `-c` means Claude. In both, `-g` means Gemini/Antigravity.
- Do not assume `/wf`, `/research`, or `/think` are repo-local Codex slash commands. Codex custom prompt slash commands are user-local under `~/.codex/prompts` and are deprecated; use repo skills for shared behavior.
- Generated Codex workflow scratch belongs under `codex/temp/`; keep that path gitignored. Codex research belongs under `codex/research/`. Claude research remains under `.claude/research/`.
- Codex `-c` calls Claude through `$HOME/.agents/bin/claude-peer` or `codex/bin/claude-peer`, preferring the user-local copy. The bridge must use official Claude Code `claude -p` with Claude.ai subscription/quota auth only, not Anthropic API-key billing.
- When Codex creates a git commit in this repo, append a final commit-message trailer: `Assisted-by: <source> <model>-<effort>`. Use `codex` as `<source>` for direct Codex work. Use `wf <flags>` when the commit was produced by `$wf`; include only workflow flags that affected the run, not the task text, for example `Assisted-by: wf -c gpt-5.5-xhigh`. Resolve `<model>` and `<effort>` from the active Codex session, falling back to `~/.codex/config.toml` keys `model` and `model_reasoning_effort`.
- Keep Claude and Codex surfaces separate. If behavior changes, update the matching workflow file and the README note that explains how to invoke it.
- Portable engineering-discipline rules (authorization gates, check=read-only, no-clobber, live-over-docs, baseline→delta, own-your-regressions, Gemini-via-bridge, …) apply to Codex sessions in this repo too. The canonical list is the "Portable engineering discipline" section of `CLAUDE.md` — read and follow it; do not duplicate it here.

# Reflection after confirmed mistakes

<!-- CODEX-REFLECT-SYSTEM:START -->
After a confirmed mistake, acknowledge it, correct the affected work within scope, and use `$reflect` to record the incident once and check recurrence. Add or tighten at most one authorized generalized rule; preserve unrelated rules. Existing ledger levels are history, not permission to impose new restrictions. Report recording separately from tested prevention.
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
