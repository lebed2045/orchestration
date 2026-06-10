# Research: Codex vs Claude Agentic Coding Workflows

Generated: 2026-06-10 15:14 WITA
Mode: `$research` skill, codebase + external web research
Canonical path: `codex/.agents/codex/research/codex-claude-agentic-coding-workflows.md`
Degradation: no callable Claude research tool was available from this Codex session; external comparison is based on official docs and practitioner writeups.

---

## Executive Summary

The best-practice workflow is **mostly the same at the engineering level** across Codex and Claude: understand the code, plan when scope is non-trivial, implement in small batches, prove the change with tests or another executable check, review the diff, and only then commit/merge.

The difference is **not the gates**. The difference is the **native control surface**:

- Claude Code is optimized around `CLAUDE.md`, `.claude/commands`, plan mode, checkpoints/rewind, subagents, hooks, and worktrees.
- Codex is optimized around `AGENTS.md`, skills, explicit goal/context/constraints/done-when prompts, `/goal`, `/review`, app/CLI/cloud surfaces, and repo/user skill discovery.

So the correct answer is: **same principles, different mechanics**. A literal copy of the Claude workflow into Codex is not ideal. The Codex version should preserve the verification gates, but express them with Codex-native surfaces and keep ceremony tiered.

---

## Codebase Patterns

### Current Claude Workflow

This repo's Claude side has a rigorous workflow:

- `.claude/commands/wf.md` implements tiered TDD, split RED/GREEN, optional worktree isolation, optional Codex/Gemini review, final verification, and evidence-graded gates.
- `CLAUDE.md` requires proof before completion claims via `EXECUTION_BLOCK`.
- `.claude/agents/` contains reviewer/cops such as coverage, metrics, simplicity, and coherence.
- Prior local research notes pointed toward the same conclusion: start simple, add gates when risk or repeated failures justify them, and never trust generated code without evidence.

### Current Codex Workflow

The Codex side now mirrors the intent, but uses skills:

- `codex/.agents/skills/wf/SKILL.md` is the Codex equivalent of `/wf`.
- `codex/.agents/skills/research/SKILL.md` is the Codex equivalent of `/research`.
- `codex/.agents/skills/think/SKILL.md` is the Codex equivalent of `/think`.
- `AGENTS.md` explains that Codex uses `$wf`, `$research`, and `$think`, not repo-local slash commands.

Important local convention:

- In Claude commands, `-c` means Codex.
- In Codex skills, `-c` means Claude.
- In both, `-g` means Gemini/Antigravity.

This convention is reasonable because `-c` now means "ask the other main model," but only if the tool is actually available.

---

## External Patterns

### Official Codex Guidance

OpenAI's Codex guidance emphasizes a prompt contract: **goal, context, constraints, and done-when**. It also recommends planning before difficult tasks, keeping `AGENTS.md` practical, and improving reliability with tests, lint/type checks, behavior confirmation, and diff review. Source: [Codex best practices](https://developers.openai.com/codex/learn/best-practices).

The Codex workflows page recommends concrete verification loops: for bug fixes, provide repro steps, keep the fix minimal, add a regression test when feasible, then rerun the repro, lint, and the smallest relevant test suite. It also documents `/review` for local code review. Source: [Codex workflows](https://developers.openai.com/codex/workflows).

Codex goals are a particularly important difference from Claude command-style orchestration. A Codex Goal is a persistent completion contract: outcome, verification surface, constraints, boundaries, iteration policy, and blocked stop condition. Source: [Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).

Codex skills should stay focused: one job, explicit steps, and tested descriptions. Source: [Codex skills](https://developers.openai.com/codex/skills).

### Official Claude Code Guidance

Anthropic's Claude Code guidance is more prescriptive about the workflow shape:

1. Give Claude a way to verify its work.
2. Explore first.
3. Plan.
4. Implement.
5. Commit.

The docs explicitly say plan mode adds overhead, so skip it for one-sentence diffs, typos, logs, and other small tasks. Source: [Claude Code best practices](https://code.claude.com/docs/en/best-practices).

Claude also has strong native affordances that Codex should not imitate mechanically: plan mode, `CLAUDE.md`, `.claude/skills`, custom subagents, hooks, checkpoints/rewind, and parallel worktrees. The same official guide recommends hooks for actions that must happen every time, subagents for investigation/review, and fresh contexts for review. Source: [Claude Code best practices](https://code.claude.com/docs/en/best-practices).

Claude common workflows include "work with tests," "plan before editing," "delegate research to subagents," and "run parallel sessions with worktrees." Source: [Claude Code common workflows](https://code.claude.com/docs/en/common-workflows).

### Practitioners Who Ship

#### Simon Willison

Simon Willison's recurring rule is not model-specific: ship code you have proven works. He separates manual testing and automated testing, and says AI-generated code does not change the human accountability burden. Source: [Your job is to deliver code you have proven to work](https://simonwillison.net/2025/Dec/18/code-proven-to-work/).

His practical LLM coding workflow also says context is central, early research is useful, production use should become more directive after research, and coding agents are most useful when they can run the code and iterate. Source: [Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/).

Implication for this repo: `EXECUTION_BLOCK` and smallest-test verification are correct. The workflow should not optimize for "agent approved"; it should optimize for evidence.

#### Addy Osmani

Addy Osmani's 2026 workflow emphasizes specs before code, bite-sized tasks, tests, review, and human accountability. He frames the spec as an executable artifact for agents, not just prose. Sources: [My LLM coding workflow going into 2026](https://addyosmani.com/blog/ai-coding-workflow/), [How to write a good spec for AI agents](https://addyosmani.com/blog/good-spec/), and [AI writes code faster. Your job is still to prove it works](https://addyosmani.com/blog/code-review-ai/).

For multi-agent work, Addy recommends a production-line shape: Plan, Spawn, Monitor, Verify, Integrate, Retro. He also gives practical limits: do not run more agents than you can meaningfully review, kill stuck agents after repeated failures, and avoid multiple agents editing the same file. Source: [The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/).

Implication for this repo: the tiered workflow is right; mandatory heavy gates for every task are wrong. Use more agents only when the review bottleneck can handle them.

#### Peter Steinberger

Peter Steinberger's current workflow is intentionally less ceremonial. He reports using plan mode for larger tasks, small prompts for smaller tasks, one or two agents for most refactoring, about four for cleanup/tests/UI, and fewer MCPs when they do not carry their context cost. He also notes that tests written in the same context as implementation can catch issues effectively. Source: [My Current AI Dev Workflow](https://steipete.me/posts/2025/optimal-ai-development-workflow).

This is the strongest counterweight to a rigid split-TDD, always-multi-agent workflow. The lesson is not "no gates"; it is "do not pay the orchestration tax unless the blast radius justifies it."

---

## Pitfalls

### Copying Claude Workflow Literally Into Codex

Bad:

- Pretend `.codex/commands` is the Codex equivalent of `.claude/commands`.
- Recreate Claude-only primitives like `EnterPlanMode`, `Agent`, and `AskUserQuestion` in skill text.
- Preserve every gate even when Codex has a better native primitive, such as `/goal` or `/review`.

Better:

- Keep the same engineering invariants.
- Express them with Codex-native surfaces: `AGENTS.md`, skills, `/goal`, `/review`, shell verification, and clear "done when" contracts.

### Overusing Multi-Agent Review

The practitioner consensus is not "more agents = better." It is:

- use one agent for small changes;
- use plan/spec review for uncertain architecture;
- use fresh reviewers for risky diffs;
- use worktrees when parallel edits might collide;
- stop when repeated failures show the context is poisoned.

External reviewers should be opt-in or risk-triggered, not mandatory per micro-change.

### Treating TDD As One Universal Shape

TDD is still a strong gate, but strict split RED/GREEN is not always optimal.

- Split RED/GREEN is useful when you want independent test pressure and less implementation bias.
- Unified test+implementation can be better when the agent needs full context to discover edge cases quickly.
- For tiny edits, a direct change plus a focused verification command is enough.

This matters for Codex because Codex's strength is often a tight local loop with explicit completion criteria. A strict Claude-style split may add latency without improving quality for small/medium tasks.

### Letting Research Become Coding

`$research` is for discovery and synthesis. It should not mutate source. For coding, use direct Codex or `$wf`.

---

## Recommended Approach

### Bottom Line

Use **the same gates**, but not always the same ceremony.

The universal workflow:

```text
Explore -> Plan/Spec -> Implement small -> Verify -> Review -> Commit -> Retro
```

Codex expression:

```text
AGENTS.md + $research when uncertain + $wf when coding + /goal for long uncertain loops + /review before commit
```

Claude expression:

```text
CLAUDE.md + /research when uncertain + /wf when coding + plan mode/hooks/subagents/worktrees when risk justifies it
```

### Practical Routing

| Situation | Codex workflow | Claude workflow | Why |
|---|---|---|---|
| Tiny one-line change | Direct prompt + run relevant check | Direct prompt + run relevant check | Planning/TDD ceremony is overhead. |
| Unknown architecture/library | `$research <topic>` or `$research -g <topic>` | `/research <topic>` or `/research -g <topic>` | Separate discovery from edits. |
| Normal small feature/fix | `$wf --tier=small <task>` | `/wf --tier=small <task>` | TDD + final verification. |
| Risky multi-file change | `$wf --tier=full <task>` | `/wf --tier=full <task>` | Plan, tests, review, metrics. |
| Ambiguous or long-running target | `/goal ...` or `$wf --goal "..."` | `/goal ...` or `/wf --goal "..."` if available | Persistent success contract. |
| Security/architecture-critical change | `$wf --tier=full -cg <task>` | `/wf --tier=full -cg <task>` | Cross-model review is worth the cost. |
| Refactor with broad surface | Plan first; consider worktree/cloud; verify before merge | Plan mode + worktree/subagents | Avoid file collisions and context rot. |

### What To Change In The Codex Version

Keep:

- tiered workflow;
- no completion claim without evidence;
- small quick test plus final verification;
- optional cross-model review;
- research before implementation when the approach is unclear.

Adjust:

- Make Codex `$wf` intentionally **tiered and lighter** than the Claude command.
- Prefer Codex-native `/goal` for long uncertain tasks instead of hand-rolled "keep going" loops.
- Prefer Codex `/review` for diff review when available.
- Consider unified TDD as the default for small tasks, or at least keep it easy to select; use split TDD when independent test pressure matters.
- Keep external Claude/Gemini review optional and final-gate focused, not part of every inner loop.

Do not add back `$r`; `$research` is clearer and avoids alias drift.

---

## Direct Answer

Are Codex and Claude best practices basically the same?

**Yes at the engineering level.**

Both want:

- specific context;
- plan/spec before complex edits;
- small batches;
- tests or executable checks;
- diff review;
- fresh context for review/research;
- durable repo guidance;
- clean stop conditions.

Are they the same workflow mechanically?

**No.**

Claude has stronger first-class workflow machinery around plan mode, hooks, subagents, checkpoints, and `.claude` command files. Codex has a stronger "goal contract + AGENTS.md + skills + review" shape. The right Codex workflow should feel like Codex, not like Claude wearing a different directory name.

Best concise policy:

```text
Use $research for uncertainty.
Use direct Codex for tiny edits.
Use $wf for code changes that need proof.
Use /goal for long uncertain loops.
Use /review or -cg only when risk justifies extra eyes.
```

---

## Sources

### Local Codebase

- `CLAUDE.md` — current Claude workflow rules and proof requirements.
- `AGENTS.md` — Codex repo guidance.
- `codex/.agents/skills/wf/SKILL.md` — Codex workflow skill.
- `codex/.agents/skills/research/SKILL.md` — Codex research skill.
- `.claude/commands/wf.md` — Claude workflow command.
- Prior local workflow research notes used during synthesis.

### Official Docs

- [OpenAI Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [OpenAI Codex workflows](https://developers.openai.com/codex/workflows)
- [Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
- [OpenAI Codex skills](https://developers.openai.com/codex/skills)
- [Codex AGENTS.md guidance](https://developers.openai.com/codex/guides/agents-md)
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code common workflows](https://code.claude.com/docs/en/common-workflows)

### Practitioner Sources

- [Simon Willison — Your job is to deliver code you have proven to work](https://simonwillison.net/2025/Dec/18/code-proven-to-work/)
- [Simon Willison — Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/)
- [Addy Osmani — My LLM coding workflow going into 2026](https://addyosmani.com/blog/ai-coding-workflow/)
- [Addy Osmani — How to write a good spec for AI agents](https://addyosmani.com/blog/good-spec/)
- [Addy Osmani — AI writes code faster. Your job is still to prove it works](https://addyosmani.com/blog/code-review-ai/)
- [Addy Osmani — The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/)
- [Peter Steinberger — My Current AI Dev Workflow](https://steipete.me/posts/2025/optimal-ai-development-workflow)
