# Shared skill consolidation implementation plan

Updated: 15-oct-2026. Implements the six-step plan approved in chat.

Goal: maintain skill instructions once in this shared checkout, register selected sources through local links, and demonstrate changes in fresh sessions without duplicate activation.

Constraints: all code, tests, receipts and backups stay under the designated shared root; only discovery links live in tool home directories. Work in the user's existing orchestration checkout on `master`, preserving earlier uncommitted setup documentation. No commits, deletion of prior versions, dependency installation or component activation without the corresponding authorization.

Implementation is inline under the executing-plans and TDD skills. The user's approved live-checkout consolidation is the working-tree choice; do not switch to another base or install packages for this task.

1. Add a source/target registry and a Python standard-library command with read-only inventory, plan and status; explicit apply; transaction receipts; and restore. Test real filesystem effects using isolated homes under `codex/temp/`.
2. Store TLDR and reflection instructions in shared cores, with thin native adapters. Preserve prior instructions and reuse the existing tested reflection recorder; keep incidental workflow redesign outside this migration.
3. Record dependency/skill review, costs and source provenance. Keep third-party selection empty pending the user's component selection; do not change managed plugin caches.
4. Demonstrate registration, idempotence, changes through links, conflicts and restore using isolated test homes. Migrate real host targets only after selection. The VM agent runs the same command from its view of this checkout.
5. Update the public guide and entrypoints with actual commands and separate source integrity, link health and active-session discovery. Obtain one independent review of the finished change and address material findings.

Review focus: source/target traversal and symlink parents; preservation of existing folders and dangling links; partial failures and restore after user edits; duplicate legacy/plugin discovery; unavailable source or moved share; simultaneous apply/restore; different host/guest path spellings.

Progress and rulings are recorded in `codex/temp/skill-consolidation/progress.md`; test artifacts are preserved there and under `codex/temp/skill-link-tests/`.
