# Reflection: record → review → apply → renew

Updated: 05-nov-2026. Replaces `reflection-workflow.md` and `reflection-review.md` (kept in `legacy/docs/`).

## The one rule

- `global/inbox/` = **not reviewed yet**. Every agent writes new incidents here.
- `global/archive/<date>/` = **reviewed**. What was applied or rejected is in that folder.

Nothing else holds reflections.

## Where things live

| What | Path | Notes |
|---|---|---|
| Global rules (one file, all agents, host + VM) | `global/AGENTS.md` | Public. `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` link here. |
| Unreviewed incidents | `global/inbox/{host,vm}-{claude,codex}/reflections/` | `~/.claude/reflections`, `~/.codex/reflections` link here. Files: `incidents.jsonl` (source of truth) + `failures.md`, `failures-addressed.md`, `reflection-log.md` (views), `inputs/`. |
| Reviewed history | `global/archive/<YYYY-MM-DD>/` | `AGENTS.md` as it stood after that review + the inbox files it consumed. |
| Apply before-copies + receipts | `global/archive/applied/<id>/` | Written automatically by `apply`; recovery evidence. |
| History before this layout | `global/archive/2026-11-05-pre-cleanup/` | Old `log/`, `_incoming/`, old rules snapshots. |
| Link receipts (machine state) | `global/registrations/` | Written by `scripts/skills.py`; needed to restore links. Not reflections. |
| Project rules | `<project>/AGENTS.md` (`CLAUDE.md` = `@AGENTS.md`) | Project lessons may refine these during authorized work. |

Everything in `global/` except `AGENTS.md` and `README.md` is gitignored.

## 1. Record (any agent, any time)

Claude `/reflect`, Codex `$reflect`. After a confirmed mistake: fix the work, record the incident once into that agent's inbox. Inside an authorized project task, a project-specific lesson may also refine the project `AGENTS.md`. Global lessons are only *proposals* in the incident (`proposed_global_rule`); recording never edits `global/AGENTS.md`.

## 2. Review (when you have time)

Say "review the reflections". Read-only. The agent reads `global/AGENTS.md` and all four inboxes, then for each lesson:

- Establishes what happened vs expected, evidence, cause, and whether prevention was actually exercised. A log line is a claim, not a fact.
- Groups incidents by real cause; doesn't count repeated discussion as new failures.
- Decides where the lesson belongs: code/tests, a project rule, a skill, or global rules. Repetition alone doesn't justify a global rule.
- Prefers refining an existing rule over adding one; stays within the budget line at the top of `global/AGENTS.md`; no automatic escalations or halts.

It presents the few changes worth making with sources, reasons and the exact diff. Helper (optional):

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py review [--output <new.json>] [--proposal <edits.json>]
```

## 3. Apply (only after you approve the diff)

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py apply --review <review.json> --confirm
```

Checks the current hash, exact diff, source incidents and line budget; a stale review needs a fresh one. Changes only `global/AGENTS.md`, saves a before-copy + receipt in `global/archive/applied/`, never touches git.

## 4. Renew (closes the cycle)

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py renew --date YYYY-MM-DD           # dry run: lists what moves
python3 -B codex/.agents/skills/reflect/scripts/reflection.py renew --date YYYY-MM-DD --confirm
```

Copies `global/AGENTS.md` to `global/archive/<date>/AGENTS.md`, moves every inbox file into `global/archive/<date>/inbox/…`, and leaves the four inbox folders empty (the links keep working). Refuses an existing archive folder. Put the review summary (applied / rejected and why) in `global/archive/<date>/review.md`.

## Limits

Each read file is capped at 8 MiB; at most 1,000 inbox folders. Apply is locked against cooperating applies but is not a cross-machine transaction. A successful apply proves the file changed, not that the rule prevents anything; check loading in fresh host and VM sessions.
