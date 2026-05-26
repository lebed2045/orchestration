# /wf - Workflow Quick Reference

Show this table and STOP. Do not execute any workflow.

## Current Workflows

| Command | Reviewers | Gates | H | Description |
|---------|-----------|-------|---|-------------|
| `/boris2` | 2×O | 2 | 0 | Boris + Agent Teams (auto) |
| `/wf15` | 3-cops + opt MCP | 2 | 0-1 | Fast TDD + optional `-c` `-g` reviewers |
| `/wf16` | 3-cops + opt reviewer | 2 | 0-1 | Fast TDD on modern primitives (Agent + worktree). Default for new work. |
| `/ddr2` | (wf-current) | — | — | Autonomous Divide-Delegate-Reflect |
| `/sc-audit` | — | — | — | Smart contract audit (parallel reviewers + LP scorecard) |
| `/research` (`/r`) | — | — | — | Multi-agent research (codebase + Antigravity + Codex) |
| `/reflect` | — | — | — | Turn failures into rules (escalation ladder) |

## Legacy Workflows (`/legacy:<name>`)

Older generations, still runnable but superseded. Use `/legacy:wf3-gh` to invoke.

| Legacy command | Successor | Reason archived |
|---|---|---|
| `/legacy:boris1-h` | `/boris2` | Manual plan iteration replaced by Agent Teams |
| `/legacy:wf1-gh` … `/legacy:wf11` | `/wf15` / `/wf16` | Pre-3-cops, pre-modern-primitives |
| `/legacy:wf12` | `/wf15` / `/wf16` | 3-cops base — superseded by fast-iteration variants |
| `/legacy:wf14` | `/wf15` / `/wf16` | Fast TDD without reviewers — superseded by wf15 (adds MCP option) |
| `/legacy:ddr` | `/ddr2` | Manual gates → autonomous |

## Suffix Legend

| Suffix | Meaning |
|--------|---------|
| `-g` | Antigravity CLI (`agy -p`) reviewer — Gemini-MCP successor (Gemini CLI sunsets 2026-06-18) |
| `-c` | Codex MCP reviewer |
| `-h` | human gate |
| no suffix | Anthropic-only + autonomous |

## Quick Pick

| Need | Use |
|------|-----|
| Full auto, Anthropic-only | `/boris2` |
| Modern Claude Code (Agent + worktree) — **default for new work** | `/wf16` |
| Slow suites + external reviewers | `/wf15 -cg` |
| Recursive task decomposition | `/ddr2` |
| Smart contract review | `/sc-audit` |

---

**Tip:** Run `/wf` anytime to see this reference. Legacy commands at `/legacy:<name>`.
