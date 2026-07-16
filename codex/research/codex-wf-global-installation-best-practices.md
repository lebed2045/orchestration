# Research: Codex `$wf` Global Installation and Reviewer Routing

Generated: 2026-07-16 15:19 WITA
Mode: codebase + official OpenAI/Anthropic documentation + local capability checks
Degradation: none; no live reviewer calls were made
Gemini route: status-checked only; primary Antigravity and configured fallback both ready

## Executive Summary

The most Codex-native form of this workflow is a **Codex skill**, not a slash-command prompt. For personal use across repositories, keep the source in this repository and symlink the skill directory into `$HOME/.agents/skills/wf`. Codex officially scans that user directory and supports symlinked skill folders. For distribution to other users or machines, package the skill and its helper tooling as a plugin instead.

The current `$wf` is deliberately explicit-only. Its description says not to auto-route ordinary code changes into the workflow. That was a conscious rollback after an earlier experiment made every code change use the full workflow. Therefore global discovery and automatic activation are separate choices:

- Global discovery: now installed and verified.
- Automatic activation: currently disabled by the skill's trigger description.

For ordinary coding, the recommended design is to let Codex handle the task directly under concise `AGENTS.md` verification rules, then reserve `$wf` for work that merits strict split TDD, evidence receipts, review gates, or worktree/commit orchestration. If automatic activation is desired, change the description and `agents/openai.yaml` policy together and evaluate representative prompts before relying on it.

## What Is Actually Installed

The following personal/global symlinks were installed:

```text
$HOME/.agents/skills/wf
  -> codex/.agents/skills/wf
$HOME/.agents/bin/claude-peer
  -> codex/bin/claude-peer
$HOME/.agents/bin/codex-review-context
  -> codex/bin/codex-review-context
```

The Gemini router was already globally configured in Codex as the `agy` MCP server, with `$HOME/.local/bin/agy-ask` as its CLI fallback.

Verification performed:

- The Codex skill validator passed.
- A fresh ephemeral Codex process reported `$wf` as available from the linked `SKILL.md`.
- The Claude bridge self-test passed using `claude.ai`, first-party, Pro subscription authentication; it made no live model call.
- The Gemini router status check reported both the primary Antigravity model and configured fallback ready; it made no live model call.

## Reviewer Capability Matrix

| Orchestrator | Main implementer | Codex reviewer | Claude reviewer | Gemini reviewer |
|---|---|---|---|---|
| Claude Code `/workflow` | Claude | **Default on**; `-c` is retained for explicitness, `--no-codex` disables | Not applicable as an external peer | `-g` opt-in; ignored for micro tier |
| Codex `$wf` | Codex | Codex performs the main work and inline/deterministic review | `-c` opt-in through `claude-peer` | `-g` opt-in through the agy router |

The shorthand is intentionally symmetric: **`-c` means “the other main coding model.”** In Claude Code it means Codex; in Codex it means Claude. `-g` means Gemini/Antigravity on both sides.

The assumption that Codex cannot consult Claude is false on this machine. Codex does not receive Claude access from an OpenAI entitlement, but the repository provides a local bridge to the separately installed and authenticated Claude Code CLI. The bridge:

- requires Claude.ai subscription authentication;
- refuses API-key and third-party-provider authentication;
- unsets common Anthropic, Bedrock, and Vertex credential variables;
- disables Claude tools, edits, network, and session persistence for the peer pass.

If Claude Code is not installed or is not logged into Claude.ai, `$wf -c` degrades visibly instead of silently substituting another model.

## Best-Practice Findings

### 1. Skill for reasoning, `AGENTS.md` for durable defaults, hooks for enforcement

OpenAI recommends skills for reusable workflows, `AGENTS.md` for persistent repository conventions, and hooks when an action must be deterministically enforced. A full TDD/review workflow fits a skill; short rules such as “run relevant tests and inspect the diff before completion” fit `AGENTS.md`; a guarantee such as “block completion unless a test manifest exists” belongs in a hook.

### 2. Personal symlink now; plugin for distribution

`$HOME/.agents/skills` is the official personal scope. Symlinking the repository source preserves one source of truth and makes edits immediately available. A plugin is preferable when distributing several skills, helper executables, MCP configuration, hooks, or assets to other users and machines.

### 3. Keep implicit triggering narrow and test it

Codex supports explicit `$skill` invocation and implicit matching against the skill description. The description should front-load concrete trigger phrases and boundaries. `agents/openai.yaml` can explicitly set `policy.allow_implicit_invocation`; its default is `true`.

The current `$wf` description explicitly forbids implicit routing. If that policy remains, `openai.yaml` should eventually encode `allow_implicit_invocation: false` so the machine-readable policy and prose agree. If automatic routing is enabled, test at least these classes:

- Should trigger: multi-file implementation, bug fix requiring regression coverage, risky refactor.
- Should not trigger: read-only explanation, code review, research, typo, status request, or a task routed to another skill.
- Ambiguous: tiny code edit where native Codex plus normal verification is cheaper than full workflow ceremony.

### 4. Keep external reviews outside the inner loop

The existing Codex adaptation correctly keeps Claude and Gemini reviewers optional and review-focused. Use deterministic tests and local review during RED/GREEN; request an external model at the final gate or for a risky plan. This limits latency, quota use, and context duplication while retaining independence where it matters.

### 5. Prefer explicit reviewer names over mnemonic ambiguity

The cross-agent meaning of `-c` is documented but easy to misremember. Future versions should consider long aliases such as `--claude-review`, `--codex-review`, and `--gemini-review`, retaining `-c`/`-g` only as shortcuts.

### 6. Keep completion evidence, but avoid copying Claude-only machinery

The strong transferable parts are executable verification, RED/GREEN pressure when appropriate, diff inspection, independent review, bounded retry loops, and evidence-backed completion. Codex should express these through skills, plans, goals, subagents when useful, MCP, and shell verification—not emulate Claude-only primitives mechanically.

## Recommended Operating Model

### Recommended default: native Codex + explicit `$wf`

Use natural task prompts for routine work. Keep concise always-on verification expectations in global or repository `AGENTS.md`. Invoke `$wf` when you explicitly want its heavier contract:

```text
$wf implement the parser change
$wf -c implement the authentication fix
$wf -cg --tier=full implement the migration
```

This is the most predictable setup and matches the repository's explicit-only history.

### Hands-off alternative: implicit `$wf`

Revise the skill description to match implementation/fix/refactor requests, set `allow_implicit_invocation: true`, and add trigger-evaluation tests. Then a prompt such as “implement token refresh with regression tests” can activate `$wf` without typing its name. This is more automatic but makes latency and ceremony less predictable.

### Distribution alternative: orchestration plugin

Package `$wf`, `$research`, `$think`, the Claude peer/context helpers, and optional agy MCP metadata into one Codex plugin. This is the best option for reproducible installation across machines or sharing with other users, but it requires a manifest, installer/update path, and explicit decisions about optional external dependencies.

## Suggested Next Changes

1. Keep the newly installed global symlink setup for immediate use.
2. Choose between explicit full workflow and implicit full workflow; do not leave the policy ambiguous.
3. If keeping explicit-only, add `policy.allow_implicit_invocation: false` to `agents/openai.yaml`.
4. If enabling implicit activation, revise the description, add prompt-trigger evals, and keep commits/external reviewers opt-in.
5. If the workflow will be installed elsewhere, build a plugin rather than documenting manual symlinks and MCP commands.

## Sources

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Anthropic: Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Anthropic: Claude Code skills](https://code.claude.com/docs/en/skills)
- Local Codex workflow: `codex/.agents/skills/wf/SKILL.md`
- Local Claude workflow: `.claude/commands/workflow.md`
- Local Claude bridge: `codex/bin/claude-peer`
- Local Gemini router: `codex/bin/agy-peer-mcp`
- Routing rollback: git commit `664abe7`
