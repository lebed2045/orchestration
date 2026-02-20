# /wf - Workflow Quick Reference

Show this table and STOP. Do not execute any workflow.

## Workflow Comparison

| Command | Reviewers | Gates | H | Description |
|---------|-----------|-------|---|-------------|
| `/boris1-h` | — | 0 | 1 | Boris's original (plan iteration with user) |
| `/boris2` | 2×O | 2 | 0 | Boris + Agent Teams (auto) |
| `/wf1-gh` | G+O | 2 | 2 | Basic dual review |
| `/wf2-gh` | G+O | 3 | 2 | Dual review + isolated coder |
| `/wf3-gh` | G+O | 3 | 1 | Anti-regression |
| `/wf4-gc` | G+C+O | 2 | 0 | Auto-fix on review fail |
| `/wf5-gch` | G+C+O | 3 | 1 | Triple review |
| `/wf6-gch` | G+C+O+S | 3 | 1 | Quad review (all 4) |
| `/wf7-gch` | G+C+CS | 2 | 1 | Token-optimized |
| `/wf8-gc` | G+C+CS | 2 | 0 | Autonomous + auto-commit |
| `/wf9-gc` | G+C+CS | 2 | 0 | MCP tools + auto-commit |
| `/wf10-gc` | G+C+CS | 2 | 0-1 | wf9 + optional `-h` flag |
| `/wf11` | 5×Claude | 2 | 0-1 | Anthropic-only (no MCP tools) |
| `/ddr` | (wf3-gh) | — | — | Meta: Divide-Delegate-Reflect |
| `/ddr2` | (wf8-gc) | — | — | Autonomous DDR |

## Suffix Legend

| Suffix | Meaning |
|--------|---------|
| `-g` | uses Gemini |
| `-c` | uses Codex |
| `-h` | has human gate |
| no suffix | Anthropic-only + autonomous |

## Quick Pick

| Need | Use |
|------|-----|
| Simple task, human plan | `/boris1-h` |
| Full auto, Anthropic-only | `/boris2` |
| Full auto, MCP tools | `/wf8-gc` or `/wf9-gc` |
| Auto with optional review | `/wf10-gc -h` |
| Maximum review coverage | `/wf6-gch` |
| Token-efficient | `/wf7-gch` |

---

**Tip:** Run `/wf` anytime to see this reference.
