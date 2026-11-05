# Reflection option 1 — implementation plan

Approved design: the user's “Do option 1” adopts the preceding four-step proposal. Implement inline with executing-plans and TDD in this shared checkout on master; no commits, branch changes, cleanup of existing artifacts, new skill installation or live global rule update.

Goal: during authorized work, confirmed project lessons update project instructions immediately. Global incidents produce proposals only. Explicit review gathers all shared host/VM Codex/Claude logs; explicit apply changes only the reviewed global diff.

Constraint: “keep all code, data and intermediates inside the user-designated shared root.” Host access is established at /Users/elpinguino/VM-shared; current guest access/loaded sessions remain unconfirmed. Reuse the existing discoverable reflect skill and Python standard library; add review/apply CLI modes rather than installing new skills.

Interfaces:
- Recorder persists expected/actual/evidence/correction and an optional one-line proposed_global_rule/replaces_global_rule in incidents.jsonl, preserving historical rows and four ledger views.
- Review consumes all immediate global/log/*/reflections/incidents.jsonl sources, reports four-role coverage and legacy/missing proposals, groups causal patterns, deduplicates identical proposals and emits an exact append/replacement diff against the global file's hash. Conflicting alternatives require explicit source selection. Default prints only; --output writes a caller-named new JSON file under the shared checkout.
- Apply consumes that review JSON with --confirm, verifies target/base/diff/line budget/source fingerprints, preserves a durable before.md and receipt under global/reflection-reviews/<run>/, and atomically applies the approved edit. No network, model calls, scheduling or automatic promotion.
- Project recording resolves the actual target, refuses shared-global aliases/hardlinks and escaping symlinks; a local CLAUDE.md importing @AGENTS.md updates the in-project shared file. Repeated patterns remain evidence; newly generated rules never impose L3/L4 halts.

Tasks:
1. RED→GREEN: project path guards, portable project target selection, richer incident records, recurrence without automatic hard gates.
2. RED→GREEN: read-only four-role review, grouped conflicts/legacy handling, no-clobber named output, confirmed/stale-safe apply and rollback, no extra intermediates with home/cache/temp redirected.
3. Update shared reflect core, thin adapters' dates, README/project pointers/setup guidance and a human guide with actual invocation examples, output sizes/locations/lifetimes and known limitations. Preserve global/AGENTS.md bytes.
4. Exercise real record→review→apply CLI paths with isolated shared-root fixtures; run repository Python and reflection suites plus applicable shell checks; obtain one fresh read-only final review and fix material findings with regressions.

Review focus: malicious/corrupt review plans; local aliases to global rules; missing/dangling/shared log sources; concurrent changes/stale approvals; output-path symlinks and rollback after I/O failure. Legacy records never get invented proposals or rewritten history. Applying a reviewed local policy does not prove fresh model-session behavior.

Progress: codex/temp/reflection-review-20261027/ledger.md. Tests use per-run shared-root temp directories; new software intermediates are removed by the software on success/failure. Explicit review artifacts/backups are durable user-requested outputs, not disposable intermediates.
