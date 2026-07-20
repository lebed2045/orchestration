---
name: cc
description: Claude-led coding workflow that delegates planning, test writing, implementation, fix iterations, and code-quality cops to Codex MCP; Claude orchestrates and is the independent reviewer at both gates — the plan (Gate 1) and the code (Gate 2). Use only when the user invokes /cc for an implementation, refactor, or bug-fix task.
---

# CC

**Updated:** `20-jul-2026`

Treat the text after `/cc` as the task. Claude is the main orchestrator: inspect the repository, define the acceptance contract, control both gates as the independent reviewer, and report the evidence. Codex performs the authoring work — the plan, the tests, the implementation, the fixes, and the cops.

This is a standalone workflow. Do not invoke `/wf`, translate the request into `/wf` flags, or modify `/wf`.

## Non-negotiable routing

- Use Codex to author the plan, the failing tests, the implementation, and every fix iteration.
- Use Codex for the code-quality cop roles — Codex's checks on its own code.
- Claude is the independent reviewer at BOTH gates, because Codex authored both artifacts: Claude reviews Codex's plan at Gate 1, and a fresh review-only Claude agent reviews Codex's code at Gate 2.
- Never let Claude author the plan or the code, and never let Codex be the final gate on its own work. If Codex coding is unavailable or fails, follow the failure contract below — do not fall back to a Claude coder.
- Run Codex coding through `mcp__codex-coder__codex` with `sandbox: "workspace-write"` and `approval-policy: "never"`. The dedicated MCP server supplies the longer 30-minute call timeout.
- Run Codex plan/cops through `mcp__codex-cli__codex` with `sandbox: "read-only"` and `approval-policy: "never"`.
- Omit model and effort overrides unless the user explicitly requests them; inherit the user's Codex configuration.
- Do not commit, merge, push, reset, clean, or stash unless the user explicitly authorizes that action.

## 1. Preflight and baseline

1. Read the applicable repository instructions, implementation, existing tests, and the final output stage of any affected pipeline.
2. Record the repository root, baseline commit, current branch, and complete dirty-path list. Preserve pre-existing changes.
3. Discover the narrow test command and the proportionate full verification command from the live repository.
4. Load both Codex MCP namespaces:

   ```text
   ToolSearch({query: "select:mcp__codex-cli__codex,mcp__codex-cli__codex-reply", max_results: 2})
   ToolSearch({query: "select:mcp__codex-coder__codex,mcp__codex-coder__codex-reply", max_results: 2})
   ```

   Hard-stop if either initial-call tool is unavailable. Do not downgrade to Claude.

5. Choose the working location before coding:

   - Use the current worktree when the task depends on its uncommitted state or isolation would make delivery unsafe.
   - Prefer a new isolated git worktree for risky or broad work that starts from committed state. Record its exact path and a uniquely generated `cc/<run-id>` branch before passing that path as Codex's `cwd`.
   - Never pretend the current worktree is disposable.

## 2. Codex plan and Gate 1 (Claude review)

Claude gives Codex the task, the acceptance contract, and the repository facts, and asks Codex to author a concise plan with:

- acceptance criteria;
- affected components and ownership boundaries;
- the RED test and expected failure;
- implementation sequence;
- narrow and full verification commands;
- relevant regression risks.

```text
mcp__codex-cli__codex({
  prompt: <task, acceptance contract, and repository facts; author the plan above and return it>,
  cwd: <working repository>,
  sandbox: "read-only",
  approval-policy: "never"
})
```

Gate 1 is Claude's own independent review of Codex's plan. Claude did not author the plan, so this is a genuine cross-model gate: Claude checks the plan against the task and the acceptance contract and either approves it or returns concrete blockers, ending with `VERDICT: APPROVED` or `VERDICT: NEEDS_WORK <reason>`. Claude sends valid findings back to Codex on the same plan thread (`mcp__codex-cli__codex-reply`) to revise, at most three passes. A missing, malformed, or still-rejecting plan after three passes is a hard stop before any code changes.

## 3. Codex RED and GREEN

Use separate Codex coding calls so the implementation agent receives the failing test from the filesystem, not the test author's hidden reasoning.

RED call:

```text
mcp__codex-coder__codex({
  prompt: <write the narrowest useful regression test, run it, prove it fails for the expected
           missing behavior, do not implement the fix, and return files plus command/output/exit>,
  cwd: <working repository or isolated worktree>,
  sandbox: "workspace-write",
  approval-policy: "never"
})
```

Claude verifies that the test exists and that the captured RED is behavior-relevant. A test that fails for setup, compilation, or an unrelated reason is not RED.

GREEN call:

```text
mcp__codex-coder__codex({
  prompt: <read the accepted plan and RED test from disk; implement the smallest source-of-truth
           fix; run the narrow test and relevant full checks; return exact evidence and changed files>,
  cwd: <same working repository>,
  sandbox: "workspace-write",
  approval-policy: "never"
})
```

When a successful Codex call returns actionable test failures, use `mcp__codex-coder__codex-reply` on that coding thread for fixes. Limit each test/fix loop to three iterations. Claude checks the files and reruns the claimed commands rather than trusting prose.

If a deterministic automated test is genuinely impractical, Codex must add or run the cheapest durable check and Claude must report the missing coverage explicitly.

## 4. Codex cops

After GREEN and the full relevant suite pass, run applicable cops as independent, read-only Codex calls over the task, accepted plan, and complete diff from the recorded baseline. Run them in parallel when the tool surface permits:

- simplicity: reject unnecessary abstraction and complexity;
- coherence: reject broken boundaries, duplication, and inconsistent ownership;
- coverage: reject missing behavior or regression coverage;
- metrics: reject suppressions, dependency cycles, egregious batch size, and unjustified structural growth.

Each cop must end with `<ROLE>: PASS` or `<ROLE>: REJECT <reason>`. Missing or malformed cop output makes the gate incomplete; do not silently skip it.

Consolidate valid findings and send them to the Codex coding thread for fixes. Rerun affected tests, the full relevant suite, and all rejecting cops. Stop after three cop/fix passes.

## 5. Gate 2: fresh Claude code review

Codex must not be the final reviewer of its own implementation. Spawn a new general-purpose Claude agent with no builder transcript and a review-only prompt. Give it only:

- the original task and acceptance criteria;
- the accepted plan;
- the baseline and complete diff;
- changed test files;
- exact RED, GREEN, and full-suite commands/results.

Tell the agent not to edit files and to end with `VERDICT: APPROVED` or `VERDICT: NEEDS_WORK <reason>`.

If Gate 2 returns `NEEDS_WORK`, send the concrete findings to Codex for the fix, rerun verification and relevant cops, then spawn a different fresh Claude reviewer. Stop after three Gate 2 passes. A failed or unavailable Claude reviewer is a hard stop, not approval.

## 6. Failure contract

A Codex coding timeout, transport error, malformed result, or lost coding thread is an implementation failure:

- Never retry it through a Claude coder and never continue as if the phase passed.
- In the current/user worktree, hard-stop with all state preserved. Print the exact dirty paths, partial commits if any, failed phase, and last error. Never reset or clean.
- In an isolated worktree created by this run, discard only when its path and `cc/<run-id>` branch were recorded before coding and it contained no user state at baseline. Capture the failure summary, run `git worktree remove --force <exact-path>`, delete only that generated branch, report what was discarded, and stop.
- If safe isolation cannot be proven, preserve the worktree and hard-stop.

Test failures returned by a healthy coding call use the bounded Codex fix loop. Exhausting a test, cop, or Gate 2 loop hard-stops with state preserved; it never changes the coder backend.

## 7. Completion

Before claiming completion, Claude:

1. inspects the final diff and confirms `/wf` was neither invoked nor modified by this workflow;
2. reruns the narrow test and proportionate full checks;
3. confirms Gate 1 (Claude's review of Codex's plan) approved, every required cop passed, and the latest fresh Claude Gate 2 approved;
4. reports the working path, changed files, exact commands and outcomes, gate verdicts, and any unverified boundary.

Do not merge an isolated worktree or create a commit unless the user explicitly requested it.
