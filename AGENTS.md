# Codex Project Guidance

This repository contains orchestration workflows for multiple coding agents.

- Claude Code workflows live under `.claude/commands` and `.claude/agents`.
- Codex workflows live under `.agents/skills`; invoke them as `$wf`, `$research`, and `$think`, or select them from `/skills`.
- In Claude commands, `-c` means Codex. In Codex skills, `-c` means Claude. In both, `-g` means Gemini/Antigravity.
- Do not assume `/wf`, `/research`, or `/think` are repo-local Codex slash commands. Codex custom prompt slash commands are user-local under `~/.codex/prompts` and are deprecated; use repo skills for shared behavior.
- Generated Codex workflow artifacts belong under `.codex/temp/` and `.codex/research/`; keep those paths gitignored.
- Keep Claude and Codex surfaces separate. If behavior changes, update the matching workflow file and the README note that explains how to invoke it.
