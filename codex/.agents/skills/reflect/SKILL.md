---
name: reflect
description: Turn confirmed Codex mistakes into durable prevention rules. Use immediately when the user corrects Codex, Codex admits or self-catches a mistake, verification disproves a claim, or the user explicitly asks to reflect, write a postmortem, check recurrence, or strengthen instructions after a failure. Record the incident, update the appropriate AGENTS.md, and escalate repeated patterns from reminder to mandatory proof to a hard workflow gate.
---

# Reflect

Turn a confirmed failure into a short postmortem, a live rule, and an append-only incident record. Do this before resuming the task that exposed the failure.

## Modes

- `$reflect`: address the most recent confirmed failure.
- `$reflect --list`: show incident patterns, levels, strike chains, and the next escalation without writing.
- `$reflect --dry`: preview the rule and ledger changes without writing.
- `$reflect -g`: ask Gemini/Antigravity to tighten the rule through `mcp__agy__agy_ask`, or `~/.local/bin/agy-ask` only when that MCP is unavailable.
- `$reflect -c`: ask Claude through `$HOME/.agents/bin/claude-peer` or `codex/bin/claude-peer` to tighten the rule.
- `$reflect -gc`: obtain both independent reviews before recording.

In Codex, `-c` means Claude. Never ask another Codex instance to be the supposedly independent reviewer.

## Workflow

### 1. Stop and acknowledge

Make the next user-facing update a compact postmortem before any more task implementation or side effects:

```text
Postmortem
Mistake: <what happened>
Cause: <why it happened>
Impact: <what this changed or risked>
Correction: <what happens now>
```

Do not dilute a confirmed correction with defensiveness. Continue the original task only after the reflection has been recorded, or after explicitly reporting why recording is `UNVERIFIED`.

### 2. Read the active instructions and choose scope

Read the applicable `AGENTS.md` files before crafting the rule.

- Use `global` and `~/.codex/AGENTS.md` when the prevention applies across projects.
- Use `project` and the repository's `AGENTS.md` only when the failure depends on that codebase, toolchain, or project convention.
- Do not duplicate a global rule into a project file.

### 3. Check recurrence before choosing a level

Run the read-only ledger view first:

```bash
python3 <skill-dir>/scripts/reflection.py list --scope global
python3 <skill-dir>/scripts/reflection.py list --scope project --project-root <repo>
```

Search `incidents.jsonl` for the same causal pattern, not merely similar wording. Reuse the prior `pattern_key` only when the same prevention rule would have stopped both incidents. Adjacent failures and incidents from another agent runtime are evidence, not automatic strikes.

The script computes escalation mechanically from `pattern_key`:

- L1: first occurrence — reminder rule.
- L2: second occurrence — mandatory current-turn proof.
- L3: third occurrence — hard gate; the task cannot continue until proof is shown.
- L4: fourth or later occurrence — halt and request manual intervention.

Never lower or hand-edit the computed level.

### 4. Craft one concrete rule

Use exactly one trigger, action, and checkable proof:

```markdown
### <Rule title> (ref: <generated ID>)
WHEN <specific trigger>:
DO <specific prevention action>.
PROVE <observable evidence from the current turn>.
```

`PROVE` must name visible evidence such as a quoted current request, command output, a diff, a test result, or a checklist printed before the gated action. “Be careful” and “double-check” are not proof.

For L2+, strengthen proof rather than merely rewording the reminder. The recorder adds the L3 gate and L4 halt language automatically.

### 5. Obtain requested independent review

Give reviewers only the failure, root cause, recurrence chain, computed level, and proposed WHEN/DO/PROVE rule. Ask them to make the proof mechanical and the rule minimal. Do not let a reviewer change scope, suppress the incident, or reduce its level.

### 6. Record through the deterministic helper

Create a temporary JSON input using `apply_patch`, with these fields:

```json
{
  "trigger": "user_correction",
  "what": "One-line failure",
  "root_cause": "One-line causal explanation",
  "impact": "One-line impact",
  "correction": "One-line immediate correction",
  "context": "What was happening",
  "pattern_key": "stable-kebab-case-cause-family",
  "rule_title": "Imperative prevention title",
  "when": "trigger condition",
  "do": "specific action",
  "prove": "mechanically checkable evidence",
  "pillar": "communication",
  "reviewer": "self"
}
```

Then run:

```bash
python3 <skill-dir>/scripts/reflection.py record --scope global --input <json>
python3 <skill-dir>/scripts/reflection.py record --scope project --project-root <repo> --input <json>
```

Add `--dry-run` for `$reflect --dry`. Delete only the temporary input you created after successful recording.

The helper must update the live `AGENTS.md` rule and all four ledger views:

- `incidents.jsonl`: structured source of truth.
- `failures.md`: human-readable postmortems.
- `failures-addressed.md`: scope, rule, recurrence, and status.
- `reflection-log.md`: append-only verbatim rule history.

Each target is replaced atomically, and the helper rolls back earlier targets if a later write fails.

If the helper prints `SIZE_GATE: COMPRESSION_REQUIRED`, back up the target `AGENTS.md`, archive verbose provenance outside the loaded instructions, and perform one conservative compression pass. Never remove or weaken a `WHEN`, `DO`, `PROVE`, `GATE`, `HALT`, level tag, or complete rule. Compare those directive counts before and after; restore the backup if any count drops.

### 7. Report and resume

Report the generated ID, recurrence, level, exact `AGENTS.md` location, and rule in one compact block. Then resume the user's current request under the new rule.

## Installation

Install global discovery and the reflection contract idempotently:

```bash
python3 <skill-dir>/scripts/reflection.py install
```

This creates a source-of-truth symlink under `~/.agents/skills/reflect` and adds a managed reflection section to `~/.codex/AGENTS.md`. It refuses to replace unrelated paths.
