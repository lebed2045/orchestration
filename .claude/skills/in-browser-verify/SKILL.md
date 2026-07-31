---
name: in-browser-verify
description: Enforce durable, executable verification for web-app features and bug fixes. Use automatically whenever Claude changes user-visible web behavior, UI flows, browser interactions, routes, forms, authentication, client/server integration, or fixes a web regression; also use when the user asks to verify, test end to end, stop claiming done, record scenarios, or avoid explaining expected behavior again. Maintains a persistent scenario contract, maps every scenario to Playwright coverage, runs the complete regression suite, captures fresh browser evidence, and blocks verified completion when proof is missing.
---

# In-Browser Verify

**Updated:** `13-jul-2026`

Turn user expectations into a durable scenario ledger and executable browser proof. Never make the user restate behavior already recorded in the ledger.

This is a standalone workflow. Do not route through or modify `/wf` unless the user separately requests that integration.

## Non-negotiable contract

- Treat `.agent-verification/config.json` and its `scenario_file` as persistent product requirements.
- Update the scenario ledger before implementation whenever behavior changes or a bug exposes a missing scenario.
- Give each scenario a stable ID such as `AUTH-001`; mark its Playwright test with `SCENARIO: AUTH-001`.
- Run the affected scenario RED before fixing code. A bug fix without a regression scenario is incomplete.
- Run the complete configured command suite after implementation, not only the new test.
- Require fresh trace evidence from a real browser run. Exit code alone is insufficient.
- Use a fresh verifier subagent (Agent tool, no shared context) when available. Give it the scenario ledger, changed behavior, running URL, and verification command, but not the builder's reasoning or claims.
- Drive the affected flow in a real browser after deterministic tests (Playwright MCP or an isolated Playwright script — never the user's daily-driver Chrome without authorization) and inspect console/network failures. This is additional evidence, never a substitute for the Playwright suite.
- Report `VERIFIED` only when the runner manifest is successful and live browser verification passed. Otherwise report `UNVERIFIED` with exact missing proof.
- Never silently rewrite scenarios or visual baselines to make a failure green.

## First-time setup in a web-app repository

1. Onboard only the current web repository:

   ```bash
   python3 "$HOME/.claude/skills/in-browser-verify/scripts/in_browser_verify.py" init --root .
   ```

   This creates `.agent-verification/config.json`, `verification/scenarios.md`, and merges two project-local hooks (SessionStart + Stop) into the repo's `.claude/settings.json`. Non-onboarded repositories are unaffected: the hook exits immediately when `.agent-verification/config.json` is absent.

2. Inspect the app's package manager, existing test scripts, Playwright configuration, startup behavior, and test-state strategy.
3. Edit `.agent-verification/config.json` so every command is correct for this repository. Commands must be argument arrays; do not use shell strings.
4. Replace the example scenario in `verification/scenarios.md` with the app's real critical flows. Mine existing tests and documentation before asking the user to repeat requirements.
5. Ensure Playwright produces a trace on successful runs (`trace: "on"` or an equivalent project policy). Keep screenshots/video when affordable.
6. Add `.agent-verification/runs/` and generated Playwright output to the app's `.gitignore`; keep the config, scenario ledger, and `.claude/settings.json` hooks tracked.
7. Run `in_browser_verify.py check` until scenario coverage and configuration pass.
8. Start a new Claude Code session in the web repository and approve the project hooks when prompted (review with `/hooks`).

If Playwright is absent, install and configure it as part of setup. Prefer role/label locators and stable test IDs; never couple acceptance tests to incidental CSS classes.

## Feature or bug-fix workflow

1. Read the full scenario ledger and the latest successful manifest, if present.
2. Identify affected scenario IDs. Add or amend scenarios before touching production code.
3. Add the smallest Playwright regression test and include `SCENARIO: <ID>` in that test file.
4. Run the narrow test and capture a behavior-relevant RED failure.
5. Implement the change.
6. Run the narrow test until green.
7. Run the complete gate:

   ```bash
   python3 "$HOME/.claude/skills/in-browser-verify/scripts/in_browser_verify.py" run --root .
   ```

8. Start or reuse the app, then drive every affected flow in a real browser. Check visible state, console errors, failed requests, loading/error states, and at least one adverse path.
9. If available, delegate a clean verification pass to a fresh subagent (Agent tool). Treat its failure report as a bug, not advice.
10. Read the generated manifest and cite its path in the final response.

## Scenario ledger format

Use level-two headings:

```markdown
## AUTH-001: User signs in with valid credentials

- Given the user account exists
- When the user submits valid credentials
- Then the dashboard is visible
- And no failed authentication request appears in the network log
```

Record corrections permanently. When the user says "it should do X," update or add a scenario immediately so future work re-tests X automatically.

## Runner

Use `scripts/in_browser_verify.py`:

- `init --root <repo>` creates starter config and scenario files without overwriting existing files, and merges the two project hooks.
- `check --root <repo>` validates configuration and scenario-to-test coverage without running commands.
- `run --root <repo>` validates coverage, executes every configured command, requires fresh evidence, and writes an immutable run directory with logs and `manifest.json`.

The runner deliberately does not infer commands. Repository-specific commands belong in the tracked config so future agents execute the same contract.

## Enforcement layers

- The skill is globally discoverable, but installs no global hooks — onboarding writes project-local hooks into the target repo's `.claude/settings.json` only.
- `SessionStart` injects the verification contract only in onboarded repositories.
- `Stop` detects completion claims (parsing the last assistant message from the transcript) and blocks the stop when no successful manifest matches the current workspace fingerprint.
- The hook is a Claude Code guardrail, not a CI boundary. Add the runner command as a required CI check when other humans or tools can merge changes.
- Never install Git hooks automatically; repository policy and CI remain explicit project decisions.

## Completion response

Include:

```text
WEB_VERIFICATION: VERIFIED | UNVERIFIED
Scenarios: <covered>/<required>
Gate: <command> (exit <code>)
Manifest: <path>
Browser check: <flows observed or unavailable reason>
Independent verifier: <result or unavailable reason>
```

Do not claim the web app works merely because unit tests, build, lint, or a reviewer passed.
