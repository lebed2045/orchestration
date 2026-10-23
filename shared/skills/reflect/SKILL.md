---
name: reflect
description: Use after a confirmed agent mistake or when the user explicitly requests a reflection or postmortem. Repeated discussion of one incident is not a new incident.
---

# Reflect

**Updated:** `15-oct-2026`

Acknowledge the concrete deviation once, answer the user's question and correct the affected work within the authorized scope. Keep the incident record brief. Recording a rule does not prove prevention worked.

## Scope and modes

- Default: record the most recent confirmed incident once. Check the relevant ledger first; do not log or escalate again merely because the user asks why the same incident happened.
- `--list`: inspect the ledger without writes. `--dry`: preview recording without writes.
- A lesson specific to a project belongs in that project. A cross-project lesson belongs in the agent's global ledger. Do not duplicate it in both scopes.
- Optional `-c` review means the other main agent; `-g` means the configured Gemini bridge. Use only a requested, available reviewer through its configured transport. No model calls are needed for default recording.

## Shared recorder

Resolve this file's actual location. The checkout is three directories above its containing folder. Both engines use the one recorder at `codex/.agents/skills/reflect/scripts/reflection.py`; inspect its `--help` and record-input schema in that file before constructing a new incident.

Use `--agent codex` or `--agent claude` according to the actual runtime. Never guess the runtime from the project directory. The helper defaults to Codex for backward compatibility, so Claude must pass its agent explicitly.

```sh
python3 <checkout>/codex/.agents/skills/reflect/scripts/reflection.py list --agent <agent> --scope global
python3 <checkout>/codex/.agents/skills/reflect/scripts/reflection.py record --agent <agent> --scope global --input <incident.json>
```

For project scope, pass `--scope project --project-root <project>`. This mode also updates that project's rules file: use it only when that exact file change is authorized; otherwise use `--dry-run` and report the pending rule change. The helper chooses `AGENTS.md` and `.codex/reflections` for Codex, or `CLAUDE.md` and `.claude/reflections` for Claude. For global scope it uses that agent's configuration folder and `reflections/`; `--agent-home` supplies an explicit configuration folder when needed.

Keep the input JSON and any intermediates in the designated shared workspace. Before recording globally in a shared setup, establish that the ledger is routed into `global/log/<machine>-<agent>/reflections`; if it is not configured, report that rather than silently creating a second local incident history. Do not create or rewire links during a read-only request.

The recorder retains the existing four ledger views and recurrence history for compatibility. Match a recurrence by causal pattern, not frustration or wording. Legacy Claude rows have no `pattern_key`: inspect their root causes and, for a confirmed match, set the incident input's optional `recurrence_of` to the existing predecessor ID. The recorder validates the ID, carries its strike chain forward, and preserves historical rows unchanged. Do not silently call a matching legacy incident a first occurrence; preview or report uncertainty when the association is unclear. Inspect existing escalation and obey the active user constraints; do not manufacture stronger restrictions merely to increase a level. Global recording leaves the shared rules file unchanged.

## Rules and effectiveness

After recording, add or tighten at most one global rule only if the lesson generalizes and the update is authorized. Reuse an existing rule when it already covers the cause. Preserve unrelated rules and the file's line budget. Keep full incident detail in the ledger.

Report the incident as **recorded; prevention untested** until an actual check demonstrates the changed behavior. Never report “fixed” or “failure addressed” solely because files were written. Use the user's concise TLDR format and resume the original authorized task.
