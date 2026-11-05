---
name: reflect
description: Use after a confirmed agent mistake, for an explicit reflection or postmortem, or to review global reflection proposals. Apply global changes only when the user explicitly approves their diff.
---

# Reflect

**Updated:** `05-nov-2026`

Correct the affected work within its authorization and record each confirmed incident once. Repeated discussion of one incident is not a new strike. Recording is **prevention untested**, not proof the problem is fixed. Resume the original task without a ritual approval question.

## Resolve the scope

A lesson about this project updates its concise instructions and is recorded once in the current machine/agent's central shared ledger, with the project named. During authorized implementation/correction, update that local rule immediately when it adds useful information. A read-only request does not authorize local edits: preview instead. Local scope means every agent working in this project, not a private rule for this one agent.

A lesson that generalizes across projects belongs in the current machine/agent's shared global log. **Global reflection only records a proposal. Never edit global instructions during recording, even if the incident seems important or recurrent.** Global changes require the user's explicit approval of a reviewed diff. Plain-language review and approval requests are sufficient; the CLI helpers below are optional conveniences, not a mandatory protocol. Prefer a test/tool fix over accumulating redundant rules; recurrence never automatically adds halts or stronger restrictions.

Resolve this shared file's actual path; the checkout is three directories above its containing folder. The one helper is `codex/.agents/skills/reflect/scripts/reflection.py` in that checkout. Inspect its help/input schema when needed. Pass `--agent codex` or `--agent claude` according to the actual runtime; Claude must not rely on the helper's Codex default.

## Record

Record actual behavior (`what`), expected behavior (`expected`), evidence references (`evidence`: list of strings), root cause, impact, immediate correction and a WHEN/DO/PROVE prevention proposal. Retain the existing required fields in the helper. Use `reviewer: "none"` unless a real reviewer participated; never invent review or successful prevention.

For a global candidate from either scope, supply `proposed_global_rule` as one short Markdown bullet. Optionally supply `replaces_global_rule` as the exact existing bullet to refine. Use null when no global rule is justified. A full incident belongs in the log, not in the global instructions. Legacy rows without proposals remain review evidence and are never silently rewritten or discarded.

```sh
python3 -B <checkout>/codex/.agents/skills/reflect/scripts/reflection.py record --agent <agent> --scope global --input <incident.json>
python3 -B <checkout>/codex/.agents/skills/reflect/scripts/reflection.py record --central --agent <agent> --scope project --project-root <project> --input <incident.json>
```

The global home ledger must resolve into this checkout's `global/inbox/<machine>-<agent>/reflections` (the unreviewed inbox); if not configured, report it rather than creating a second local history. Use `--central` for project recording: the incident goes to the configured shared agent ledger, not a second project-local log. The helper requires a resolving link into this checkout's `global/inbox`. Preserve old project-only logs without silently migrating them; inspect them when relevant to recurrence or review, and report that central history alone does not include them. The legacy CLI without `--central` remains backward-compatible but is not the default skill workflow. Project mode updates `AGENTS.md` for Codex and `CLAUDE.md` for Claude; a local `@AGENTS.md` import uses that shared project file. The helper refuses project targets that alias global instructions, escape the project, or use shared-global hardlinks. Preserve existing project wrapper/symlink arrangements.

Legacy Claude rows have no `pattern_key`: inspect their actual causes and, for a confirmed recurrence, set optional `recurrence_of` to the historical incident ID in the selected ledger. If the predecessor exists only in an old project-local log, cite its file/ID in evidence instead; do not invent a central predecessor or silently migrate that history. Recurrence counts cover the selected ledger and project. Do not infer recurrence from frustration or log the same incident twice.

`--list` maps to the helper's `list` command (use `--central` plus project scope/root to filter the central log to that project); `--dry` maps to `record --dry-run`. Both are read-only. Keep input JSON and intermediates in the designated shared workspace. No model calls are required for recording. Optional `-c`/`-g` reviews run only when requested, through their configured available transports.

## Review global proposals — explicit user request

A normal request to review shared reflections is sufficient. Read and follow `docs/reflection.md` in the resolved checkout. Read the actual incidents and current rules, exercise judgment about causes and scope, and propose only justified changes. You may review directly without generating JSON or invoking a helper. User approval is required before editing global rules.

`$reflect --review` (Claude: `/reflect --review`) maps to:

```sh
python3 -B <checkout>/codex/.agents/skills/reflect/scripts/reflection.py review
```

This reads all four `global/inbox/` folders (and any older labels still there), reports host/VM × Codex/Claude coverage, groups recorded causal keys and proposes an exact diff. It does not inspect live VM configuration or prove four active sessions loaded the rules. Report missing/unreadable sources and competing proposals; do not silently count missing data as a clean review.

Evaluate evidence, scope, redundancy and conflicts. Distill durable lessons, preserving unrelated rules and the global line budget. The default helper deduplicates matching recorded proposals; it does not replace the agent's semantic review. `--select <source-folder>:<incident-ID>` selects explicit proposals; use the reported `source:ID@line` token for duplicate legacy IDs. For a synthesized/legacy-backed rule, a caller-authorized `--proposal <JSON>` supplies `edits: [{old: null-or-exact-bullet, new: "- ...", sources: ["source:ID"]}]`; the generated review attaches incident fingerprints.

Default review prints JSON only. `--output <new-file.json>` saves it only when the user asks to save a review artifact. Show the proposed diff before any apply. Review requests never imply approval to change global rules.

## Apply global proposals — explicit approval only

The user can approve a proposed diff in ordinary language. Re-read the target, preserve a recovery copy and apply only those approved changes; special flags or JSON are not required. The helper below is an optional way to enforce the same mechanical checks.

`$reflect --apply <review.json>` (Claude: `/reflect --apply <review.json>`) maps to:

```sh
python3 -B <checkout>/codex/.agents/skills/reflect/scripts/reflection.py apply --review <review.json> --confirm
```

Run only after the user explicitly approves that exact global diff. If no file was saved, the approval authorizes saving that exact reviewed JSON as an audit artifact before applying; use a unique named path in the shared checkout. Do not regenerate a different proposal and call it approved. The helper rejects stale global content, altered evidence/diffs, unresolved source errors/conflicts and budget overflow. When stale, re-review and show the changed diff; the earlier approval does not cover it.

Apply preserves a before-copy and receipt under `global/archive/applied/`. It never commits, pushes, deletes logs or rewires global links. Preserve historical rows and evidence. New instructions may need fresh sessions; report filesystem/CLI checks separately from untested model-session behavior. See `docs/reflection.md` for artifact locations, size limits and recovery.

## Renew — after an applied review

When the user says the review is finished, run `reflection.py renew --date <YYYY-MM-DD>` (dry run), show what moves, then `--confirm`. It copies `global/AGENTS.md` to `global/archive/<date>/AGENTS.md`, moves every inbox file there, and leaves the four inboxes empty. Write `global/archive/<date>/review.md` listing applied and rejected proposals. Inbox = unreviewed; archive = reviewed.
