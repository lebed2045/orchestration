# Shared setup for Claude Code and Codex

Updated: 05-nov-2026.

Keep one source checkout and let each selected agent discover it through local links. This works on one Mac or on a macOS host and UTM macOS guest. Reading this guide does not authorize installation: review [components](skill-review.md), then select them explicitly.

## What travels with a clone

- `skills.json`, `scripts/skills.py`, this guide and `dependencies.json`: public registry, registration tool, instructions and optional source pins.
- `shared/skills/`: common TLDR and reflection behavior. `.claude/` and `codex/.agents/skills/` contain native entrypoints and other workflows.
- `vendor/`: ignored third-party source; a fresh clone must reconstruct an approved dependency at its pinned commit.
- `global/`: ignored personal rules, incident history, registration receipts and backups. A fresh clone does not include this owner's private files.
- `legacy/skills/`: inactive historical instruction copies preserved during consolidation.

Ignored rules, history and vendor source are outside this repository's Git rollback. Preserve backups; use private version control if private rule history is needed. Keep public setup documentation outside `global/`.

## One source, local discovery

The host/VM constraint is: **“keep all code, data and intermediates inside the user-designated shared root.”** Discovery symlinks live in each tool's home; sources, test artifacts and recovery data stay in this checkout. The user confirms the VM agent will use this same folder. Its current mount spelling, home registrations and runtime discovery remain unconfirmed from the host.

Run the tool on the machine whose home is being configured, from that machine's view of the checkout. Host and guest may use different mount paths: never copy the host's absolute symlink targets to the guest. No SSH is needed if the VM agent executes the command itself.

Selected sources map individually to:

- Codex: `~/.agents/skills/<name>`.
- Claude: `~/.claude/skills/<name>`, or `~/.claude/commands/<name>.md` for native command workflows.
- Reflection history: `~/.codex/reflections` and `~/.claude/reflections` point to separate `global/inbox/<machine>-<agent>/reflections` folders (unreviewed; see `docs/reflection.md`). `<machine>` is exactly `host` or `vm`.

TLDR and reflection adapters read one shared core each. Reflection uses the same Python recorder, with an explicit engine parameter; it retains historical ledger views and refines project rules during authorized work. Global recording creates proposals only: [explicit review and approved apply](reflection.md) own all global changes. Recurrence never generates automatic halts. Personal global instruction links are separate from skill registration.

Official discovery references: [Codex skills](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills) and [Claude skills](https://code.claude.com/docs/en/skills#choose-where-skills-load). Filesystem links do not establish that an active session loaded a skill.

## Preview and apply selected links

From the actual checkout on each machine, inspect the current state. These commands write nothing:

```sh
python3 scripts/skills.py inventory
python3 scripts/skills.py --machine host plan --engine both --skill tldr --skill reflect
```

Use a distinct stable label for each machine, such as `host-my-mac` or `vm-my-mac`. Do not give host and guest the same label. After explicit component selection, apply that exact preview:

```sh
python3 scripts/skills.py --machine host apply --engine both --skill tldr --skill reflect --confirm
python3 scripts/skills.py --machine host status --engine both --skill tldr --skill reflect
```

The VM agent runs the same commands from its mount, replacing only the machine label with its distinct VM label. The default home and checkout root resolve locally. Python 3.9 or newer is required; the tool uses only the standard library.

`apply` refuses missing sources, conflicting targets, unsafe paths and duplicate legacy registrations before changing discovery paths. Existing targets require `--replace`; retiring old discovery copies additionally requires `--retire-legacy`. These flags are explicit migration choices, not cleanup. Review the paths before authorizing them. Existing files, directories and dangling symlinks move into uniquely named backups rather than being overwritten. Unrelated installed skills remain in place.

Selecting reflection also routes its agent ledger. Existing home-folder history is copied into the shared destination, checked, then the original is preserved in the backup. If histories differ, migration stops for an explicit merge. New project reflections use `--central`, updating project rules and recording incidents in the shared agent ledger; older project-only history remains in its project. The tool does not configure reviewer bridges, MCP servers, hooks or global rule links.

A registry entry is not a complete dependency installer. `research`, `think`, `wf` and browser verification still require their documented support files, transports and project setup; review those dependencies separately before global activation. No claim of readiness for those larger workflows follows from a successful link.

## Receipts and recovery

Each changed apply prints a receipt under `global/registrations/<machine>/<timestamp>/receipt.json`. Keep its exact absolute path. Restore on the same machine/home, using that path:

```sh
python3 scripts/skills.py restore --receipt <absolute-receipt-path> --confirm
```

Restore refuses user-modified targets and restores preserved predecessors. Generated symlinks are retained in the receipt's recovery directory. Shared reflection history, source directories and backups are never deleted. Expected exceptions during apply trigger rollback; receipts distinguish applied, rolled-back and recovery-required states. Restore journals each completed step; after an ordinary I/O failure, resolve its cause and retry the same receipt. Process interruption or power loss can require manual journal inspection; this is not a crash-proof transaction system.

The tool locks concurrent mutations for the same resolved home using `flock`; network-filesystem lock semantics are untested. Do not run simultaneous host/guest migrations into the same reflection destination. Registration does not coordinate concurrent reflection writes.

The old `scripts/link-globals.sh link` migrates its entire list, including bridges and a hook. It is not a selected-skills installer. Do not use it as a shortcut for this procedure.

## Optional pinned Superpowers source

`dependencies.json` lists upstream 6.4.2 and its immutable commit. `selected_skills` is empty pending selection. See the [component review](skill-review.md) for per-skill effects and unresolved compatibility work.

After explicit selection, obtain the full source at `vendor/superpowers/6.4.2`, retaining its license and relative supporting files. No downloader is included; acquisition must use a separately approved standard Git operation, without running install scripts or hooks. The registration tool requires the pinned Git HEAD, a clean source tree and the listed reference SHA-256 values. Named checksums cover only those files, not the entire package audit.

Both tools can link compatible selected skills from that one source directory. The tool does not reproduce native plugin registration, namespaces or startup hooks. Upstream recommends [native per-tool installation](https://github.com/obra/superpowers#installation). Check companion and bootstrap behavior before replacing it. Preserve native installations until their replacements are demonstrated and removal is explicitly authorized. Never move or rewrite managed plugin caches.

A detected native package cache blocks manual registration conservatively; a cache alone does not prove activation. After separately verifying native deactivation, `--native-disabled superpowers` records that attestation in the receipt. It is not an API check or a way to disable the plugin. The host's existing Superpowers remains separate from first-party TLDR/reflection registration.

## Updates and four-session checks

An edit to a shared source is visible through all resolving links. New sessions should load the edited instructions; existing sessions can retain old context. Committing records first-party history but is unnecessary for visibility on the same disk. Separate clones need their own update. Ignored vendor edits do not travel through Git: keep the vendor pristine and store reviewed customizations as tracked patches or a separately named first-party skill.

Check Codex and Claude separately on host and VM in fresh sessions: list available skills, invoke TLDR on known text, and exercise reflection dry-run before a real incident. Confirm the ledger routes to the intended shared machine/agent folder. Legacy Claude history needs a confirmed causal association through the optional `recurrence_of` input field; the recorder validates that ID and preserves old rows. Do not manufacture incidents to inflate recurrence. Filesystem tests do not prove these four runtime paths.

A missing shared mount is a setup failure. Do not make a local fallback copy or mount/unmount automatically. A moved checkout requires explicit link registration at its new path. `status` reports link health and integrity information; it cannot prove active-session loading or native-plugin state.
