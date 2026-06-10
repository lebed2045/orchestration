---
name: wf
description: Codex-native fast-iteration TDD workflow equivalent to Claude /wf. Use when the user explicitly invokes $wf, asks for a Codex equivalent of /wf, or asks Codex to build, fix, refactor, or implement code with tiered TDD, verification gates, optional worktree isolation, reviewer passes, and evidence-backed completion.
---

# WF

First response line for every run: `wf v19 (10-jun-2026)`.

This is the Codex-native adaptation of `.claude/commands/wf.md`. Preserve the workflow intent, but use Codex surfaces: `update_plan`, shell commands, available subagents, available MCP/app tools, and explicit degradation notes. Do not call Claude-only primitives such as `TodoWrite`, `EnterPlanMode`, `AskUserQuestion`, or `Agent`.

## Invocation

Use as `$wf [flags] <task>`.

Supported flags:

- `--tier=auto|micro|small|full`; default `auto`.
- `--split-tdd`; default. Run RED then GREEN in separate fresh passes when possible.
- `--unified-tdd`; one pass writes the failing test, then implements.
- `--no-worktree`; default. Work in the current branch.
- `--worktree`; create an isolated git worktree when feasible.
- `-h`; add a human approval checkpoint after planning.
- `-c`; request a Claude reviewer through the local official-Claude bridge. From Codex, `c` means Claude; from Claude Code, `c` means Codex.
- `-g`; request an Antigravity/Gemini reviewer through the agy bridge MCP (`mcp__agy__agy_ask`) when loaded.
- `--commit`; may create commits and merge only after all gates pass.
- `--dry-run`; stop after writing the plan, no source edits.
- `--goal "<criterion>"`; add an explicit success contract to GREEN and final verification.

If the user writes `/wf`, treat it as a request to use `$wf`; explain only if needed.

## Tier Detection

If `--tier` is absent or `auto`, classify the task:

- `micro`: typo, rename, copy/comment-only, version bump, or a short task with no feature/refactor verb.
- `full`: multi-file feature, migration, integration, architectural refactor, or long multi-clause task.
- `small`: everything between those two.

Print the resolved settings before editing: tier, TDD mode, worktree mode, requested reviewers, commit mode, dry-run mode, and task text.

## Workflow

1. Capture context:
   - Run `git status --short`, current branch, current SHA, and identify likely test commands from repo files.
   - Set a run baseline SHA for later diff checks.
   - Create a plan with `update_plan`; keep statuses current.

2. Write workflow notes:
   - Use `codex/.agents/codex/temp/wf/spec.md` for the task spec.
   - Use `codex/.agents/codex/temp/wf/architecture.md` for design, file plan, quick test, and verification commands.
   - For `micro`, keep both files tiny.
   - For `--dry-run`, stop here and summarize the plan.

3. Plan gate:
   - For `-h`, ask the user to approve or edit the plan before source edits.
   - Without `-h`, continue autonomously after writing the plan.

4. RED phase:
   - Add or update the narrowest failing test that proves the requested behavior.
   - Run only the quick test and capture the failure.
   - If no test framework exists, create the cheapest deterministic verification possible and label the limitation.

5. GREEN phase:
   - Implement the smallest change that satisfies the RED test and the optional `--goal`.
   - Keep the loop to five iterations. If the same failure repeats twice, stop and report the blocker.
   - Prefer fresh subagents for RED and GREEN when a subagent tool is available. If not, run the passes inline and label the reduced isolation.

6. Final verification:
   - Run the quick test.
   - Run the relevant full test/lint/build command when one exists.
   - Before any completion claim, include an `EXECUTION_BLOCK` with the actual command, relevant output, exit code, and timestamp.

7. Review gate:
   - Always inspect `git diff`.
   - Run deterministic signals on changed production files: total changed LOC, large-file warnings, and duplication if `jscpd` is installed.
   - `small`: add coverage and metrics review.
   - `full`: add simplicity, coherence, coverage, and metrics review.
   - Use subagents or callable external reviewer tools only when available. In Codex, `-c` is a Claude reviewer request and `-g` is a Gemini/Antigravity reviewer request.
   - For `-c`, run the first executable found at `$HOME/.agents/bin/claude-peer` or `./codex/bin/claude-peer`. Prefer the user-local bridge so an untrusted checkout cannot replace it.
   - Do not interpolate user task text into a shell command. Use the existing `codex/.agents/codex/temp/wf/spec.md` as the task file.
   - Build reviewer context with the first executable found at `$HOME/.agents/bin/codex-review-context` or `./codex/bin/codex-review-context`, then call:
     `<context-builder> | <bridge> --mode review --task-file codex/.agents/codex/temp/wf/spec.md`
   - Reviewer context must include `git diff HEAD` plus untracked text files, excluding `codex/.agents/codex/temp` and `.claude/temp`.
   - The Claude bridge must use official `claude -p` subscription/quota auth only. It must refuse API-key auth and disable Claude tools/edits. If the bridge exits non-zero, continue only with a visible `CLAUDE_REVIEW_UNAVAILABLE` degradation note and include the exit code.
   - For `-g`, discover the agy bridge MCP before the review call. If `tool_search` is available, search for `mcp__agy__agy_ask`, `mcp__agy__agy_continue`, and `mcp__agy__agy_status`; otherwise use whichever callable MCP tools are already exposed in the session.
   - Call `mcp__agy__agy_ask` with the review prompt and a bounded timeout when that argument is supported. The bridge owns model selection and quota handling: it first tries Antigravity `agy`, detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`, and if free Gemini quota is exhausted automatically routes the same prompt to Vertex `gemini-3.5-flash` on project `gemini-keroga-260526-3895`, location `global`, using service account key `~/dev_local/temp/google300/vertex-key.json` unless overridden by bridge environment.
   - Treat a response prefixed `[agy quota exhausted — auto-routed to Vertex gemini-3.5-flash on project gemini-keroga-260526-3895]` as a valid Gemini reviewer response, not as a degradation. Record the route in the review summary.
   - If the agy response is truncated and `mcp__agy__agy_continue` is available, continue the same reviewer conversation rather than starting a new reviewer pass.
   - Do not replace a requested `-g` review with Claude, Codex, or inline self-review because of perceived cost. The Vertex fallback is the intended Gemini fallback. Only degrade when the agy MCP tool is missing, errors, or times out after its own fallback path.
   - If the bridge was recently updated but still behaves like the old agy-only bridge, note that the MCP host must be restarted before the new fallback code is loaded.
   - If a requested reviewer is missing, continue with a visible degradation note unless the user explicitly asked to abort on missing tools.

8. Commit behavior:
   - Do not create commits unless the user passed `--commit` or otherwise explicitly requested commits.
   - With `--commit`, commit only after verification and review gates pass; if using a worktree, merge with `git merge --ff-only`.
   - Without `--commit`, leave the working tree changed and report exact verification evidence.

## Completion Standard

Never claim "done", "fixed", "complete", "tests pass", or equivalent unless the latest relevant `EXECUTION_BLOCK` has exit code 0. If verification cannot be run, say `UNVERIFIED` and explain what remains.
