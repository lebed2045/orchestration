# Orchestration

Slash-command workflows for [Claude Code](https://claude.com/claude-code) that force TDD, zero-context review, and verifiable completion. Stops Claude from claiming "done" without proof.

## Install

Open Claude Code in your project and paste:

```
Check the repo https://github.com/lebed2045/orchestration — adopt it for my workflow, review all files in my project and this repo, interview me with questions, install globally (~/.claude/).
```

Restart Claude Code and the commands appear.

## Commands

| Command | What it does |
|---|---|
| `/wf` | The workflow. Tier-auto TDD on modern primitives. Prints `wf v16 (26-may-2026)` as its first line. |
| `/research` (`/r`) | Codebase + Antigravity CLI + Codex MCP research. |
| `/reflect` | Turn recurring failures into rules. |

Older generations are archived in [legacy/](legacy/) (outside `.claude/` so Claude Code doesn't auto-register them as commands). They're kept in the repo as evolutionary context for AI coders reading the codebase, not for invocation.

## Why bother

Vanilla Claude reviews its own work and the review is biased. `/wf` enforces three things vanilla skips: TDD as a gate (RED then GREEN, both verified), zero-context reviewers (no planning history → can't be optimistic), and `EXECUTION_BLOCK` proof (command + output + exit code) before any completion claim. Plus `BASELINE_BLOCK`/`REGRESSION_DELTA` anti-regression. Full rules in [CLAUDE.md](CLAUDE.md).

## Optional reviewers

- `-c` → Codex MCP: `npx -y codex-mcp-server`
- `-g` → Antigravity CLI: `curl -fsSL https://antigravity.google/cli/install.sh | bash` (Gemini-MCP successor; Gemini CLI sunsets 2026-06-18)

Workflows degrade gracefully when these aren't installed.

## Thanks

A GitHub star on [lebed2045/orchestration](https://github.com/lebed2045/orchestration) tells me what's worth building more of. PRs welcome. "This didn't work for me" reports are most valuable.

## License

MIT
