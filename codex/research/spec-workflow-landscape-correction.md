# Research: Correction to the AI Spec-Driven Development Workflow Recommendation

Generated: 2026-07-24, Asia/Makassar

Mode: Full adversarial run — Codex lead, two independent Codex research agents, Claude, Gemini/Antigravity route

Degradation: Claude had no live web access. Antigravity quota was exhausted and the approved router used google300 Vertex/gemini-3.5-flash. Both external passes made stale or false factual claims; those claims were rejected through current primary-source verification.

## Question and Scope

The previous research recommended GitHub Spec Kit without first comparing the maintained ecosystem around:

- Obra Superpowers
- Fission-AI OpenSpec
- BMAD Method
- Agent Skills
- GitHub Spec Kit

This correction asks:

1. Are these direct substitutes or different layers?
2. Which addresses uncertain product intent, a large brownfield codebase, and weak AI verification?
3. Which workflow minimizes ceremony without discarding durable intent?
4. What should a solo developer using Claude Code and Codex actually adopt?

## Assumptions

- The speech-transcribed phrase “ID US money agent skills” is interpreted as BMAD Method and Agent Skills. If it named another project, that project remains to be added.
- “Standard” distinguishes a documented interoperability format from a popular methodology. Popularity alone is not treated as proof.
- The target is a solo developer working in existing repositories, not a regulated multi-team program.
- Current sources were accessed on 2026-07-24.

## Executive Summary

The previous recommendation should be withdrawn. It omitted the most relevant workflow landscape and recommended Spec Kit despite a first-party template making tests optional unless explicitly requested. That is a poor default for a user whose primary complaint is inadequate AI testing.

The corrected category map is:

| Candidate | Actual category | Relationship |
|---|---|---|
| Agent Skills | Open packaging and discovery format for reusable agent procedures | Foundation under workflows; not an SDLC |
| Obra Superpowers | Opinionated, automatically activated software-development methodology implemented as composable skills | Full workflow; strongest built-in TDD and evidence discipline |
| Fission-AI OpenSpec | Living-spec and change-delta system | Artifact/source-of-truth workflow |
| GitHub Spec Kit | Per-feature spec → plan → tasks → implementation pipeline | Artifact and planning workflow |
| BMAD Method | Adaptive product-discovery through delivery methodology with multiple tracks and roles | Broadest product/program workflow |

There is an emerging de facto interoperability convention here: Agent Skills defines `SKILL.md`, and its current client guide calls `.agents/skills/` a widely adopted cross-client location. That standard says how procedures travel; it does not decide which development procedure is correct.

For this user:

- **Ready-made replacement for the custom workflow:** use **Superpowers** first. It directly covers codebase exploration, question-driven design, approved written specs, detailed plans, TDD, task review, and fresh verification evidence.
- **Durable current-system behavior and change history:** use **OpenSpec as the sole artifact owner**, then use selected TDD/debugging/verification skills inspired by Superpowers. Do not install both complete lifecycles unchanged.
- **Major product discovery or a large undocumented brownfield system:** use **BMAD selectively** for `document-project`, `project-context.md`, or its full method; use Quick Flow for ordinary changes.
- **Spec Kit:** choose it only when its large integration matrix and standardized artifact pipeline matter more than verification defaults, and first customize it to require tests and runtime evidence.

## Codebase Patterns

The local orchestration repository already implements much of Superpowers as Agent Skills:

- `$wf` is an explicit-only Agent Skill with tiered TDD, optional worktree isolation, fresh RED/GREEN passes, final verification, subagent review, and evidence-backed completion (`codex/.agents/skills/wf/SKILL.md:1-28`, `61-107`).
- Its verification contract requires a quick test, relevant full test/lint/build command, diff inspection, and an execution receipt (`codex/.agents/skills/wf/SKILL.md:71-87`, `105-107`).

This means the user did partially reinvent Superpowers. The meaningful differences are:

| Local `$wf` | Superpowers |
|---|---|
| Explicit invocation only | Automatically activates applicable skills |
| Tiered ceremony | Design process required even for simple/config changes |
| Worktree optional | Worktree is part of the standard lifecycle |
| Commit only when authorized | Brainstorming currently instructs the agent to commit the design |
| Optional external Claude/Gemini reviews | Fresh task subagent plus spec and code-quality reviews |
| Temporary spec/architecture notes | Persistent dated design and plan artifacts |

Installing full Superpowers into this orchestration repository without reconciling ownership would create overlapping workflow rules. It would also conflict with the repository’s explicit commit-authorization boundary.

## External Evidence and Reference Implementations

### Agent Skills

Agent Skills is an open, lightweight format: a directory containing required `SKILL.md` instructions and optional scripts, references, and assets. It uses progressive disclosure and supports reusable workflows across compatible agents.

The current client implementation guide states that `.agents/skills/` has emerged as a widely adopted cross-client convention while also noting that the formal specification does not mandate installation paths. Agent Skills therefore provides format portability, not identical behavior, dependency management, or an SDLC.

### Obra Superpowers

Superpowers describes itself as a complete development methodology built from composable skills. Its current flow:

1. explores current project context;
2. asks clarification questions one at a time;
3. presents multiple approaches and a design for approval;
4. saves a dated design;
5. writes an exact implementation plan;
6. uses subagent-driven implementation;
7. enforces RED → GREEN TDD;
8. reviews tasks;
9. requires fresh command evidence before completion.

Its verification skill explicitly forbids completion claims without running the full proving command in the current message. Of the compared ready-made methodologies, this is the strongest first-party verification default.

The cost is rigidity and token/interaction overhead. Current brainstorming requires design even for simple changes, and capable harnesses use mandatory subagent-driven development. Its latest documentation supports Claude Code, Codex, Gemini, Copilot, Cursor, and other harnesses, but installation and adapters remain harness-specific.

### Fission-AI OpenSpec

OpenSpec is not a JSON/YAML schema system, contrary to the Gemini pass. Its product artifacts are Markdown:

- living domain specifications under `openspec/specs/`;
- one change folder containing `proposal.md`, delta specs, `design.md`, and `tasks.md`;
- archive merges deltas into the current specs and preserves history.

This is the strongest artifact model for an evolving brownfield product because it distinguishes current behavior from proposed changes. `/opsx:explore` reads the affected code before creating artifacts, and the default path is comparatively short.

Its verification is weaker than Superpowers. `/opsx:verify` is available only in the expanded profile, searches the codebase for evidence, and reports critical/warning/suggestion findings. Warnings and incomplete tasks do not block archive. A deterministic test and runtime-evidence gate must be added separately.

### BMAD Method

BMAD covers a broader lifecycle than the other candidates. It can generate `project-context.md`, document an established codebase, produce product briefs/PRDs and architecture, break work into epics and stories, implement stories with tests, and perform code review.

It adapts ceremony:

- Quick Flow performs clarification, planning, implementation, review, and presentation for bounded work.
- Full Method adds product and architecture phases.
- Larger tracks add still more governance.

BMAD is valuable for deep brownfield onboarding and major product discovery. Full BMAD is the most cumbersome daily default; advanced traceability, ATDD, risk, and non-functional testing are in its separately installed TEA module rather than guaranteed by the base path.

### GitHub Spec Kit

Spec Kit has excellent integration coverage and clear separation between specification, planning, tasks, analysis, implementation, and convergence. Its optional clarification, checklist, and analysis gates are useful.

However:

- its official task template says tests are optional unless explicitly requested;
- `analyze` verifies consistency among prose artifacts, not runtime behavior;
- specialized brownfield discovery appears primarily through community extensions;
- every decomposed sub-feature repeats the spec/plan/tasks artifact set.

It remains a good neutral framework, but it was not justified as the default for this user.

## Pitfalls and Trade-offs

1. **Do not stack full Superpowers and full OpenSpec unchanged.** Both own discovery, specification, design, planning, implementation, and verification. The result is duplicate specs, duplicate plans, and conflicting gates.
2. **Agent Skills portability is not behavioral reproducibility.** Clients vary in discovery paths, activation, compaction behavior, tools, permissions, and subagent support.
3. **Full Superpowers is intentionally rigid.** This protects quality but may be disproportionate for tiny changes and can conflict with local commit/worktree policies.
4. **OpenSpec’s living-spec model can become stale.** Archive and delta synchronization do not prove the running system matches the resulting spec.
5. **BMAD personas are not independent evidence.** Multiple named roles may still use one underlying model and shared assumptions.
6. **Spec Kit consistency is not validation.** A perfectly coherent spec/plan/tasks chain can still describe and implement the wrong product.
7. **No framework solves oracle quality.** Acceptance criteria still need observable outcomes and tests that fail for the wrong behavior.

## Disagreements and Adjudication

| Question | Positions | Primary-source adjudication | Verdict |
|---|---|---|---|
| Are all five competing frameworks? | Gemini forced them into inaccurate layers; Claude and Codex separated layers | Agent Skills defines packaging; each project’s own documentation defines its lifecycle | Different categories; only the process frameworks substantially substitute |
| Is Agent Skills merely a tool-definition mechanism? | Gemini said yes | Agent Skills explicitly packages instructions, scripts, references, assets, and repeatable workflows | Gemini claim rejected |
| Is Spec Kit GitHub/Copilot-locked? | Gemini said yes | Current Spec Kit documentation advertises 35 integrations, including Codex and Claude | Gemini claim rejected |
| Is Superpowers Claude-only? | Claude said yes | Current Superpowers README documents Claude, Codex, Gemini, Copilot, Cursor, and others | Claude claim rejected as stale |
| Is OpenSpec a high-ceremony JSON/YAML schema? | Gemini said yes | Current OpenSpec examples and artifact documentation use plain Markdown and a short core flow | Gemini claim rejected |
| Which has the strongest testing default? | Codex favored Superpowers; other passes said every framework needs an added gate | Superpowers mandates failing tests and fresh full-command evidence; Spec Kit tests are optional; OpenSpec verify is optional/advisory; BMAD advanced testing is modular | Superpowers strongest default, though project-specific acceptance coverage remains necessary |
| Should OpenSpec and Superpowers be combined wholesale? | Some passes suggested a hybrid | Their first-party workflows both own spec/design/plan/apply/review stages | Do not combine whole systems; assign one artifact owner and compose selected execution skills |
| Is BMAD necessarily too heavy? | Claude said yes; Codex found adaptive tracks | BMAD provides Quick Flow and a separate full method | Not necessarily; Quick Flow is viable, full method is high ceremony |
| Is Spec Kit the practical default? | Prior answer said yes; all adversarial passes failed to defend it for this user | Tests optional, weaker first-party brownfield discovery, artifact consistency rather than runtime proof | Rejected for this user’s primary failure modes |

Recommendation-critical disagreements unresolved: 0.

## Uncertainty and Unresolved Questions

1. The speech-transcribed project name may identify something other than BMAD Method.
2. Agent Skills has strong interoperability momentum, but no neutral comparative benchmark proves identical skill behavior across harnesses.
3. No controlled comparative study establishes a universal quality or productivity winner among these workflows.
4. The best ceremony level still needs a local pilot measuring human interventions, elapsed time, defects, and token/quota usage.
5. Selecting individual Superpowers skills instead of the whole plugin may require local adaptation and maintenance.

## Recommended Approach

### Decision table

| Actual need | Choose |
|---|---|
| Replace a custom cumbersome workflow with a ready-made guarded coding method | Full Superpowers |
| Keep an authoritative description of current system behavior plus auditable proposed changes | OpenSpec as artifact owner |
| Add portable reusable procedures to Claude, Codex, and other agents | Agent Skills |
| Deeply document a large existing codebase or conduct full product/architecture discovery | BMAD selectively |
| Standardize one artifact pipeline across the broadest integration matrix | Spec Kit, customized to mandate verification |

### Recommended first pilot for this user

1. Do not install Spec Kit based on the previous answer.
2. In a disposable or low-risk repository, run one real bounded feature using full Superpowers.
3. Measure:
   - clarification turns;
   - time to approved design;
   - token/quota use;
   - unsupported completion claims;
   - defects found before and after review;
   - whether the dated spec remains useful after implementation.
4. If the missing capability is a living current-system specification, switch the artifact owner to OpenSpec.
5. Under OpenSpec, retain a single execution skill requiring:
   - acceptance criterion → deterministic check mapping;
   - observed RED before implementation where practical;
   - quick and relevant full regression commands;
   - fresh runtime evidence;
   - independent adverse-path review.
6. Use BMAD’s `document-project` or `project-context.md` only when a repository is too large to navigate safely through slice-local reconnaissance.
7. Do not run full Superpowers, OpenSpec, Spec Kit, and BMAD together.

The pragmatic architecture is:

```text
PRODUCT.md
    product intent and roadmap
        |
        v
one artifact owner
    Superpowers design/plan
    OR OpenSpec current specs + change deltas
    OR BMAD track
        |
        v
Agent Skills execution discipline
    reconnaissance -> test sensitivity -> implementation -> fresh verification
        |
        v
CI and real runtime evidence
```

## Sources

### Local codebase files

1. `codex/.agents/skills/wf/SKILL.md` — explicit tiered TDD, subagents, verification, review, and completion evidence.
2. `codex/.agents/skills/in-browser-verify/SKILL.md` — durable scenario and browser-evidence contract.

### Primary web sources

1. Agent Skills, [Overview](https://agentskills.io/home), accessed 2026-07-24.
2. Agent Skills, [Specification](https://agentskills.io/specification), accessed 2026-07-24.
3. Agent Skills, [Client implementation guide](https://agentskills.io/client-implementation/adding-skills-support), accessed 2026-07-24.
4. Obra, [Superpowers repository and installation](https://github.com/obra/superpowers), accessed 2026-07-24.
5. Obra, [Superpowers brainstorming skill](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md), accessed 2026-07-24.
6. Obra, [Superpowers TDD skill](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md), accessed 2026-07-24.
7. Obra, [Superpowers verification-before-completion skill](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md), accessed 2026-07-24.
8. Obra, [Superpowers releases](https://github.com/obra/superpowers/releases), accessed 2026-07-24.
9. Fission-AI, [OpenSpec repository](https://github.com/Fission-AI/OpenSpec), accessed 2026-07-24.
10. Fission-AI, [OpenSpec getting started](https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md), accessed 2026-07-24.
11. Fission-AI, [OpenSpec commands](https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md), accessed 2026-07-24.
12. BMAD, [Installation](https://docs.bmad-method.org/how-to/install-bmad/), accessed 2026-07-24.
13. BMAD, [Established projects](https://docs.bmad-method.org/how-to/established-projects/), accessed 2026-07-24.
14. BMAD, [Workflow map](https://docs.bmad-method.org/reference/workflow-map/), accessed 2026-07-24.
15. BMAD, [Testing options](https://docs.bmad-method.org/reference/testing/), accessed 2026-07-24.
16. GitHub, [Spec Kit Agentic SDD](https://github.github.com/spec-kit/reference/agentic-sdd.html), accessed 2026-07-24.
17. GitHub, [Spec Kit integrations](https://github.github.com/spec-kit/reference/integrations.html), accessed 2026-07-24.
18. GitHub, [Spec Kit task template](https://github.com/github/spec-kit/blob/main/templates/tasks-template.md?plain=1), accessed 2026-07-24.

### Secondary sources

None used for recommendation-critical claims.

### Agent contributions

- Codex lead: current primary-source inspection, local-workflow comparison, adjudication, synthesis.
- Codex research agent 1: Superpowers, OpenSpec, and Agent Skills adversarial comparison.
- Codex research agent 2: Spec Kit, BMAD, and OpenSpec adversarial comparison.
- Claude: independent first-principles pass; stale portability claims rejected.
- Gemini via approved router: independent pass; multiple factual claims rejected.
