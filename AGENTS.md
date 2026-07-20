# Codex Project Guidance

This repository contains orchestration workflows for multiple coding agents.

- Claude Code workflows live under `.claude/commands` and `.claude/agents`.
- Codex workflows live under `codex/.agents/skills`; invoke them as `$wf`, `$research`, `$think`, `$reflect`, and `$tldr`, or select them from `/skills`.
- `$reflect` triggers on confirmed Codex mistakes and user corrections. It writes the postmortem/recurrence ledger under `~/.codex/reflections` (or project `.codex/reflections`) and strengthens the appropriate `AGENTS.md` rule through a tested escalation ladder.
- In Claude commands, `-c` means Codex. In Codex skills, `-c` means Claude. In both, `-g` means Gemini/Antigravity.
- Do not assume `/wf`, `/research`, or `/think` are repo-local Codex slash commands. Codex custom prompt slash commands are user-local under `~/.codex/prompts` and are deprecated; use repo skills for shared behavior.
- Generated Codex workflow scratch belongs under `codex/temp/`; keep that path gitignored. Codex research belongs under `codex/research/`. Claude research remains under `.claude/research/`.
- Codex `-c` calls Claude through `$HOME/.agents/bin/claude-peer` or `codex/bin/claude-peer`, preferring the user-local copy. The bridge must use official Claude Code `claude -p` with Claude.ai subscription/quota auth only, not Anthropic API-key billing.
- When Codex creates a git commit in this repo, append a final commit-message trailer: `Assisted-by: <source> <model>-<effort>`. Use `codex` as `<source>` for direct Codex work. Use `wf <flags>` when the commit was produced by `$wf`; include only workflow flags that affected the run, not the task text, for example `Assisted-by: wf -c gpt-5.5-xhigh`. Resolve `<model>` and `<effort>` from the active Codex session, falling back to `~/.codex/config.toml` keys `model` and `model_reasoning_effort`.
- Keep Claude and Codex surfaces separate. If behavior changes, update the matching workflow file and the README note that explains how to invoke it.
