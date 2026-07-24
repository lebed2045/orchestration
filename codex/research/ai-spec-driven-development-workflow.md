# Research: A less cumbersome AI spec-driven development workflow

Generated: 2026-07-24 13:39 WITA
Mode: Full adversarial run — Codex lead, two independent Codex research subagents, Claude, and Gemini/Antigravity
Degradation: Claude's external pass had no web access, so its claims were treated as opinion and independently checked. Antigravity quota was unavailable; the approved router successfully used `google300 Vertex/gemini-3.5-flash`, which is a valid Gemini route rather than a substitute reviewer.

## Question and Scope

The current process is:

1. Write `PRODUCT.md` with the product idea and versioned MVP stages.
2. Ask a high-reasoning model to append clarification questions.
3. Answer those questions in detail.
4. Ask a high-reasoning model for a concise implementation plan.
5. Ask a lower-effort model to convert each version into a coding and verification artifact.
6. Give that artifact to a lower-tier implementation subagent.

The process is intended to manage three different uncertainties:

- **Product uncertainty:** the desired result is partly experimental.
- **Codebase uncertainty:** the current system is large and only partially understood.
- **Verification uncertainty:** coding agents often stop at a plausible implementation without proving all promised behavior.

This research asks which parts are sound, which are ceremony, and what operating model strong teams can defend with current primary evidence. It does not claim a universal process for regulated, safety-critical, or multi-organization development.

## Assumptions

- The developer is willing to keep durable repository documents but wants less manual document synchronization.
- Most work can be sliced into independently testable increments lasting hours to a few days.
- Existing repository-native tests and runtime checks should be reused rather than replaced by a universal tool stack.
- A model's agreement is not evidence. External reviewer claims were used only after the lead opened the underlying primary source.
- "Best practice" here means a defensible pattern with strong operational or empirical support, not a settled scientific optimum. No source found a universal winning artifact count or model-routing policy.

## Executive Summary

The workflow is **not a reinvention of the bicycle**. It closely resembles GitHub Spec Kit's current `specify → clarify → plan → tasks → implement` process. The cumbersome part is that the workflow manually treats every derived artifact as durable and repeats the same intent through several lossy translations.

The strongest evidence supports **adaptive ceremony**:

- Keep `PRODUCT.md` as the slow-changing product strategy and hypothesis ledger.
- Work on one small vertical slice at a time.
- Keep one living per-slice contract containing the outcome, boundaries, concrete examples, unresolved questions, verified codebase facts, risky assumptions, and requirement-to-evidence mapping.
- Generate or embed the technical plan only when the change is genuinely cross-cutting, unfamiliar, or expensive to reverse. Treat task lists as disposable execution aids.
- Delete the separate "coding artifact" when it merely rewrites the plan.
- Allocate model capability by uncertainty and blast radius, not by phase name. A cheaper implementer is appropriate only when the task is bounded, the affected contracts are known, and feedback is fast.
- Make executable evidence—not another review document—the completion contract.

The practical default is:

> **Chat for discovery; documents for durable decisions; executable checks for truth; small deployed slices for learning.**

For exploratory product work, a complete plan is often premature. First write a time-boxed hypothesis or run a spike. Tests can prove that the implementation matches a stated behavior; they cannot prove that the behavior is the right product. DORA's current guidance emphasizes small, independently valuable and testable batches because they shorten feedback and counter AI-driven instability. Cucumber's current BDD guidance similarly uses small examples in a repeated discovery → formulation → automation loop.

The testing problem is primarily an **oracle, sensitivity, and boundary** problem—not a "make the AI think harder" problem:

1. Every accepted behavior needs a stable ID and an observable oracle.
2. Every ID must map to an executable check and fresh evidence.
3. A new check must demonstrate that it can fail for the relevant wrong behavior.
4. Targeted checks guide the edit loop; a broader declared regression gate runs before completion.
5. The real boundary must be observed: visible browser behavior, interface contract, persisted side effect, queue message, or other user-relevant outcome.
6. A fresh verifier tries a named falsification without seeing the builder's rationale and without editing the implementation.

Do not use "all reviewers are unable to disagree" as the pass condition. It is impossible to falsify and rewards endless objections. The stronger rule is:

> **Pass within the declared scope only when every reviewer reports zero evidence-backed blocking findings after named falsification attempts. One reproducible blocker overrides any number of approvals.**

## Codebase Patterns

The local orchestration repository already contains most of the right mechanisms:

- `$wf` scales work into micro, small, and full tiers rather than applying one ceremony level to everything (`codex/.agents/skills/wf/SKILL.md:32-40`).
- It uses temporary spec and architecture notes, a conditional human plan gate, behavior-relevant RED, a bounded GREEN loop, targeted tests, a relevant full gate, and exact execution evidence (`codex/.agents/skills/wf/SKILL.md:51-74`).
- It stops after repeated failure and labels unverifiable work rather than claiming success (`codex/.agents/skills/wf/SKILL.md:66-74`, `codex/.agents/skills/wf/SKILL.md:105-107`).
- The separate browser workflow keeps persistent scenario IDs, maps them to tests, requires RED, the complete configured suite, fresh trace evidence, an adverse path, and a fresh verifier (`codex/.agents/skills/in-browser-verify/SKILL.md:14-23`, `codex/.agents/skills/in-browser-verify/SKILL.md:49-65`).
- Its runner validates scenario-to-test coverage and writes immutable evidence; project-local hooks block unsupported completion claims, while CI remains the real cross-actor gate (`codex/.agents/skills/in-browser-verify/SKILL.md:82-98`).
- The repository's portable discipline already says live state outranks documentation, baselines must be compared with deltas, and a diagnostic should replace repeated theory (`CLAUDE.md:133-149`).

The gap is not another plan document. It is a **general, non-browser-specific requirement-to-evidence contract** and an explicit rule for deciding when a plan deserves to be durable.

The earlier BeatLab workflow research reached the same local conclusion: `PRODUCT.md` is the intent source, derived specs may stale, approval should precede implementation, and a green generated gate is insufficient when spec freshness is not proved. That is historical evidence from this workspace rather than a universal external result.

## External Evidence and Reference Implementations

### 1. The current workflow is legitimate, but its full ceremony is optional

[GitHub Spec Kit's current Agentic SDD reference](https://github.github.com/spec-kit/reference/agentic-sdd.html), accessed 2026-07-24, implements nearly the same sequence: specify, clarify, plan, checklist, tasks, analyze, implement, and converge. Crucially, its own documentation says only `specify` is strictly required before planning; clarify, checklist, and analyze are gates for work with meaningful ambiguity. It also recommends staged implementation and verification for large features.

[Spec Kit's persistence models](https://github.github.com/spec-kit/concepts/spec-persistence.html), accessed 2026-07-24, explicitly distinguish:

- flow-back artifacts that are reconciled after implementation discoveries;
- immutable flow-forward historical artifacts; and
- a living spec where plan and tasks are disposable derivations.

This directly adjudicates the artifact question: the user should choose one source-of-truth model instead of maintaining `PRODUCT.md`, plan, coding artifact, and tests as co-equal truth. For this exploratory solo workflow, a living product/slice contract with disposable plan/tasks is the best default. A separate ADR preserves only long-lived technical rationale.

### 2. Exploration and planning are valuable, but should be conditional

[Anthropic's current Claude Code best practices](https://code.claude.com/docs/en/best-practices), accessed 2026-07-24, recommend:

- executable verification rather than a "looks done" judgment;
- explore → plan → implement for unfamiliar or multi-file work;
- skipping a plan when the diff is obvious and small;
- concise persistent instructions instead of file-by-file codebase descriptions;
- bounded subagents for investigation;
- fresh-context adversarial review against a plan; and
- pruning over-specified instructions because context noise causes important rules to be ignored.

This is first-party operational guidance, not a randomized workflow comparison. It nonetheless matches the local repository's tiering and supports just-in-time reconnaissance over a comprehensive "how the whole system works" document.

### 3. Product uncertainty requires smaller experiments, not more complete prose

[DORA's 2025 AI-assisted development report](https://dora.dev/research/2025/dora-report/) says AI amplifies an organization's existing strengths and weaknesses rather than replacing the surrounding engineering system. [DORA's small-batch capability](https://dora.dev/capabilities/working-in-small-batches/), current 2025 guidance, says small batches shorten feedback, reduce sunk-cost risk, and act as a countermeasure to AI-driven delivery instability. It recommends independently valuable, negotiable, small, and testable batches.

[Cucumber's BDD guidance](https://cucumber.io/docs/bdd/), updated 2026-07-22, uses rapid small iterations and a discovery → formulation → automation loop. Its [Example Mapping guidance](https://cucumber.io/docs/bdd/example-mapping/), updated 2026-07-22, captures rules, concrete examples, unanswered questions, assumptions, and deferred stories until the slice is clear or the timebox expires.

These sources reject both extremes:

- exhaustive upfront specification for an experiment; and
- chat-only improvisation with no durable examples or boundaries.

### 4. Passing tests are necessary, but a green suite can still be weak or incomplete

[IEEE 1012-2024](https://standards.ieee.org/ieee/1012/7324/), published 2025-08-22, defines verification and validation as including analysis, evaluation, review, inspection, assessment, and testing. [NASA's IV&V overview](https://www.nasa.gov/ivv-overview/), updated 2024-07-23, separates "building the product right" from "building the right product" and lets an independent verifier choose its own scope and techniques. A solo AI workflow can approximate technical independence with a fresh context, but it is not organizational IV&V.

[NASA's current bidirectional-traceability guidance](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052%2B-%2BBidirectional%2BTraceability), accessed 2026-07-24, maps requirements forward to implementation and tests and tests back to justified requirements. This is heavier than many ordinary applications need, but a tiny per-slice matrix provides the high-value part: it exposes accepted behavior with no test and tests that prove no accepted behavior.

[Playwright's current best practices](https://playwright.dev/docs/best-practices), accessed 2026-07-24, recommend user-visible behavior, isolated tests, resilient user-facing locators, web-first assertions, traces for CI diagnosis, and frequent CI execution. A trace is evidence of what ran; it is not proof that an omitted assertion or omitted product behavior is correct.

[Pact's contract-versus-functional-test guidance](https://docs.pact.io/consumer/contract_tests_not_functional_tests), updated 2022-03-02, makes another important boundary explicit: matching a request/response contract does not prove that the provider performed the required side effect. If the promise is persistence, billing, delivery, or queue publication, the oracle must observe that final state.

### 5. Test sensitivity should be sampled, not replaced by coverage numbers

[Google's 2021 industrial mutation-testing work](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/) calls mutation one of the strongest adequacy criteria but makes it scalable by mutating only changed code, filtering mutants, and limiting review volume. [Google's 2018 industrial case study](https://research.google/pubs/an-industrial-application-of-mutation-testing-lessons-challenges-and-research-directions/) says complete mutation adequacy is neither practical nor desirable.

The right inference is not "mutation-test every change exhaustively." It is:

- require a behavior-relevant RED when feasible;
- sample a deliberate fault or changed-code mutation for risky or AI-generated tests;
- investigate a surviving important mutant; and
- never mistake a mutation score for product completeness.

Two recent preprints strengthen the caution without settling the question. [Chen et al.](https://arxiv.org/abs/2602.07900), revised 2026-04-09, found that increasing or reducing agent-written test volume did not significantly change SWE-bench Verified outcomes in their setting; many tests acted as observational feedback rather than assertions. [SWE-Mutation](https://arxiv.org/abs/2605.22175), submitted 2026-05-21, reports that current LLM-generated suites often lack discriminative power against realistic mutated solutions. These are preprints and benchmark-specific, so they support skepticism about "more AI-written tests" rather than a universal ban.

### 6. Fast selected tests and the final gate serve different purposes

[Google's ICSE 2019 test-selection study](https://research.google/pubs/assessing-transition-based-test-selection-algorithms-at-google/) found that regression-test selection remained largely open and that simple history-based algorithms underperformed expectations. The defensible loop is therefore:

- fast affected checks during implementation;
- the repository's declared relevant regression gate before completion; and
- an explicit limitation when the full environment cannot run.

## Pitfalls and Trade-offs

### Over-documentation

- Repeatedly translating the same intent creates drift and context bloat.
- A polished architecture explanation can freeze an unverified codebase assumption.
- A question list can become theater if every unknown is forced into prose instead of an experiment.
- A durable task list becomes stale as soon as implementation reveals new facts.

Mitigation: one source of truth, generated derivations, evidence timestamps/SHA, and an artifact budget based on risk.

### Under-documentation

- Chat-only decisions disappear across sessions.
- Without pre-implementation examples, implementer-authored tests can encode whatever was built.
- A fresh reviewer cannot distinguish a product pivot from implementation drift.

Mitigation: a small living slice contract with observable examples, non-goals, and change history.

### Testing theater

- A scenario ID can point to a test that only checks page load or a success message.
- Unit mocks can agree with each other while the real integration fails.
- Contract tests can pass while the intended side effect never happens.
- Coverage can be high while fault sensitivity is low.
- A reviewer can approve prose without running a falsification attempt.

Mitigation: record the oracle and boundary, prove sensitivity, run an adverse path, and preserve fresh evidence tied to the current revision.

### Independent-review theater

- Three models with the same prompt often produce correlated opinions.
- A reviewer ordered to find a problem can always invent style objections.
- A reviewer who sees the builder's reasoning inherits its framing.

Mitigation: distinct falsification roles, fresh contexts, severity and reproduction requirements, and evidence adjudication rather than voting.

### Model-tier mistakes

- A lower-cost model may be excellent for a mechanical bounded patch.
- The implementation phase may also contain the hardest repository localization and integration reasoning.
- No primary source established a universal "high model plans, low model codes" rule.

Mitigation: route by task uncertainty, coupling, reversibility, and test latency; benchmark cost and escaped defects locally.

## Disagreements and Adjudication

| Question | Position A | Position B | Adjudicating evidence | Verdict |
|---|---|---|---|---|
| Keep the full spec → plan → tasks chain? | GitHub Spec Kit shows a comprehensive chain can be useful. | Claude and both Codex subagents argued that repeated translation creates drift. | Spec Kit itself says only `specify` is mandatory before planning and provides a living-spec model with disposable derivations. | Keep the capability, invoke stages conditionally. Do not make every artifact durable. |
| Separate durable `PLAN.md` for every slice? | Claude's pass recommended two durable Markdown artifacts. | Gemini and the SDD subagent preferred a compressed contract and disposable plan. | Anthropic says planning adds overhead and should be skipped for obvious small diffs; Spec Kit permits derived plan/tasks. | Embed the plan in the slice contract by default; split it only for cross-cutting or expensive-to-reverse work. |
| Always use a lower-tier implementation agent? | It may reduce cost after expensive planning. | Large unfamiliar codebases may put the hardest reasoning in implementation. | No verified source supports phase-based downshifting; current guidance emphasizes task/context fit. | Use cheaper models only for bounded mechanical work with fast deterministic feedback. |
| Must a separate agent write every test? | Fresh author/checker separation reduces shared framing. | A separate agent can write equally weak tests; the 2026 preprint finds test volume alone has marginal value. | Anthropic recommends fresh verification; mutation and RED test sensitivity provide deterministic checks. | Prefer separate acceptance author/verifier for risky work, but make sensitivity and boundary evidence the gate. |
| Should mutation testing be mandatory? | It exposes weak assertions. | Exhaustive mutation is expensive and can distract from omitted behavior. | Google's 2018 and 2021 industrial work supports filtered changed-code mutation and rejects complete adequacy as a goal. | Use targeted changed-code mutation or deliberate fault injection for risky tests, not a universal score. |
| Should three reviewers pass only when none can disagree? | Strong contrarian pressure reduces rubber-stamping. | A model can always object; unanimity is not falsifiable and causes overengineering. | Anthropic's current guidance warns that gap-seeking reviewers over-report and recommends correctness/scope findings only. | Each reviewer returns `PASS_WITHIN_SCOPE` or `BLOCKED`; zero unresolved evidence-backed blockers is the gate. |
| Can tests determine that the product is right? | Executable specs tie code to stated intent. | Experimental product value is unknown until user/operational feedback. | IEEE/NASA distinguish verification from validation; DORA emphasizes rapid feedback in small batches. | Tests prove conformance to the slice contract; product validation requires an experiment or real use. |

No recommendation-critical disagreement remained unresolved. The reviewer models differed on artifact count and test-author separation, but the primary sources support a conditional rather than universal rule.

## Uncertainty and Unresolved Questions

1. **Model economics are local.** Measure lead time, human interventions, token/cost, escaped defects, regressions, and document-reconciliation time. Do not permanently route models from benchmark anecdotes.
2. **"Relevant full suite" is repository-specific.** A monorepo needs ownership/dependency rules; some repositories can run everything cheaply.
3. **Mutation tooling is stack-specific.** There is no defensible universal threshold or per-change budget.
4. **Real services versus deterministic substitutes is risk-specific.** Payments, migrations, identity, and irreversible side effects need stronger boundary checks than a prototype.
5. **Regulated or safety-critical work may require immutable plans and formal traceability.** The compact model is a default for exploratory product development, not an exemption from external obligations.
6. **Product hypotheses need actual feedback.** If a 0.x milestone has no user, metric, or observable learning goal, neither a model nor a test suite can decide whether it succeeded.

## Recommended Approach

### A. Replace the document cascade with an artifact budget

| Work type | Durable artifacts | Technical plan | Required verification |
|---|---|---|---|
| Exploration / unknown desired result | `PRODUCT.md` + one experiment brief | No production plan; time-boxed spike only | Prototype observation, telemetry, or user feedback; label production claims `UNVERIFIED` |
| Small, obvious change | Existing product/slice contract or issue | No separate plan | Behavior-relevant check + relevant regression gate |
| Normal feature slice | `PRODUCT.md` + `specs/<id>-<name>.md` | Short section inside slice spec | Stable IDs, RED/sensitivity proof, targeted + full gate, real-boundary evidence |
| Cross-cutting/high-risk change | Product + slice spec + separate technical plan | Yes; include migration, rollback, and failure modes | Independent technical review, stronger integration/runtime evidence, targeted mutation/fault injection |
| Long-lived architecture decision | Above + ADR | ADR stores the durable rationale | Architecture-specific checks and review |

### B. Use one living per-slice contract

Suggested shape:

```markdown
# S-014: <one vertical outcome>

## Hypothesis and appetite
- We believe ...
- We will spend at most ...
- We will learn success/failure from ...

## In scope / out of scope

## Acceptance examples
- S-014-A1: Given ... When ... Then ...
- S-014-A2 adverse: Given ... When ... Then ...

## Questions and assumptions
| Item | Type: blocker / reversible assumption / experiment | Resolution |

## Codebase reconnaissance
| Claim | Verified fact / assumption / unknown | File:test:runtime evidence | SHA/date |

## Technical delta
- Components/interfaces changed
- Migration/rollback
- Stop conditions

## Verification map
| Acceptance ID | Observable oracle | Automated check | Real-boundary evidence | Status |
```

Do not retain a Q&A transcript. Encode decisions into the owning section and keep only unresolved questions with their impact. Do not generate a separate coding artifact unless it adds a genuinely different contract such as an API schema or migration runbook.

### C. Run a seven-step operating loop

1. **Choose one bet.** Turn a `PRODUCT.md` 0.x milestone into one hours-to-days vertical slice with an appetite and learning goal.
2. **Reconnoiter read-only.** Ask a capable model or bounded subagents to answer exact codebase questions. Separate verified facts from assumptions and unknowns; cite file/test/runtime evidence and the current SHA. After repeated reading without progress, run a small diagnostic instead of writing more theory.
3. **Approve the contract.** The human approves outcome, scope, non-goals, examples, and any irreversible decisions. Only behavior-changing unanswered questions block; reversible assumptions may proceed visibly; empirical questions become spikes.
4. **Prove the oracle.** Add or identify the smallest check. Capture a relevant RED, reproduction, deliberate fault, or changed-code mutation. If no meaningful oracle exists, the slice is not implementation-ready.
5. **Implement in a bounded loop.** Choose model capability by uncertainty and coupling. Run fast affected checks after each change. Stop after five iterations or after the same failure repeats twice without new diagnostic evidence.
6. **Verify at completion.** Run the affected check, the declared relevant regression gate, and the real acceptance boundary. A fresh verifier receives the slice contract, diff, current state, and commands—but not the builder's rationale—and attempts at least one adverse path or falsification.
7. **Close the learning loop.** Record a receipt tied to the revision/workspace. Expose the slice to real use, update `PRODUCT.md`, archive the slice contract, and discard generated plan/tasks unless they contain lasting rationale.

### D. Allocate model effort by risk, not phase

Use the strongest available reasoning for:

- product framing when the outcome is contested;
- broad or unfamiliar codebase reconnaissance;
- architecture, migrations, concurrency, security, and hard-to-reverse integration;
- adversarial review of high-blast-radius work.

Use a lower-cost model for:

- repetitive transformations with exact boundaries;
- implementation where APIs are already verified and tests are fast;
- task-list generation and mechanical documentation;
- rerunning deterministic checks and formatting evidence.

Escalate the implementer when it must discover architecture while coding. Downshift only after uncertainty has actually been removed, not merely because a plan document says it has.

### E. Give adversarial reviewers different jobs

For ordinary slices, deterministic gates plus one fresh verifier are usually enough. For consequential work, run three independent roles:

1. **Product skeptic:** find ambiguous, contradictory, unobservable, or premature outcomes.
2. **Technical skeptic:** disprove codebase and architectural assumptions from live evidence.
3. **Verification attacker:** find accepted behavior with no sensitive oracle, and tests that remain green under a relevant fault.

Rotate which model receives each role across runs. Do not show one reviewer another's conclusion during the first pass. Require every finding to include severity, scope, evidence/reproduction, and the exact acceptance ID affected.

Pass rule:

```text
PASS_WITHIN_SCOPE
- declared scope attacked
- falsification attempts run
- zero unresolved critical/high findings
- limitations listed
```

Any reproducible blocking failure yields `BLOCKED`, regardless of reviewer votes.

### F. Track whether the simplification works

For the next 5–10 slices, measure:

- idea-to-first-running-slice time;
- time spent reconciling documents;
- number of human clarification rounds;
- repeated agent failures;
- acceptance IDs without executable evidence;
- escaped defects and regressions;
- false-positive reviewer findings;
- model cost per accepted slice;
- product hypotheses validated or invalidated.

If defects rise, strengthen the relevant gate. If document reconciliation stays high without reducing defects, remove another derived artifact. This turns workflow design itself into an experiment.

## Sources

### Local codebase files

- `codex/.agents/skills/wf/SKILL.md:32-107`
- `codex/.agents/skills/in-browser-verify/SKILL.md:12-113`
- `CLAUDE.md:129-153`
- `README.md:142-148`

### Primary web sources

1. GitHub, [Agentic SDD](https://github.github.com/spec-kit/reference/agentic-sdd.html), current documentation accessed 2026-07-24.
2. GitHub, [Spec Persistence Models](https://github.github.com/spec-kit/concepts/spec-persistence.html), current documentation accessed 2026-07-24.
3. Anthropic, [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices), current documentation accessed 2026-07-24.
4. DORA, [State of AI-assisted Software Development 2025](https://dora.dev/research/2025/dora-report/), 2025.
5. DORA, [Working in small batches](https://dora.dev/capabilities/working-in-small-batches/), current 2025 capability guidance.
6. Cucumber, [Behaviour-Driven Development](https://cucumber.io/docs/bdd/), updated 2026-07-22.
7. Cucumber, [Example Mapping](https://cucumber.io/docs/bdd/example-mapping/), updated 2026-07-22.
8. Microsoft Playwright, [Best Practices](https://playwright.dev/docs/best-practices), current documentation accessed 2026-07-24.
9. IEEE, [IEEE 1012-2024](https://standards.ieee.org/ieee/1012/7324/), published 2025-08-22.
10. NASA, [IV&V Overview](https://www.nasa.gov/ivv-overview/), updated 2024-07-23.
11. NASA, [SWE-052 Bidirectional Traceability](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052%2B-%2BBidirectional%2BTraceability), current handbook accessed 2026-07-24.
12. Pact Foundation, [Contract Tests vs Functional Tests](https://docs.pact.io/consumer/contract_tests_not_functional_tests), updated 2022-03-02.
13. Petrovic et al., [Practical Mutation Testing at Scale: A View from Google](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/), IEEE TSE, 2021.
14. Petrovic et al., [An Industrial Application of Mutation Testing](https://research.google/pubs/an-industrial-application-of-mutation-testing-lessons-challenges-and-research-directions/), Mutation 2018.
15. Leong et al., [Assessing Transition-based Test Selection Algorithms at Google](https://research.google/pubs/assessing-transition-based-test-selection-algorithms-at-google/), ICSE 2019.
16. Chen et al., [Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents](https://arxiv.org/abs/2602.07900), preprint revised 2026-04-09.
17. Sun et al., [SWE-Mutation: Can LLMs Generate Reliable Test Suites in Software Engineering?](https://arxiv.org/abs/2605.22175), preprint submitted 2026-05-21.

### Secondary sources

None used for recommendation-critical claims.

### Agent contributions

- Codex lead: local codebase inspection, primary-source verification, disagreement adjudication, synthesis.
- Independent Codex SDD subagent: product/process falsification and minimal artifact model.
- Independent Codex verification subagent: traceability, oracle sensitivity, boundary testing, and stop conditions.
- Claude via official `claude-peer`: first-principles artifact-chain critique; no unverified citations were promoted.
- Gemini via approved agy router, actual route `google300 Vertex/gemini-3.5-flash`: compressed-contract proposal and objections; overclaims were independently checked or rejected.
