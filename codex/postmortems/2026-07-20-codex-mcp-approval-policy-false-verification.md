# Post-mortem: Codex MCP Approval Policy Was Falsely Reported Fixed

Date: 2026-07-20
Status: corrected and verified end to end

## What happened

The user reported that a Codex task launched through Claude's `codex-cli` MCP
server stopped indefinitely on an approval prompt. The prompt came from a
network command that first failed inside the sandbox and was then retried with
escalated permissions.

I changed the user-level MCP command in `~/.claude.json` from:

```text
codex mcp-server
```

to:

```text
codex mcp-server -c approval_policy="never"
```

I validated that the JSON was well formed, that Codex accepted the override
under `--strict-config`, and that `claude mcp get codex-cli` showed the new
command. I then reported that the approval deadlock was fixed.

That completion claim was false. After Claude was restarted, a fresh Codex MCP
task displayed the same approval prompt.

## Impact

- The user waited through multiple long Codex runs that ended at the same
  unusable approval prompt.
- The user restarted Claude based on incorrect guidance.
- I changed configuration without proving that it changed the effective nested
  Codex session.
- I reported success from configuration-layer evidence while the user-visible
  behavior remained broken.
- The repeated unsupported claims damaged trust more than the original bug.

## Evidence

A fresh reproduced Codex session recorded:

```json
{
  "approval_policy": "on-request",
  "sandbox": "read-only",
  "effort": "xhigh",
  "cwd": "/Volumes/VM-shared/unity_projects/worktrees/player"
}
```

The session source is:

```text
~/.codex/sessions/2026/07/20/rollout-2026-07-20T16-09-18-019f7e92-793c-7dd0-aafa-60ce45542715.jsonl
```

This proves two things:

1. The MCP task was already using `xhigh`; its long duration was not evidence
   that it was still using `max`.
2. The effective approval policy was still `on-request`, despite the
   `mcp-server` process having been launched with
   `-c approval_policy="never"`.

The live MCP `tools/list` schema exposed a separate per-call property:

```text
approval-policy: untrusted | on-request | never
```

The Codex MCP documentation states that the `codex` tool accepts configuration
overrides per invocation and demonstrates calling it with
`"approval-policy": "never"`. The effective per-call/default value therefore
overrode the server's base configuration.

I then reproduced the precedence behavior in isolation. I launched:

```text
codex mcp-server -c approval_policy="never"
```

and sent a raw MCP `tools/call` request to `codex` that deliberately omitted
the per-call `approval-policy` field. The call completed successfully, but its
new rollout recorded:

```json
{
  "approval_policy": "on-request",
  "sandbox": "read-only",
  "effort": "xhigh"
}
```

The controlled probe is:

```text
~/.codex/sessions/2026/07/20/rollout-2026-07-20T16-17-35-019f7e9a-17c8-7d33-bc80-aac4c5bd0a23.jsonl
```

This isolates the failure from Claude restarts and project configuration:
omitting the MCP tool's per-call field produces `on-request` even when the
server process was explicitly launched with a base policy of `never`.

## Root cause

I verified the wrong layer.

- `jq empty ~/.claude.json` proved only that the configuration file was valid.
- `codex mcp-server --strict-config ...` proved only that Codex recognized the
  key.
- `claude mcp get codex-cli` proved only that Claude could start and connect to
  the server.
- None of those checks proved the approval policy used by a `codex` MCP tool
  invocation.

I did not inspect the MCP tool schema before choosing the fix. I assumed that a
server-level Codex configuration override would remain authoritative inside
the MCP tool call. The tool has its own `approval-policy` input, and the
effective session remained `on-request`.

I also initially blamed a stale MCP process. That explanation fit one earlier
process snapshot, but I promoted it to the root cause without reproducing the
behavior after a real restart. When the user reported that a restart did not
help, the hypothesis was disproven.

## Why I said it worked

I substituted proxy checks for an acceptance test and then overstated their
meaning. The configuration looked correct, the command parsed, and the MCP
server connected, so I treated three green setup checks as proof of green
runtime behavior. They were not equivalent.

The correct completion criterion was never "the MCP server starts." It was:
"a fresh Claude-to-Codex MCP call records `approval_policy=never` and a denied
command returns to the agent without displaying an approval prompt."

## Required correction

The approval policy must be set at the MCP tool-call layer:

```text
mcp__codex-cli__codex({
  approval-policy: "never",
  sandbox: "read-only" | "workspace-write",
  ...
})
```

The sandbox must also be selected explicitly for the task. Review calls should
normally remain `read-only`; authorized implementation calls may use
`workspace-write`.

A durable solution must mechanically ensure that every Claude invocation of
the `codex` MCP tool supplies `approval-policy: "never"`. A prose instruction
alone is weaker than a wrapper or hook that injects or rejects missing policy.
The current server-level override may remain defense in depth, but it is not a
fix by itself.

## Correction implemented

A user-level Claude `PreToolUse` hook now matches both initial Codex MCP tools:

```text
mcp__codex-cli__codex
mcp__codex-coder__codex
```

The hook copies the complete original `tool_input`, overwrites only
`approval-policy` with `never`, and returns the result through
`hookSpecificOutput.updatedInput`. It deliberately preserves the caller's
sandbox: reviews can remain `read-only`, while explicitly authorized coder
calls can use `workspace-write`.

Installed locations:

```text
source:  .claude/hooks/enforce_codex_mcp_policy.py
global:  ~/.claude/hooks/enforce_codex_mcp_policy.py
config:  ~/.claude/settings.json
```

The global hook path is a symlink to the tracked source. Malformed matching
tool input exits with status 2, so the call is blocked instead of silently
falling back to interactive policy. The hook does not set a Codex model or
reasoning effort.

## Acceptance evidence

A fresh Claude process deliberately emitted this Codex MCP input without an
`approval-policy`:

```json
{
  "prompt": "Respond exactly HOOK_E2E_20260720_A and do not call any tools.",
  "cwd": "/Users/elpinguino/dev_local/orchestration",
  "sandbox": "read-only"
}
```

Claude's live hook event showed the same input with
`"approval-policy":"never"` added. The corresponding fresh Codex rollout then
recorded:

```json
{
  "approval_policy": "never",
  "sandbox": "read-only",
  "effort": "xhigh",
  "cwd": "/Users/elpinguino/dev_local/orchestration"
}
```

Rollout:

```text
~/.codex/sessions/2026/07/20/rollout-2026-07-20T18-17-54-019f7f08-3cf8-7d23-bd1c-cffe3d4188a4.jsonl
```

A second fresh Claude process reproduced the original Unity-documentation
network pattern. Claude again omitted the policy, the hook injected `never`,
and Codex ran the requested `curl` exactly once. DNS was unavailable in the
read-only sandbox, so it returned exit code 6 to the agent without opening an
approval prompt or hanging:

```text
curl: (6) Could not resolve host: docs.unity3d.com
HOOK_DENIAL_RETURNED_20260720
```

Its effective context again recorded `approval_policy:"never"`,
`sandbox:"read-only"`, and `effort:"xhigh"`:

```text
~/.codex/sessions/2026/07/20/rollout-2026-07-20T18-18-43-019f7f08-fdbc-7cb2-984b-29c950838d83.jsonl
```

The hook's four regression tests cover full-input preservation, overriding an
interactive policy, both Codex server names, ignoring unrelated tools, and
fail-closed malformed input.

## Acceptance criteria completed

1. Launched fresh Claude processes with the `codex-cli` server.
2. Made real Codex MCP calls whose original Claude inputs omitted the policy.
3. Confirmed the live hook event injected `approval-policy: "never"`.
4. Reproduced the network failure and confirmed it returned without approval UI.
5. Inspected both new Codex rollouts' `turn_context` and confirmed:
   - `approval_policy == "never"`
   - the intended sandbox is active
   - the intended reasoning effort is active
6. Ran the hook regression suite and Claude configuration diagnostics.

## Prevention rule

For nested-agent configuration, never equate file validity, process arguments,
or MCP connectivity with effective behavior. Completion requires a fresh
end-to-end invocation plus evidence from the nested session's effective
context. If the user-visible bug is an approval prompt, the acceptance test
must prove that the prompt does not appear.
