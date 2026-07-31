---
name: think
description: Run a Codex-chaired, anti-sycophantic deliberation council with independent Codex, Claude, and Gemini/Antigravity perspectives, default peer critique and adversarial cross-examination, dissent, and persistent provenance. Use when the user invokes $think or /think, asks what to do or what Codex thinks, wants assumptions challenged, needs a judgment call without one objective ground truth, or wants to revisit the latest deliberation with --nudge.
---

# Think

**Updated:** `21-jul-2026`

Print this exact first line for every run: `think (21-jul-2026)`.

Use Codex as chair for questions of judgment, framing, priorities, or introspection. Do not use this workflow for code changes or source-backed factual research. Use `$wf` only when explicitly invoked; use `$research` when claims should be settled primarily by evidence and citations.

## Invocation

Use `$think [flags] <topic>`. Treat `/think` as `$think`.

- No flag: run independent first passes, light anonymous peer review, adversarial cross-examination, then chair synthesis.
- `--solo`: chair-only response; do not spawn members or call external peers. Record `Cross-examination: skipped:solo-no-peers`.
- `--nudge "<pushback>"`: load the newest `codex/research/think-*.md`, recover its original topic, and run a new deliberation with the pushback as additional context. Never overwrite the earlier artifact.
- `-c`: explicitly require the Claude peer. Claude is attempted by default; this flag never means another Codex instance.
- `-g`: explicitly require Gemini/Antigravity. Gemini is attempted by default; this flag never authorizes a raw Gemini, Vertex, browser, or API substitute.
- `--vault <path>`: not implemented. Ignore it with a visible note and do not read the path.

Parse flags as whole tokens so punctuation inside the topic survives. If `--nudge` has no previous Think artifact, stop with `--nudge requires a previous $think session.`

## Preflight and Run State

Before deliberating:

1. Create a unique run directory under `codex/temp/think/<UTC-run-id>/`. Make the UTC run ID collision-proof by combining a full UTC timestamp with a random suffix or UUID. Keep prompts, first passes, reviews, rebuttals, and a measured start stamp there.
2. Resolve the persona card in this order: `~/.codex/USER.md`, then `~/.claude/USER.md`. If neither exists, continue with the visible note `Persona card: none`; do not infer biography. Warn in provenance that the selected card was sent verbatim to external council members. Never read paths listed inside the card unless the user explicitly asks.
3. Resolve a Claude bridge by choosing the first executable at `$HOME/.agents/bin/claude-peer` or `./codex/bin/claude-peer`, preferring the user-local bridge. Run its `--self-test --mode research` before recommending or invoking it. It must confirm Claude.ai subscription auth, first-party routing, API-key refusal, and `liveCall=false`.
4. Discover the Gemini router. Use `mcp__agy__agy_ask` when exposed; otherwise use executable `~/.local/bin/agy-ask`. Both are transports into the repository-owned Antigravity-first, local-Gemini-fallback router.
5. Record each intended member as `available`, `unavailable`, or `not requested (--solo)` before calls. A namespace or executable check establishes availability; only a successful response establishes participation.

Do not make live preflight model calls. Do not pretend an unavailable model participated.

## Shared Council Contract

Give every first-pass member the topic, relevant `--nudge` context, persona card if present, and this contract:

```text
Wait a minute.

Name one assumption in the user's framing that you find suspect before answering.
Optimize for truth, not user approval. Do not default to agreement or praise.
If you do not know, say so. Name real trade-offs and the cost of your recommendation.
Do not infer facts about the user beyond the supplied persona card and question.

End with exactly:
## What I might be wrong about
List 2-4 specific ways this view may be miscalibrated.
```

Treat agreement as a hypothesis, not evidence. Never steer participants toward consensus.

## Independent First Passes

In default and `--nudge` modes, launch every available pass before consuming any result. Start the Codex subagent, Claude bridge, and Gemini bridge concurrently when the harness supports it; otherwise launch them back-to-back without showing one member another member's answer. This independence is load-bearing.

### Codex member: first principles and steel-man

Use a fresh subagent when subagents are available. Give it only the shared contract, persona card, topic/nudge, and this method:

```text
Reasoning method: FIRST PRINCIPLES + STEEL-MAN.
Reduce the question to mechanical primitives. State the strongest version of the
position implicit in the question. Only then answer.

Use these headings:
## Mechanical primitives
## Steel-man of the framing
## My answer
## What I might be wrong about
```

Save the response as `codex-r1.md`. If subagents are unavailable, the chair may write a separated inline pass, but mark `Codex member: inline; independence degraded`.

### Claude member: contrarian and inversion

Prepare the complete prompt in a run-directory task file; never interpolate user text into a shell command. Send it through:

```text
<bridge> --mode research --task-file <claude-task-file>
```

Supply any longer safe context through stdin. The bridge must use official `claude -p` with Claude.ai subscription/quota auth, disable tools and edits, and refuse API-key billing. Add this assigned method:

```text
Reasoning method: CONTRARIAN + INVERSION.
Assume the user's likely direction fails within six months. Trace backward to the
most plausible cause and name the earliest observable signal. Only then answer.

Use these headings:
## If this fails, here is how
## Earliest detectable signal
## My answer after inversion
## What I might be wrong about
```

Save a successful response as `claude-r1.md`. A missing bridge, failed self-test, non-zero exit, timeout, or empty output means Claude did not participate; record the exact reason and exit code when available. Do not replace Claude with an inline Codex view.

### Gemini member: expansionist and analogy

Call `mcp__agy__agy_ask` with a bounded timeout, or pass the prompt through stdin to `~/.local/bin/agy-ask -` when the MCP tool is not exposed. Add this assigned method:

```text
Reasoning method: EXPANSIONIST + ANALOGY.
Find a useful analogy in a genuinely different domain. Map it back only where the
mechanics survive; identify what does not transfer. Only then answer.

Use these headings:
## Analogous situation
## What survives the mapping
## What does not survive
## My answer through the analogy
## What I might be wrong about
```

Save a successful response as `gemini-r1.md`. If truncated, continue the same router conversation through `mcp__agy__agy_continue` or `~/.local/bin/agy-ask continue` when available. A route prefix showing Antigravity quota exhaustion and local fallback is a valid Gemini response; record the actual route rather than calling it degraded.

Never invoke raw `agy`, `gemini`, a Gemini web page, Vertex, or the Gemini API. Never substitute another model for Gemini. If both approved transports are absent or the router fails after its own fallback, record the exact failure and continue without that member.

## Normal Peer Review

Skip this phase in `--solo`. If at least two first-pass views succeeded, the Codex chair shuffles them behind `Response A/B/C`, records the private mapping, and performs a compact best-effort anonymous review. The chair may recognize style; call this anonymized, never perfectly blinded.

Rank the responses on:

1. challenge to assumptions;
2. explicit trade-offs;
3. honesty and calibration;
4. practical usefulness.

For each response, capture one strongest contribution and one weakest assumption. Do not revise member positions in this phase; cross-examination follows automatically. Save the ranking and mapping as `peer-review.md`. If fewer than two views succeeded, record `Peer review skipped: fewer than two first-pass views.`

## Cross-Examination

After independent first passes and peer review are banked, run adversarial cross-examination automatically in every default and `--nudge` run with at least two successful participants. `--solo` is the only intentional exception because it has no peers.

Record the phase outcome as exactly one of:

- `completed`: at least one round-two response succeeded;
- `skipped:solo-no-peers`: `--solo` was requested;
- `skipped:fewer-than-two-successful-participants`: degradation left fewer than two first-pass views;
- `failed:no-rebuttal-output`: at least two first passes succeeded, but every round-two response failed or was empty.

When at least two round-one participants succeeded, send each successful round-one participant its own full first pass plus a labeled, sanitized digest of every other successful round-one view. Define success as a non-empty first-pass response saved in the run directory; preflight availability alone never qualifies a member for cross-examination. Do not expose secrets, credentials, or proprietary raw text merely because one member saw it. Launch round-two calls in parallel when possible. Reuse the Codex subagent only if its first pass succeeded. Call Claude or Gemini for round two only if that same peer produced a successful round-one response, using the approved transport from round one.

Use this rebuttal contract:

```text
Independent round 1 is complete. Cross-examine the rival views; do not seek agreement.

1. Try to falsify each rival's key claims. Name unsupported, incomplete, or mistaken
   reasoning concretely. Do not manufacture objections.
2. State what a rival caught that you missed. If nothing changes, say "no revisions".
3. Restate each of YOUR key claims marked [HELD], [REVISED], or [WITHDRAWN].

Use these headings:
## Rebuttals of rivals
## Where I was wrong
## My final position
```

Save successful outputs as `<member>-r2.md`. A failed round two never erases that member's valid first pass. `[WITHDRAWN]` retracts only that participant's claim; a rival may still hold it. Opposing `[HELD]` claims are meaningful dissent, not a synthesis failure.

When cross-examination completes, the chair also self-critiques its framing and records a table with one row per successful round-one participant: counts or concise lists of HELD, REVISED, WITHDRAWN claims and the strongest rebuttal landed. Adjudicate latest valid positions by reasons and evidence, never by vote.

## Chair Synthesis

The Codex chair reads the latest valid view from each participant, the peer review, and cross-examination outputs when completed. Produce these sections in order:

1. `## Convergent view` — actual overlap only; say when none exists.
2. `## Strongest dissenting take` — name the participant and explain why the minority could be right. In `--solo`, steel-man the strongest case against the chair.
3. `## What might be wrong about the framing` — challenge a premise in how the user asked, not merely an answer detail.
4. `## Concrete next moves` — 1-3 cheap, reversible actions possible within seven days, or explicitly recommend doing nothing.
5. `## Council provenance` — participant, reasoning method, actual transport/route, success/degradation, peer-review rank, and key contribution.

If the conclusion validates the user's initial view, ensure at least one successful pass genuinely challenged it. Otherwise label the convergence weak rather than presenting theatrical consensus.

## Artifact

Choose a new artifact without clobbering existing work:

- For a normal run, propose `codex/research/think-<slug>.md` and `stat` that exact path before writing. If it exists, append the current collision-proof UTC run ID: `think-<slug>-<UTC-run-id>.md`, then `stat` the new path too.
- For a nudge, propose `codex/research/think-<original-slug>-nudge-<UTC-run-id>.md` and `stat` it before writing.
- If any run-ID-qualified target also exists, generate a fresh collision-proof UTC run ID, recompute the run directory and target, and repeat the `stat` check. Never overwrite or truncate an existing artifact.

Write the artifact at the checked-new path. Include:

```markdown
# Council deliberation: <topic>

think (21-jul-2026)
Generated: <timestamp and timezone>
Mode: <default | solo | nudge>
Council: <successful participants>
Persona card: <path | none>
Degradation: <none | exact unavailable/failed members and reasons>
Cross-examination: <completed | skipped:solo-no-peers | skipped:fewer-than-two-successful-participants | failed:no-rebuttal-output>

## Synthesis
### Convergent view
### Strongest dissenting take
### What might be wrong about the framing
### Concrete next moves
### Council provenance

## Raw first-pass views
## Peer review
## Cross-examination
## Provenance
```

Always include `## Cross-examination`. When the phase did not complete, put its exact outcome and reason there instead of a rebuttal table. In provenance, list requested and successful members separately, actual bridge routes, persona disclosure, independence level, run-directory artifact names, failures/timeouts, and measured start/end/elapsed time. Never estimate timing.

In chat, show only:

1. the required banner;
2. visible degradation and cross-examination-state notes;
3. the synthesis;
4. a clickable link to the full artifact;
5. `Deliberation written to <path>.`;
6. the measured timing receipt, or `TOTAL UNVERIFIED` if the start stamp is missing.

Do not call an opinion verified or complete. The timing receipt is the final chat line; print no text after it.
