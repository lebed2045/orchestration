# Component review for shared registration

Observed 15-oct-2026. This is a selection sheet, not installation authorization. The implementation and test fixtures are in this working tree; they have not been committed or published.

## First-party selection

Official source: [lebed2045/orchestration](https://github.com/lebed2045/orchestration). Owner: lebed2045. Baseline commit: `592a5b0ad051a06b9138d023047b180046082a04`, plus the reviewed working-tree changes dated 15-oct-2026. These new changes have no release version. Current stars, repository age and release date are unknown: GitHub API requests were rate-limited. Source availability and tests are evidence of behavior, not a security guarantee.

| Component | Execution and dependencies | Measured source size | Context / execution cost |
|---|---|---:|---|
| TLDR | Markdown instructions plus two thin tool adapters; no hooks, services, subprocesses or third-party model calls | 2,401 bytes across active entrypoints/core | Core: 1,060 characters; actual tokens and USD depend on the current model/plan and are unknown |
| Reflection | Same shared core and Python standard-library recorder for both tools; records four ledger views and recurrence; global rules unchanged, project recording also edits that project's rules and requires authorization; optional reviewers require an explicit flag and configured transport | 25,127 bytes including recorder and entrypoints | Local I/O, model context and optional reviewer cost vary; USD unknown |

Sizes are working-tree measurements on 15-oct-2026; supporting test files and UI metadata are excluded. These sources already live in the shared checkout; registration adds small local symlinks, shared receipt JSON, and backups of any replaced targets. Backup size depends on existing files; the tool refuses an individual backup above 8 MiB or 1,000 entries. Reflection history grows with use. No package install, startup hook or daemon is added.

Selecting reflection also selects routing each tool's global ledger to `global/inbox/<machine>-<agent>/reflections`. Existing history is preserved; divergent histories stop the migration. Project reflections remain in that project. The tool does not rewrite global instruction links.

Removal: run `scripts/skills.py restore` against that machine/home's printed receipt. It restores preserved originals and keeps generated links, sources and history in the shared recovery folder. Restore refuses targets changed since registration. Cleanup is a separate explicit action.

**Recommended first activation:** TLDR and reflection for host Codex and Claude; VM agent registers those same sources from the guest mount. Existing Superpowers remains available until its separate source migration is selected and demonstrated.

## Superpowers: separate selection

Official source: [obra/superpowers](https://github.com/obra/superpowers), owner Jesse Vincent (`obra`), MIT license. Pin: **6.4.2**, commit `8ca22dba9a94f28898bbce59f2537ff4d87c747d`; tag object and reference checksums are in `dependencies.json`. Current stars, repository age and latest release date are unknown after API rate limiting. Two installed standalone files match the pinned upstream checksums; this is not a whole-package audit.

The host Codex native plugin is enabled at 6.4.2; its installed package measured 633,790 bytes and its Codex manifest declares an empty hooks object. Host Claude reported no native plugins. VM registrations have not been inspected. Download size for a full pinned Git checkout and native startup behavior on every harness remain unknown.

The rows below are individually selectable components, not an implicit bundle. Every row shares the source/version/license/removal policy above. Context figures are SKILL.md characters, not token or USD estimates; referenced files and subagents add variable context/cost. A manual skill link executes no script by itself, but its instructions can direct the actions listed. Existing user authorization gates still apply.

| Skill | Body characters | Actions / compatibility concerns |
|---|---:|---|
| brainstorming | 17,458 | Design docs; optional visual companion server/browser; commit suggestions need authorization |
| diagnosing-superpowers | 6,883 | Case bundle and seven analyst agents; default `~/.superpowers` output needs adaptation to the shared root |
| dispatching-parallel-agents | 6,052 | Multiple workers; model quota/cost depends on dispatch |
| executing-plans | 20,249 | Ledger, tests and a final independent reviewer; worktree/commit defaults remain gated |
| finishing-a-development-branch | 7,729 | Tests and proposed merge/push/deletion paths; each action needs explicit authorization |
| receiving-code-review | 6,165 | Checks review feedback against source before implementing it |
| requesting-code-review | 2,973 | One independent reviewer; additional model quota/cost |
| subagent-driven-development | 32,358 | Implementers and repeated review agents; potentially substantial variable model quota/cost |
| systematic-debugging | 9,441 | Diagnostic commands, experiments and tests within authorized task scope |
| test-driven-development | 9,556 | Red/green tests; deletion advice cannot override file preservation rules |
| using-git-worktrees | 6,803 | Worktrees and suggested package setup; no implicit permission to install packages or commit |
| using-superpowers | 3,180 | Startup skill routing and companion loading; native bootstrap semantics need per-tool verification |
| verification-before-completion | 3,598 | Fresh commands and evidence before success claims |
| writing-plans | 10,317 | Plan files and execution choices; commit suggestions remain gated |
| writing-skills | 26,523 | Skill changes, pressure tests and reviewer agents; bundled scripts need task-specific review |

Each component's incremental disk footprint depends on its supporting files; it is unknown here. All 15 can reuse a single full pinned source checkout after selection. No dependency downloader is provided. Downloading would be a separate approved standard Git operation, followed by revision/clean-tree/checksum checks. No upstream installation script or hook should be executed during source acquisition.

[Upstream installation](https://github.com/obra/superpowers#installation) uses native integrations per tool. Shared manual skills do not reproduce their registration, namespaces or startup hooks. Before replacement, demonstrate compatible discovery and bootstrap behavior, then obtain explicit native-plugin deactivation/removal authorization. Do not edit managed caches. Uninstall manual links through receipts; preserve source and old installations until explicitly cleaned up.

Third-party selection is currently empty. Superpowers migration is **not ready for activation** until companion/startup compatibility and the chosen native-plugin transition are resolved. The two existing standalone Codex copies also need explicit duplicate retirement when their replacements are registered.
