# Reflection: local learning, manual global promotion

Updated: 27-oct-2026. Implements the user's selected option 1. No additional skill installation, plugin, API, service or scheduled job is involved.

## Everyday use

Codex: `$reflect`; Claude: `/reflect`. After a confirmed mistake, correct the work, record it once, and distinguish untested prevention from a demonstrated fix. Within an authorized implementation task, project-specific lessons immediately refine the project instruction file and record the incident once in the configured central machine/agent folder (the skill passes `--central`). Legacy project-only logs are preserved, not silently migrated. Read-only requests preview instead. A project rule applies to everyone working in that project.

Cross-project lessons only become proposals in the shared global logs. Recording never edits global instructions. Recurrence is diagnostic history, not an automatic escalation into hard gates or halts. Existing historical records remain unchanged.

Both engines load global and project guidance. Project Codex uses `AGENTS.md`; project Claude uses `CLAUDE.md`, or its existing `@AGENTS.md` import/symlink to that common project file. The recorder refuses aliases/hardlinks to global instructions and paths that escape the project. It does not configure new wrappers or links.

## Review, then explicitly apply

Plain-language requests are sufficient. Follow [the judgment-based review guide](reflection-review.md): read the incidents and current rules, propose justified changes, and wait for explicit approval before editing global instructions. The helper commands below are optional mechanical conveniences; no special command or JSON format is required from the user.

From the orchestration checkout, the underlying commands are:

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py review
python3 -B codex/.agents/skills/reflect/scripts/reflection.py review --select host-codex:GLO-1
```

Use the documented `python3 -B` invocation: macOS Python can otherwise create bytecode caches before application code starts. The first command is read-only and prints JSON. It scans all immediate `global/log/*/reflections/incidents.jsonl` sources, including old machine labels, and reports the four host/VM × Codex/Claude roles as recorded, empty, missing or unreadable. These are log-coverage states, not proof of active sessions. Malformed, dangling or escaping sources are reported and block a ready-to-apply result. Duplicate legacy IDs retain every row, using explicit `source:ID@line` tokens with warnings; history is never repaired in place.

The agent evaluates causes and proposals, removes duplicates and shows a small exact diff. Different proposals for one causal key require explicit selection or a reviewed synthesis. Old rows lacking proposed text are listed as needing a proposal; their causes do not automatically become rules.

When the user asks to save the review, use a new named file inside the shared checkout:

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py review --output <new-review.json>
```

Its parent must already exist; existing files are never overwritten. Optional `--proposal <proposal.json>` lets the reviewing agent express a synthesized edit with provenance:

```json
{"edits":[{"old":null,"new":"- A concise general rule.","sources":["host-codex:GLO-1","vm-claude:GLO-4"]}]}
```

Use an exact existing bullet instead of null to refine it. Sources must identify real incidents. This input is permitted only as a caller-authorized saved artifact, or as part of an explicitly approved apply; a plain review creates no files.

When using the optional helper, after the user approves the displayed diff, apply that review file:

```sh
python3 -B codex/.agents/skills/reflect/scripts/reflection.py apply --review <review.json> --confirm
```

The corresponding existing skill modes are `$reflect --review` and `$reflect --apply <review.json>` (Claude uses `/reflect`). They are modes of the existing skill, not separately installed skills. `--confirm` records the caller's explicit authorization; it is not permission inferred from an incident or a prior review request.

Apply checks the current global hash, resolved target, exact diff, selected incident fingerprints and line budget. Changed content/evidence requires a fresh review. Named synthesis remains a human-reviewed proposal; the helper cannot judge its semantic quality or prove that a person actually approved it.

Apply changes only `global/AGENTS.md`, preserving its symlink target and existing file permissions. It makes no Git changes. During ordinary write failure it attempts rollback; a simultaneous unrelated user edit is preserved and reported for recovery. Cooperating applies share a lock. A non-cooperating writer/power loss can still require manual recovery; this is not a filesystem transaction across machines.

## Files, sizes and lifetime

All shared workflow code, records and outputs remain inside the user-designated shared root. The host sees `/Users/elpinguino/VM-shared`; the VM's current access is not established by these checks. Each machine resolves its own checkout path. Existing home-directory discovery symlinks are unchanged.

| Artifact | Location | Size / lifetime |
|---|---|---|
| Global incidents and four ledger views | `global/log/<machine>-<agent>/reflections/` | Append-only, variable growth; retained until explicitly cleaned up |
| Legacy project incidents and four views | `<project>/.codex/reflections/` or `.claude/reflections/` | Existing history retained; new skill records go centrally |
| Review/synthesis JSON explicitly requested by caller | Caller-named new file under the checkout | Variable; each input file is capped at 8 MiB; keep as review evidence |
| Global before-copy and apply receipt | `global/reflection-reviews/<timestamp-id>/before.md`, `receipt.json` | Before-copy matches previous rules size; receipt is small variable JSON; durable recovery evidence |
| Apply lock | `global/reflection-reviews/apply.lock` | Empty persistent coordination file |
| Atomic-write/review staging | Per-run temporary folder beside the named output, or temporary file beside the target | Roughly the output size; removed by software on success/failure; no home/cache outputs |

Review limits each read file to 8 MiB and direct log-folder enumeration to 1,000 entries. Output can grow with the number of incidents; inspect its size before saving very large histories. Private `global/` is Git-ignored, so repository Git history does not back up these personal rules or receipts.

A successful CLI apply establishes file behavior only. Check instruction loading in fresh host and VM sessions separately; saving a proposed rule does not demonstrate prevention.
