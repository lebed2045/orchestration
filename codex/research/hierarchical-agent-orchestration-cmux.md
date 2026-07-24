# Research: Hierarchical agent orchestration in cmux

Generated: 2026-07-21 19:17:10 WITA
Mode: full; Codex lead, two independent research subagents, primary web research, Claude peer, Gemini/Antigravity router (local Vertex fallback)
Degradation: Claude peer had no network and supplied memory-derived locators that required chair verification. Gemini used the approved router's google300 Vertex fallback because Antigravity quota was unavailable. No live team was spawned, so the documented `cmux claude-teams` plus `/cc` composition remains operationally untested.

## Question and Scope

What is the established terminology and best-practice architecture for a human-supervised planning agent that splits a spec into parallel tracks, delegates each track to a manager/worker session in cmux, monitors liveness and progress, and periodically integrates results? Should every Claude Code session learn manager behavior through global `~/.claude/CLAUDE.md`, or should management be an explicit role?

This run is advisory. It did not edit global Claude instructions, launch or disturb the user's active cmux sessions, or implement a new workflow.

## Assumptions

- A parallel track is valuable only when it has a useful independent deliverable and sufficiently disjoint write ownership.
- `/cc` remains the implementation workflow inside one track: Claude owns its acceptance and review gates while Codex authors the plan/tests/code/fixes.
- Git/worktree/test evidence is more trustworthy than terminal transport acknowledgements, CPU use, or an agent's prose status.
- Human approval remains required for destructive or externally consequential actions.

## Executive Summary

The proposal is a recognized pattern: **centralized hierarchical multi-agent orchestration**, usually called **orchestrator-workers**, **manager-workers**, or a **team lead with teammates**. The best name for the work decomposition is **spec → dependency graph → parallel tracks/workstreams → tasks → runs**, with **fan-out/fan-in** around the independent tracks.

It is good practice **selectively**, not universally. Use it when tracks are genuinely parallel, low-coupling, isolated, and independently verifiable. Anthropic explicitly warns that coding often has fewer truly parallel tasks than research, and Google Research's controlled study found multi-agent coordination helped parallelizable tasks but harmed sequential planning. More agents are not automatically better.

The local stack already has the right transport and UI layer:

- installed Claude Code: `2.1.216`;
- agent teams enabled in `~/.claude/settings.json`;
- installed cmux: `0.64.20`, exposing `cmux claude-teams`;
- cmux's first-party integration launches Claude agent teams as native cmux splits with messaging, capture, metadata, and notifications.

Therefore: **do not build the manager around raw `cmux send`.** Use `cmux claude-teams` for session coordination and add a dedicated, explicit-only `/manager` skill as the policy layer above per-track `/cc` sessions.

Do **not** teach the full manager playbook globally. Teach only a tiny universal protocol globally: management requires an explicit role; transport acknowledgement is not execution; parallel writers need isolated ownership; status claims need artifact evidence. Keep task decomposition, dispatch, monitoring, retry, and integration mechanics in `/manager`, globally discoverable but dormant until invoked.

## Codebase Patterns

The current repository already has the lower layer of the proposed hierarchy:

```text
Human / Principal
└── /manager (new, explicit-only) — program orchestrator and integration owner
    ├── Track lead A: Claude session running /cc in worktree A
    │   ├── Codex: plan → RED → GREEN → fixes/cops
    │   └── fresh Claude: final track review
    └── Track lead B: Claude session running /cc in worktree B
        ├── Codex: plan → RED → GREEN → fixes/cops
        └── fresh Claude: final track review
```

- `/cc` is already a bounded single-track lead: Claude defines the acceptance contract and review gates, while Codex authors the plan, tests, implementation, and fixes ([`.claude/skills/cc/SKILL.md:3`](../../.claude/skills/cc/SKILL.md), [`.claude/skills/cc/SKILL.md:10`](../../.claude/skills/cc/SKILL.md)).
- The repository deliberately puts complete workflow mechanics in command/skill files and keeps `CLAUDE.md` for general rules ([`CLAUDE.md:48`](../../CLAUDE.md)).
- The global file distinguishes global commands from global rules, so a globally installed skill does not need to become always-on behavior (`~/.claude/CLAUDE.md:525-531`).
- The README already installs `/cc` as a globally discoverable skill at `~/.claude/skills/cc/` ([`README.md:31`](../../README.md)). `/manager` should follow the same discovery pattern.

The live worktree was already dirty before this research, including the cited workflow/documentation files. These citations describe current filesystem contents, not necessarily committed `HEAD`.

### Recommended vocabulary

| Layer | Recommended term | Responsibility |
|---|---|---|
| Human | Principal / accountable owner | sets intent, approves consequential actions, resolves policy conflicts |
| Top agent | Program orchestrator / team lead | owns spec, dependency graph, allocation, reconciliation, integration |
| Middle agent | Track lead | owns one independently verifiable workstream; in this repo, a `/cc` session |
| Implementer | Worker | executes a bounded task inside the track; here, Codex roles under `/cc` |
| Attempt | Run | one bounded execution attempt, replaceable without losing durable task state |
| Isolation unit | Lane | one track/session + worktree + branch + owned paths |

Use **supervisor** when discussing lifecycle duties such as liveness, restart, and retry budgets; use **orchestrator** or **team lead** for decomposition, routing, and synthesis. **Control plane vs execution plane** is a useful distributed-systems analogy, not the primary agent-product terminology.

## External Evidence and Reference Implementations

1. Anthropic defines the **orchestrator-workers** workflow as a central LLM dynamically decomposing work, delegating it, and synthesizing results. It also advises using the simplest architecture that works and accepting agent complexity only when the performance trade-off warrants it ([Building effective agents, 2024-12-19](https://www.anthropic.com/engineering/building-effective-agents)).
2. Anthropic's production research system uses a lead agent and parallel specialized subagents, but its engineering report says coding often has fewer truly parallelizable tasks and many dependencies are a poor fit; multi-agent runs also have substantial token cost ([multi-agent research system, 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system)).
3. Claude Code's native **agent teams** use a team lead, teammates, shared task list, direct messaging, plan approval, automatic delivery, and idle/API-error notifications. The docs recommend teams for independent modules/cross-layer work, not sequential or same-file work ([agent teams](https://code.claude.com/docs/en/agent-teams)).
4. Claude Code distinguishes subagents, human-dispatched background sessions, lead-managed agent teams, and scripted dynamic workflows; worktrees provide edit isolation rather than coordination ([parallel agents](https://code.claude.com/docs/en/agents), [worktrees](https://code.claude.com/docs/en/worktrees)).
5. cmux provides a first-party `cmux claude-teams` launcher that translates Claude's tmux operations into native cmux splits and maps send/capture/list/kill operations through its socket API ([cmux Claude teams](https://cmux.com/docs/agent-integrations/claude-code-teams)). Its CLI separately defines `send` (text input) and `send-key enter` (keypress), directly explaining why a successful `send` did not submit the prompt ([cmux CLI](https://cmux.com/docs/api)).
6. OpenAI's Agents SDK distinguishes **manager-style orchestration** (manager retains control and shared guardrails) from handoffs, and recommends deterministic code orchestration when predictability matters ([Agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)).
7. Google Research evaluated 180 agent configurations. In the studied benchmarks, centralized coordination improved a parallelizable task while every multi-agent variant degraded sequential planning; centralized topology also contained error amplification better than independent agents ([Google Research, 2026-01-28](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/), [paper](https://arxiv.org/abs/2512.08296)).
8. GitHub's engineering guidance treats multi-agent workflows as distributed systems: define typed boundaries and constrained actions, validate every boundary, log intermediate state, and expect partial failure ([GitHub, 2026-02-24](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)).
9. A2A's task protocol separates submitted, working, completed, failed, canceled, input-required, and authorization-required states and supports polling, streaming, and push updates. It is a useful vocabulary model even if A2A is not adopted ([A2A v1 specification](https://a2a-protocol.org/latest/specification/)).
10. Kubernetes control loops continuously compare desired and observed state; its startup/liveness/readiness distinction illustrates why “process exists,” “work can proceed,” and “task is correct” are different signals ([controllers](https://kubernetes.io/docs/concepts/architecture/controller/), [probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)).
11. Magentic-One uses an orchestrator that plans, tracks progress, and replans after errors ([paper, 2024-11-07](https://arxiv.org/abs/2411.04468)). Erlang/OTP supervision provides a mature analogy for bounded restart intensity rather than endless retries ([supervisor behavior](https://www.erlang.org/doc/system/sup_princ.html)).

## Pitfalls and Trade-offs

| Risk | Consequence | Required control |
|---|---|---|
| Fake parallelism | coordination costs exceed saved time | parallelize only dependency-free or weakly coupled tracks |
| Same-file/shared-contract edits | overwrite or semantic merge conflict | disjoint path ownership; serialize hot/shared files through the top lead |
| Transport ack mistaken for execution | stale composer text and zero progress look successful | separate COMPOSED/SUBMITTED/WORKING states; prove state at the target and in artifacts |
| Screen/CPU as source of truth | live-but-blocked or stale sessions look healthy | screen is diagnostic; ledger, task state, git, tests, and review are authoritative |
| Recursive management | delegation explosion, unclear accountability | only explicitly assigned leads may create/manage peer sessions; native teams forbid nesting |
| Lead as bottleneck | slow synthesis and context overload | track leads return compact structured evidence and durable artifact references |
| Unbounded retries | repeated failures consume time/quota | retry budgets by failure cause, then replan or escalate |
| Status lag/premature shutdown | lead reports done while work is incomplete | reconcile every declared state against target session and repository evidence |
| Permission inheritance | workers receive more authority than intended | start with bounded permissions and preserve human gates for consequential actions |
| Experimental native teams | resume/status/shutdown limitations | preserve an external ledger and make runs replaceable |

## Disagreements and Adjudication

| Position | Evidence | Adjudicating source | Verdict |
|---|---|---|---|
| “Every Claude should be a manager” | ambient availability might improve delegation | Claude teammates all load global `CLAUDE.md`; native teams prohibit nested teams; global text costs every session | Rejected. Globalize only universal role/safety invariants; keep the playbook explicit-only. |
| “A manager should inspect tabs every 30 minutes” | periodic checks catch silent stalls | Claude teams provide event/idle/error delivery; A2A distinguishes streaming/push from higher-latency polling | Use events for normal operation and a configurable periodic reconciliation watchdog. No universal 30-minute constant. |
| “More managers/agents are better” | broader parallel capacity | Google study shows topology- and task-dependent gains plus large sequential penalties; Anthropic warns coding has fewer parallel tasks | Rejected as a default. Scale only with demonstrated independent tracks. |
| “Use raw cmux send/read-screen as orchestration” | simple and already familiar | cmux has a native Claude Teams integration; raw send and Enter are separate operations | Use `cmux claude-teams`; retain read-screen as diagnostic proof, not the task protocol. |
| “Each track needs another general manager layer” | local autonomy | `/cc` already manages planning/coding/review inside one track; Claude agent teams disallow nested teams | Usually redundant. Treat each `/cc` session as the track lead. Add deeper hierarchy only when a track independently justifies it. |
| Gemini proposed fixed 180-second heartbeats and automatic killing | fast failure detection | no source supported that universal threshold; Kubernetes warns bad liveness probes can cause cascading failure | Rejected. Timeouts are phase/task-specific, and termination requires bounded policy plus recoverable state. |

## Uncertainty and Unresolved Questions

- `cmux claude-teams` and teammate loading of user skills/MCP are documented and locally available, but this research did not launch a team or prove that a teammate can execute the complete local `/cc` workflow end to end. Treat that composition as **UNVERIFIED operationally** until a small, disposable smoke test runs.
- Claude agent teams remain experimental and document status-lag, session-resumption, shutdown, and no-nesting limitations. The external manager ledger is therefore required even when native teams are used.
- The exact integration/merge policy depends on the target repository's dependency graph, test cost, and hot-file set; it should not be universalized in global instructions.
- The Google scaling results are strong evidence against universal multi-agent scaling, but they cover selected benchmarks rather than this exact Claude/cmux coding topology.

## Recommended Approach

### 1. Use the existing native control surface

Launch the top session through `cmux claude-teams`, not through a home-grown loop of `cmux send` calls. Let Claude's team lead own native task assignment and messaging while cmux provides splits, capture, and notifications.

### 2. Add one explicit-only `/manager` skill above `/cc`

The skill should:

1. read the spec and produce a dependency DAG;
2. refuse fan-out for sequential, same-file, or unresolved-interface tracks;
3. map each parallel track to one owner, worktree, branch, allowed paths, dependencies, acceptance evidence, and stop conditions;
4. spawn the minimum useful number of track leads and give each a full delegation contract;
5. instruct each track lead to run `/cc` for its single track;
6. consume native task/idle/error events and reconcile them against git/test/review artifacts;
7. bound retries by repeated cause and escalate/replan instead of endlessly nudging;
8. verify each track and then run an integration gate before claiming the program complete.

Recommended manager state machine:

```text
PLANNED → DISPATCHED → WORKING → READY → VERIFIED → INTEGRATED
                         ├── INPUT_REQUIRED
                         ├── BLOCKED
                         └── FAILED
```

For any legacy/manual cmux dispatch, add a transport-only pre-state:

```text
COMPOSED → SUBMITTED → DISPATCHED
```

`cmux send OK` proves only `COMPOSED`. Enter plus visible target receipt can prove `SUBMITTED`. Only target task state or useful artifact movement proves `WORKING`. Only acceptance evidence proves `VERIFIED`.

Minimum ledger fields:

```text
track_id, objective, dependencies, owner, worktree, branch, owned_paths,
session_id/surface_id, state, last_observed_at, HEAD, changed_paths,
test_evidence, review_verdict, blocker, retry_count, next_action
```

### 3. Keep the global rule tiny

Proposed universal protocol, not yet applied:

```markdown
### Agent-management boundary
- Create or manage peer sessions only when explicitly assigned the team-lead/manager role; bounded subagents or MCP roles required by an invoked workflow remain allowed.
- Transport acknowledgement is not execution: distinguish dispatched, working, blocked, verified, and integrated states, and attach target-session plus repository/test evidence to status claims.
- Parallel mutating tracks require isolated worktrees and disjoint ownership; cross-track or shared-contract changes escalate to the lead.
```

Install the full playbook as `~/.claude/skills/manager/SKILL.md` so it is globally available but not globally active. This matches the repository's existing `/cc` installation model and avoids turning every leaf worker into a recursive coordinator.

### 4. Monitoring policy

- Primary: native task updates, teammate messages, idle/error notifications, CI/test completion.
- Reconciliation: on every state transition and on a configurable watchdog interval, compare spec/ledger desired state with native task state, target screen, branch HEAD/diff, and tests.
- Escalate on semantic stalls, repeated identical failure, ownership conflict, dependency violation, missing authority, or no evidence-bearing progress.
- Do not hard-code “every 30 minutes” as the only liveness mechanism. It is acceptable as a coarse backstop for long tasks, but too slow for cheap failures and unnecessarily noisy for very long phases.

## Sources

### Codebase files

- `.claude/skills/cc/SKILL.md:3,10,16-23`
- `CLAUDE.md:42,48,54-56`
- `README.md:22-34`
- `~/.claude/CLAUDE.md:525-531`
- `~/.claude/settings.json:3`

### Primary web and paper sources

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), 2024-12-19
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), 2025-06-13
- [Claude Code: Agent teams](https://code.claude.com/docs/en/agent-teams), retrieved 2026-07-21
- [Claude Code: Run agents in parallel](https://code.claude.com/docs/en/agents), retrieved 2026-07-21
- [Claude Code: Worktrees](https://code.claude.com/docs/en/worktrees), retrieved 2026-07-21
- [cmux: Claude Code Teams](https://cmux.com/docs/agent-integrations/claude-code-teams), retrieved 2026-07-21
- [cmux: CLI reference](https://cmux.com/docs/api), retrieved 2026-07-21
- [OpenAI Agents SDK: Agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/), retrieved 2026-07-21
- [Google Research: Towards a science of scaling agent systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/), 2026-01-28
- [Kim et al.: Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296), submitted 2025-12-09
- [GitHub: Multi-agent workflows often fail](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/), 2026-02-24
- [A2A Protocol v1 specification](https://a2a-protocol.org/latest/specification/), retrieved 2026-07-21
- [Kubernetes: Controllers](https://kubernetes.io/docs/concepts/architecture/controller/), last modified 2024-09-01
- [Kubernetes: Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/), retrieved 2026-07-21
- [Fourney et al.: Magentic-One](https://arxiv.org/abs/2411.04468), submitted 2024-11-07
- [Erlang/OTP: Supervisor Behaviour](https://www.erlang.org/doc/system/sup_princ.html), OTP 29.0.3, retrieved 2026-07-21

### Secondary sources

- None used for recommendation-critical claims.

### Agent contributions

- Independent local-architecture Codex subagent: current workflow/role-boundary audit.
- Independent prior-art Codex subagent: terminology, product patterns, and failure modes.
- Claude peer: role vocabulary, desired-vs-observed control loop, and global-constitution vs role-playbook split; URLs independently verified where material.
- Gemini/Antigravity router via google300 Vertex fallback: argued for role-specific management and out-of-band verification; unsupported fixed timings and causal claims were rejected.
