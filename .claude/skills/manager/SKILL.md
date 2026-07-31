---
name: manager
description: Human-supervised program orchestration for decomposing a specification into dependency-aware tracks, assigning Claude Code track leads that run /cc in isolated git worktrees, supervising them through native cmux agent teams, and integrating only verified results. Use only when the user explicitly invokes /manager for a multi-track implementation effort.
argument-hint: "<specification or implementation objective>"
disable-model-invocation: true
---

# Manager

**Updated:** `22-jul-2026`

Print `manager (22-jul-2026)` as the first response line of every run.

Treat `$ARGUMENTS` as the exact program objective. Act as the single program orchestrator and integration owner. Delegate bounded tracks to Claude teammates; each teammate is a track lead that invokes `/cc` for its track. Do not invoke `/wf`, create a second manager layer, or let teammates create agent teams.

## Invocation modes

- `/manager --plan-only <objective>`: inspect and return the dependency DAG, track boundaries, risks, and proposed verification without creating files, worktrees, tasks, or teammates.
- `/manager --smoke-test`: validate the exact installed Claude + cmux + Codex + `/manager` + `/cc` composition in a disposable repository and record a compatibility receipt for the current target repository without changing its working tree.
- `/manager <objective>`: run the production workflow below. Require a compatible smoke receipt before fan-out.

Strip only whole-token mode flags. `--plan-only` and `--smoke-test` are mutually exclusive. On conflict, report it and stop without mutation.

## 1. Preflight

Before creating tasks, worktrees, or teammates:

For `--plan-only`, run step 1 plus the read-only baseline discovery needed for section 2, return the plan, and stop. Skip the cmux, smoke-receipt, and run-directory steps.

1. Read the target repository instructions, the supplied spec, relevant architecture, implementation, tests, and the final output stage of affected pipelines.
2. Verify the four variables documented by cmux for a `cmux claude-teams` session: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `CMUX_SOCKET_PATH`, `TMUX`, and `TMUX_PANE` must be non-empty. Record presence only; never print the socket values. If any is absent, stop before mutation and tell the user to restart with `cmux claude-teams`. Never fall back to raw `cmux send` orchestration.
3. Resolve the cmux executable with `command -v cmux`; on macOS, check `/Applications/cmux.app/Contents/Resources/bin/cmux` as the fallback. Record `cmux --version`, then run `cmux claude-teams --help` to prove the launcher exists.
4. Prove that `/cc` is available from the target repository or the user's Claude skill directory. If it is missing, stop; a generic Claude coding fallback would break the required role boundary.
5. Resolve the absolute target Git common directory with `git rev-parse --path-format=absolute --git-common-dir`.
6. Compute a compatibility fingerprint from `claude --version`, `cmux --version`, `codex --version`, and SHA-256 hashes of the resolved `/manager` and `/cc` `SKILL.md` files. In production mode, read `<target-git-common-dir>/manager/smoke/<fingerprint>.md` and require a successful receipt for that exact fingerprint; if none exists, stop and tell the user to run `/manager --smoke-test`, with no unverified bypass. In smoke mode, use the fingerprint as the candidate receipt identity and continue without a pre-existing receipt.
7. Record the repository root, current branch, `HEAD`, all worktrees, complete dirty-path baseline, and the narrow and full verification commands.
8. Discover the reproducible lane setup and readiness checks from lockfiles, package-manager scripts, `.worktreeinclude`, and repository instructions. Copy only gitignored files explicitly declared safe for worktrees; never infer or copy secrets. If dependencies or tests cannot be provisioned reproducibly in a fresh lane, block fan-out before spawning teammates.
9. If the objective depends on uncommitted user changes, do not pretend a clean `HEAD` contains them. Ask once whether to use the current worktree as the integration lane or wait for a user-provided committed baseline. Never stash, reset, clean, or commit user work to manufacture a baseline.
10. Create the collision-safe run directory under `<target-git-common-dir>/manager/runs/<run-id>/`, not in the working tree. Record the objective, baseline, plan, state ledger, event journal, and integration evidence there. The manager alone writes the ledger.

Hard-stop if native agent teams, `/cc`, a trustworthy source baseline, or a safe integration lane is unavailable.

### Smoke-test gate

Run this only for explicit `--smoke-test` mode:

1. Create a disposable Git repository with a local baseline commit and two worktrees under a fresh system temporary directory. The commit and branches must exist only inside this run-owned repository. Record and validate the exact paths before any cleanup.
2. Create one native team task and one teammate. Require the teammate to prove `/cc` discovery, native task updates, direct messaging, idle delivery, and the exact lane repository/branch/`HEAD` using `git -C <lane>`.
3. Have the teammate invoke `/cc` on a tiny deterministic behavior change. The `/cc` contract must pass the lane's absolute path as `cwd` to every Codex call; direct teammate file edits are forbidden.
4. Verify both `/cc` gates, the lane-only dirty delta, and the narrow test. Confirm the original target repository's dirty-path set did not change.
5. Exercise the no-commit integration sequence in section 6, including a new file, into the second disposable worktree and rerun the test there.
6. Add a deliberate out-of-ownership sentinel only inside the disposable lane, prove the scope verifier rejects it, then remove that run-owned sentinel before continuing.
7. Capture team lifecycle evidence, shut down only the smoke teammate, and clean up the native team. Remove only the validated disposable paths created by this smoke run.
8. Write a receipt under `<target-git-common-dir>/manager/smoke/<fingerprint>.md` containing Claude/cmux/Codex versions, skill hashes, exact commands/exits, task/message/idle evidence, lane and integration checks, contamination-detector evidence, and both `/cc` verdicts. A partial or failed smoke test writes no success receipt.

Stop after reporting the smoke result. Do not continue into a production objective in the same invocation.

## 2. Decide whether to fan out

Build a dependency DAG before spawning anyone. A parallel track is eligible only when it has:

- an independently useful deliverable and acceptance check;
- no unresolved interface dependency on another runnable track;
- disjoint mutating path ownership;
- a source baseline that can be reproduced in its worktree;
- enough work to outweigh coordination and integration cost.

Serialize foundation work, shared contracts, migrations, generated lockfiles, and hot files through the manager or an explicit predecessor track. Never assign the same writable path to two live tracks.

If fewer than two tracks are safely runnable, do not create a team. Report the blocking dependency and recommend one `/cc` run instead. More agents are not a success metric.

Before dispatch, show the user a compact track plan:

| Track | Objective | Depends on | Owned paths | Acceptance evidence | Integration order |
|---|---|---|---|---|---|

Proceed without another question unless the plan changes authority, destructive scope, or externally consequential behavior.

State one residual limitation with the plan: current native agent teams do not enforce teammate CWD. This workflow compensates with exact `/cc` `cwd` contracts plus source- and integration-lane delta audits; the smoke receipt proves that composition for the current fingerprint.

## 3. Create lanes and delegation contracts

Create the minimum useful number of teammates. Before spawning them, the manager creates every lane as a real Git worktree on a unique `manager/<run-id>/<track-id>` branch under a validated fresh temporary root. Run the recorded setup and readiness checks in each fresh lane and record their exits. Record track ID, teammate, absolute worktree, branch, baseline `HEAD`, and exact owned paths. Reconcile the mapping with `git worktree list` before the first delegation.

Native agent teams do not provide worktree isolation. Bind each teammate operationally by contract: the teammate must perform all repository inspection with `git -C <absolute-worktree>`, invoke `/cc` with that worktree as the selected working repository, and pass the same absolute path as `cwd` to every Codex MCP call. The teammate must not use direct file-editing tools. Before approving work, require its lane receipt (`git -C` top level, branch, `HEAD`) and prove that the integration lane's baseline dirty-path set has not changed.

Do not commit or merge unless the user explicitly requested it. By default, keep track changes uncommitted and integrate complete binary diffs into the integration lane after verification. Preserve all generated worktrees and branches at handoff unless cleanup was explicitly authorized.

Create one native team task per track and encode DAG dependencies in the shared task list. Give each track lead this complete contract:

```text
TRACK: <id and objective>
SOURCE: <repo, baseline HEAD, prerequisite artifacts>
LANE: <worktree, branch, owned paths>
CODEX_CWD: <absolute worktree path required on every Codex MCP call>
SETUP: <already-run provisioning command and readiness evidence>
FORBIDDEN: <shared or other-track paths; git commit/merge/push/reset/clean/stash>
DEPENDENCIES: <task IDs and resolved interfaces>
ACCEPTANCE: <behavior, tests, review evidence, completion conditions>
VERIFY: <narrow and proportionate full commands>
REPORT: <HEAD, complete changed paths, tests with exits, /cc gate verdicts, blockers>
STOP: <ownership conflict, missing authority, repeated cause, unexpected baseline>

Use git -C with the assigned absolute worktree for every repository check. Do not
edit files directly. Invoke /cc with this single-track contract and require every
Codex call to use CODEX_CWD. Do not create teammates or broaden scope. Mark the task
ready only after /cc has approved both gates and the required verification has run.
```

Dispatch through Claude Code's native agent-team task and messaging tools. Let cmux render teammates as native splits. Do not drive teammates with terminal keystrokes.

## 4. Maintain desired and observed state

Use this state machine:

```text
PLANNED -> DISPATCHED -> WORKING -> READY -> VERIFIED -> INTEGRATED
                            |          |          |
                            +-> INPUT_REQUIRED    +-> FAILED
                            +-> BLOCKED
                            +-> FAILED
```

Native task acceptance proves `DISPATCHED`, not `WORKING`. Move state only with the following evidence:

- `WORKING`: a target-session update plus useful artifact movement inside the assigned lane, such as a relevant diff, test result, or reviewed plan, while the integration-lane baseline remains unchanged;
- `READY`: the track lead's structured report and completed native task;
- `VERIFIED`: manager inspection confirms scope, diff, tests, and `/cc` gate evidence in the assigned worktree;
- `INTEGRATED`: the verified track diff is present in the integration lane and the required integration checks pass.

Keep these ledger fields for every transition:

```text
track_id, objective, dependencies, owner, worktree, branch, owned_paths,
session_id_or_surface_id, state, last_observed_at, HEAD, changed_paths,
test_evidence, review_verdict, blocker, retry_count, next_action
```

Use native task updates, teammate messages, idle/error notifications, git state, tests, and review artifacts as the primary signals. Use cmux screen capture only to diagnose a suspected stall; screen text, process existence, CPU use, and transport acknowledgements are never completion evidence.

Reconcile on every state transition and at a phase-appropriate watchdog interval. Do not hard-code a universal polling interval. Record every nudge, retry, replan, and user escalation in the event journal.

Classify failures before retrying. Set a bounded same-cause retry budget in the plan; a repeated identical failure must trigger replan or escalation, never an endless nudge loop. Preserve partial work and evidence.

## 5. Verify each track

When a lead reports ready, independently inspect its lane:

1. Confirm worktree, branch, and `HEAD` still match the ledger.
2. Enumerate tracked, staged, unstaged, and untracked paths; reject any path outside ownership.
3. Inspect the complete diff and relevant new files.
4. Confirm `/cc` Gate 1 and fresh-Claude Gate 2 both approved and that the reported commands/results are present.
5. Rerun the narrow acceptance check and the proportionate full check in that worktree.
6. Compare against baseline and record the regression delta. A green-before/red-after result is the manager's regression until proved otherwise.

Return valid findings to the same track lead for a bounded `/cc` fix cycle. Do not edit a track's files from the manager lane while its lead is active. Mark missing proof `UNVERIFIED`; never promote it to `VERIFIED` from prose consensus.

## 6. Integrate in dependency order

Integrate only verified tracks and only into the recorded integration lane.

For the default no-commit path:

1. Enumerate the lane's complete delta with `git status --short --untracked-files=all` and reject paths outside ownership.
2. Mark each verified owned untracked file with `git add --intent-to-add -- <paths>` in the generated track worktree so `git diff HEAD` includes it without staging content or creating a commit.
3. Save `git diff --binary HEAD -- <owned-paths>` to the track patch under the run directory. Inspect `git diff --name-status HEAD -- <owned-paths>` and require its path set to equal the verified track delta.
4. Run `git apply --check <patch>` in the integration lane, then apply that exact patch. Never use `--3way` to conceal an unexpected baseline mismatch.
5. Re-enumerate the integration-lane delta with `git status --short --untracked-files=all` and require it to equal the cumulative expected paths.
6. Apply one track at a time in dependency order and rerun that track's acceptance checks after application.
7. Perform shared-contract or cross-track edits serially in the integration lane after all prerequisite tracks are present.

If a diff does not apply cleanly, stop integration, preserve both lanes, and replan. Do not resolve a semantic conflict by choosing one side mechanically.

After all tracks are present, run the integration suite, lint/type/build gates, and any end-to-end check required by the target repository. Inspect the final combined diff and compare it with every track's owned-path contract.

## 7. Complete or stop safely

Before claiming program completion, prove that every planned track is either `INTEGRATED` or explicitly excluded by the user, every required gate is green, the final dirty-path set is understood, and no live task remains falsely marked complete.

Report:

| Track | Worktree / branch | Final state | Changed paths | Tests | `/cc` reviews | Integration evidence |
|---|---|---|---|---|---|---|

Include the target repository's required completion receipt, exact setup and verification commands with exit codes, integration-lane path, remaining worktrees/branches, the contract-only CWD limitation, unresolved risks, and any `UNVERIFIED` boundary.

Request teammate shutdown only after evidence is captured and work is integrated or intentionally preserved. Close only teammates created by this run. Never kill unrelated cmux workspaces or sessions.

On any stop condition, preserve all worktrees and user changes, identify the failed phase and last verified state, and give one concrete next action. Never reset, clean, stash, force-delete, or silently discard partial work.
