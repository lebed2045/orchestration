# Orchestration

Orchestration workflows for coding agents that force TDD, independent review where available, and verifiable completion.

## Install

Open Claude Code in your project and paste:

```
Check the repo https://github.com/lebed2045/orchestration — adopt it for my workflow, review all files in my project and this repo, interview me with questions, install globally (~/.claude/).
```

Restart Claude Code and the commands appear.

## Commands

| Command | What it does |
|---|---|
| `/wf` | The workflow. Tier-auto TDD on modern primitives. Prints `wf v19 (10-jun-2026)` as its first line. |
| `/research` (`/r`) | Codebase + Antigravity CLI + Codex MCP research. |
| `/think` | Council-style deliberation for judgment calls, framing critique, and pushback. |
| `/reflect` | Turn recurring failures into rules. |

## Codex

Codex does not load repo-local `/wf`, `/research`, or `/think` slash commands out of the box. Its repo-shared mechanism is skills, so the Codex equivalents live in:

```text
.agents/skills/
├── wf/
├── research/
└── think/
```

Invoke them in Codex as `$wf <task>`, `$research <topic>`, and `$think <topic>`, or choose them from `/skills`. Start a new Codex session if the skills do not appear immediately. Codex custom prompt slash commands exist as `/prompts:<name>`, but they are user-local under `~/.codex/prompts` and deprecated, so this repo uses skills instead.

Older generations are archived in [legacy/](legacy/) (outside `.claude/` so Claude Code doesn't auto-register them as commands). They're kept in the repo as evolutionary context for AI coders reading the codebase, not for invocation.

## Why bother

Vanilla Claude reviews its own work and the review is biased. `/wf` enforces three things vanilla skips: TDD as a gate (RED then GREEN, both verified), zero-context reviewers (no planning history → can't be optimistic), and `EXECUTION_BLOCK` proof (command + output + exit code) before any completion claim. Plus `BASELINE_BLOCK`/`REGRESSION_DELTA` anti-regression. Full rules in [CLAUDE.md](CLAUDE.md).

## Optional reviewers

- `-c` means "the other main model": Claude commands call Codex; Codex skills call Claude.
- `-g` means Gemini / Antigravity.

Workflows degrade gracefully when these aren't installed.

## Thanks

A GitHub star on [lebed2045/orchestration](https://github.com/lebed2045/orchestration) tells me what's worth building more of. PRs welcome. "This didn't work for me" reports are most valuable.

## License

MIT
