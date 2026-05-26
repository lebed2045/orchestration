# Orchestration

**Multi-phase development workflows for [Claude Code](https://claude.com/claude-code), packaged as slash commands.** Each workflow chains specialized agents — cops, coders, reviewers, planners — under strict TDD, anti-regression checks, and verifiable completion gates. The goal: stop Claude from claiming "done" without proof, catch what the original author misses, and keep tests honest.

If you've ever shipped Claude-generated code only to find the tests were self-fulfilling, the warnings were ignored, or the "fix" silently broke something else — these workflows exist for that.

## Install (set it and forget it)

Open Claude Code in your project and paste:

```
Check the repo https://github.com/lebed2045/orchestration — adopt it for my workflow, review all files in my project and this repo, interview me with questions, install globally (~/.claude/).
```

Claude will review this repo, ask about your preferences (test runner, framework, style rules), then install workflows into `~/.claude/commands/`. Done. Restart Claude Code and the slash commands appear.

## 30-second tour

```
/wf16 add an email validator with regex + tests
```

What happens:
1. **Tier auto-detect** — wf16 reads your task, picks `small` tier (one file, one feature)
2. **Split TDD** — two zero-context agents in sequence: one writes a failing test (RED), commits; another implements until it passes (GREEN), commits
3. **Coverage cop** — adversarial reviewer with default REJECT verdict checks the test actually exercises the feature
4. **Proof block** — wf16 prints command output + exit code; no "looks good to me" handwave

For multi-file features: `/wf16 implement OAuth refresh flow` → auto picks `full` tier, runs 3 cops (simplicity, coherence, coverage), optional worktree isolation.

## Current workflows

| Command | What it does |
|---|---|
| `/wf16` | Fast-iteration TDD on modern Claude Code primitives (Agent + worktree + tier-auto). **Default for new work.** |
| `/wf15` | Fast TDD on slow suites (Unity, .NET) + optional `-c` Codex / `-g` Antigravity reviewers. |
| `/boris2` | Boris Cherny patterns + Agent Teams (parallel TDD across files). |
| `/ddr2` | Autonomous Divide-Delegate-Reflect — recursively splits oversized tasks. |
| `/sc-audit` | Smart contract audit: 6 parallel reviewers + blue team + LP scorecard. |
| `/research` (`/r`) | Multi-agent research: codebase + Antigravity CLI + Codex MCP. |
| `/reflect` | Turn recurring failures into rules with L1–L4 escalation. |
| `/wf` | Print the quick-reference table. |

Run `/wf` inside Claude Code for the full flag legend.

## What makes this different

Vanilla Claude Code plans, codes, reviews itself, and claims done. The author knows why it was written, so the review is biased. Tests get written to pass, warnings get ignored, "complete" gets said without proof.

These workflows enforce three things vanilla flows skip:

- **TDD as a gate, not a suggestion.** RED phase must produce a failing test (verified). GREEN phase must turn it green (verified). You see both exit codes.
- **Zero-context reviewers.** Reviewer agents are spawned without the planning history. They can't be optimistic about code they didn't write — they only see the diff and the spec.
- **`EXECUTION_BLOCK` before any completion claim.** Command + output + exit code, pasted in full. "Should work" and "tests pass" without an `EXIT_CODE: 0` line are blocked phrases.

Anti-regression workflows (`wf15`, `wf16`) additionally capture a `BASELINE_BLOCK` before any change and compare after — increased warnings or new failures trigger STOP, not "let me try harder."

## Legacy

Older workflows live in [.claude/commands/legacy/](.claude/commands/legacy/) and resolve as `/legacy:wf3-gh`, `/legacy:wf12`, etc. The set includes `wf1`–`wf12`, `wf14`, `boris1-h`, and `ddr`. Still runnable for back-compat; don't add new functionality there — promote any keeper into the current set. Their dependency agents (`coder-v*`, `intake-v*`, `planner-v*`, `fresh-reviewer-v*`, `researcher-v1`) live in [.claude/agents/legacy/](.claude/agents/legacy/).

## Requirements

- **Claude Code** — CLI, VS Code extension, or JetBrains.
- **Optional reviewers** for `-c` and `-g` flags:
  - `-c` → `codex-cli` MCP server: `npx -y codex-mcp-server`
  - `-g` → Antigravity CLI (`agy`): `curl -fsSL https://antigravity.google/cli/install.sh | bash`
    Antigravity is Google's named successor to Gemini CLI (the latter sunsets for AI Pro/Ultra on **2026-06-18**). Note: `agy` is a CLI subprocess, not an MCP — workflows shell out via `agy -p "<prompt>"`.

Everything else is optional. The workflows degrade gracefully when reviewers aren't installed.

## Proof discipline

Every workflow enforces an `EXECUTION_BLOCK` (command + output + exit code) before any "done"/"fixed"/"complete" claim. `wf15` and `wf16` add anti-regression: `BASELINE_BLOCK` captured before changes, `REGRESSION_DELTA` reported after. Same-error-twice → STOP and escalate. Full rule set lives in [CLAUDE.md](CLAUDE.md).

## Contributing

Found a workflow pattern that catches a class of bug yours doesn't? Open a PR. The bar: it must enforce verifiable proof, not vibes. New workflows go in `.claude/commands/`, agents in `.claude/agents/`. If it's experimental, name it clearly (`wfNN-experimental.md`) so it's obvious it hasn't earned a slot in the current set.

## Virtual thank-you

If any of these workflows save you time — even once — the warmest way to say thanks is a GitHub star on [lebed2045/orchestration](https://github.com/lebed2045/orchestration). It's free, it takes one click, and it tells me which patterns are worth building more of. Issues and PRs are equally welcome; "this didn't work for me" reports are most valuable of all.

## License

MIT
