# Post-mortem: `$in-browser-verify` Hooks Were Installed Globally

Date: 2026-07-13
Status: corrected

## What happened

I installed the skill's `SessionStart` and `Stop` hooks in `~/.codex/hooks.json`. The hook script itself was repository-aware and became a no-op outside onboarded web apps, but Codex discovers and asks users to trust global hooks before running them. As a result, every Codex session—including unrelated non-web work—showed the verification hook.

## Impact

- Non-web sessions displayed an irrelevant hook review prompt.
- The user reasonably perceived the web workflow as globally invasive.
- Script-level conditional behavior did not prevent configuration-level discovery noise.

## Root cause

- I scoped hook execution but failed to scope hook registration.
- I optimized for automatic enforcement across repositories without respecting the explicit onboarding boundary.
- Tests verified that the global installer was idempotent, but did not test the more important product property: non-web sessions must have no web-verification hooks at all.

## Correction

- Keep only the skill discovery link global.
- Remove all `$in-browser-verify` entries from `~/.codex/hooks.json`.
- Have `init` merge hooks into `<web-repo>/.codex/hooks.json` only when that repository is explicitly onboarded.
- Track the project hook file with the web app's scenario and verification configuration.

## Prevention rule

Scope registration at least as narrowly as execution. A global hook with an internal no-op is still globally visible and globally trusted; repository-specific policy belongs in repository-specific hook configuration.
