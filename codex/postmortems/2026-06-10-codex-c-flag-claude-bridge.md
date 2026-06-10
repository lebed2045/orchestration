# Post-mortem: Codex `-c` Did Not Actually Call Claude

Date: 2026-06-10
Status: corrected in repo and synced to global Codex skills

## What happened

I ported the Claude workflow convention into Codex skills and documented `-c` as "request Claude." The actual Codex environment had no Claude MCP or Claude reviewer tool configured. In practice, `-c` could only degrade to an inline second Codex pass, which is not the same thing as a Claude review.

## Impact

- Any prior Codex `$wf -c` or `$research -c` run did not get an independent Claude model pass unless a separate Claude tool happened to exist.
- The wording created a false expectation that `-c` was operational.
- Research output was also saved under hidden, gitignored tool scratch instead of a canonical repo folder.

## Root cause

- I copied the semantic flag contract before proving the operational bridge existed.
- The skill text allowed graceful degradation, but did not require a concrete preflight command or an explicit "Claude unavailable" result.
- I did not check `~/.codex/config.toml` before discussing `-c` as if it could work.

## Correction

- Added `codex/bin/claude-peer`, a local read-only bridge around the official `claude -p` non-interactive CLI.
- The bridge refuses API-key auth and requires `claude auth status` to report `authMethod=claude.ai`.
- The bridge unsets common Anthropic API/provider environment variables for the child Claude process.
- The bridge also unsets common Bedrock/Vertex ambient provider variables for the child Claude process.
- The bridge disables Claude tools with `--tools ""`, uses `--safe-mode`, and does not allow edits.
- Added `codex/bin/codex-review-context` so reviewer input includes `git diff HEAD` and untracked text files.
- The context builder omits untracked symlinks and binary/non-text files.
- Updated Codex skill instructions so `-c` names this exact bridge and must report a visible degradation if it is unavailable.
- Updated skill instructions to prefer the user-local bridge and pass task text through files, not shell interpolation.
- Codex research notes now belong under `codex/.agents/codex/research/`; Claude research remains under `.claude/research/`.

## Prevention rule

Any workflow flag that claims to call another model must name the exact local command or MCP tool, include a preflight check, and report the result in the run output. If the bridge is missing, say it is missing; do not imply independence.
