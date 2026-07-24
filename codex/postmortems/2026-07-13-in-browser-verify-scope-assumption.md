# Post-mortem: I Assumed `$in-browser-verify` Belonged Inside `$wf`

Date: 2026-07-13
Status: corrected before integration

## What happened

The user asked for a durable Codex skill or command that records web-app behavior once and re-tests it for every future feature and bug fix. I correctly started a standalone verification skill, now named `$in-browser-verify`, but then announced that I would integrate it into `$wf` without being asked.

## Impact

- I expanded the requested scope from a reusable verification workflow into a modification of an existing development workflow.
- That assumption risked coupling web verification to `$wf`, even though web verification has a distinct lifecycle: initial app onboarding, persistent scenario maintenance, full browser regression, evidence capture, and independent validation.
- It made the user spend another turn correcting workflow architecture—the exact repetition cost this task is meant to eliminate.
- No `$wf` integration was made before the correction.

## Root cause

- I treated an existing TDD workflow as the obvious host instead of preserving the user's intentionally open request for “some skill/command etc.”
- I optimized for reuse of existing machinery before establishing the new workflow's independent boundary.
- I stated a future implementation decision as settled rather than flagging it as an optional integration point.

## Correction

- Keep `$in-browser-verify` standalone and independently invokable.
- Let the skill trigger for web-app feature and bug-fix work through its own metadata and persistent per-app configuration.
- Do not modify `$wf` unless the user separately requests integration after using the standalone workflow.
- Keep the durable behavior contract in each web app (`verification/scenarios.md` plus `.agent-verification/config.json`) and the generic workflow implementation in the shared `$in-browser-verify` skill.

## Prevention rule

When a user asks for a new reusable workflow, build the smallest independently usable surface first. Treat integration into existing workflows as a separate product decision requiring explicit evidence or user direction; never assume “can integrate” means “should integrate.”
