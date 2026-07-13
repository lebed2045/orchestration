---
name: think
description: Codex-native deliberation workflow equivalent to Claude /think. Use when the user explicitly invokes $think, asks for a council-style opinion, wants pushback on framing, asks "what do you think", needs a decision critique, or wants non-factual introspective analysis with dissent, tradeoffs, and concrete next moves.
---

# Think

First response line for every run: `think (19-jun-2026)`.

This is a Codex-native adaptation of `.claude/commands/think.md`. Use it for opinion, judgment, framing critique, or decisions without a single objective test. Do not use it for code changes (`$wf` exists for those, but only on explicit invocation), or source-backed factual research that should run through `$research`.

## Invocation

Use as `$think [flags] <topic>`.

Flags:

- no flag: run a three-perspective council when possible.
- `--solo`: one Codex pass only, no peer review.
- `-g`: require the Antigravity/Gemini council member through the agy bridge MCP when available; otherwise include a visible degradation note. In default mode, use Gemini for the expansionist/analogy pass when the tool is loaded.
- `--nudge "<pushback>"`: re-open the most recent `codex/research/think-*.md` and deliberate again with the added pushback.
- `--vault <path>`: not implemented; ignore with a visible note.

If the user writes `/think`, treat it as `$think`.

## Preconditions

- Do not pretend unavailable models or tools participated.
- Prefer true independent subagents when available. If none are available, run separated inline passes and explicitly label them as not independently isolated.
- If a persona card exists at `~/.codex/USER.md`, read it. If not, fall back to `~/.claude/USER.md` only if accessible. If neither exists, continue without a persona card and say so.
- Do not browse unless the topic needs current facts; this workflow is primarily judgment, not research.
- For Gemini/Antigravity participation, discover the agy bridge MCP before deliberation. If `tool_search` is available, search for `mcp__agy__agy_ask`, `mcp__agy__agy_continue`, and `mcp__agy__agy_status`; otherwise use whichever callable MCP tools are already exposed in the session.
- Call `mcp__agy__agy_ask`, or invoke `~/.local/bin/agy-ask` with the same prompt when the MCP tool is not exposed. These are two transports into the same router.
- The repository-owned agy bridge first tries Antigravity `agy`, then auto-routes to its configured local Gemini-compatible fallback. It reports the actual route in every response.
- Treat a response prefixed `[agy quota exhausted — auto-routed …]` as a valid Gemini council response, not as a degradation. Record the route in council provenance.
- If a Gemini response is truncated and `mcp__agy__agy_continue` is available, continue the same council-member conversation rather than starting a replacement pass.
- Do not invoke raw `agy`, `gemini`, a browser, Vertex, or Gemini API, and do not replace requested Gemini participation with Claude, Codex, or another inline pass. Only degrade when both bridge transports are unavailable or the bridge errors after trying its own fallback.
- If the bridge was recently updated but still behaves like the old agy-only bridge, note that the MCP host must be restarted before the new fallback code is loaded.

## Council Passes

For default mode, produce these perspectives:

1. First principles + steel-man:
   - Name one suspect assumption in the user's framing.
   - Reduce the question to mechanical primitives.
   - Steel-man the user's likely position.
   - Answer.

2. Contrarian + inversion:
   - Assume the user's likely path fails in six months.
   - Trace backward to the failure mode and earliest signal.
   - Answer from that inversion.

3. Expansionist + analogy:
   - Prefer `mcp__agy__agy_ask`; use `~/.local/bin/agy-ask` when the MCP tool is not exposed.
   - Pick a genuinely different domain.
   - Map only the parts that survive mechanical scrutiny.
   - Drop the parts that do not transfer.
   - Answer from the surviving analogy.

Each pass must end with `## What I might be wrong about` containing 2-4 specific calibration risks.

## Synthesis

Write `codex/research/think-<slug>.md` with:

```markdown
# Council deliberation: <topic>

think (19-jun-2026)
Generated: <YYYY-MM-DD HH:MM>
Mode: <default | --solo | --nudge>
Independence: <true subagents | inline separated passes | solo>
Persona card: <path | none>
Gemini route: <agy | bridge fallback | unavailable | not requested>

## Synthesis

### Convergent view

### Strongest dissenting take

### What might be wrong about the framing

### Concrete next moves

### Council provenance

## Raw perspectives
```

In chat, show only the banner, any degradation note, the synthesis, and a clickable link to the full deliberation file. Avoid completion language; use `Deliberation written to ...`.
