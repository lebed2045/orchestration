---
name: research
description: Codex-native research workflow equivalent to Claude /research. Use when the user explicitly invokes $research, asks for a Codex equivalent of /research, asks to research a technical topic, compare implementation approaches, find codebase patterns, or combine local code exploration with external sources and practical recommendations.
---

# Research

First response line for every run: `research (19-jun-2026)`.

Run a codebase-first research pass with optional external/source-backed research. This adapts `.claude/commands/r.md` for Codex.

## Invocation

Use as `$research [flags] <topic>`.

Flags:

- no flag: codebase research only.
- `-g`: include an Antigravity/Gemini research pass through the agy bridge MCP (`mcp__agy__agy_ask`).
- `-c`: include a Claude research pass through the local official-Claude bridge. If unavailable, do a separated second pass inline and label `Claude unavailable`.
- `-gc` or `-cg`: include both.

If the user writes `/research` in Codex, treat it as `$research`. Do not create or imply a `$r` alias in this repo.

## Clarify Scope

Ask one concise clarification only when the topic is too vague to research safely, such as a one-word topic with multiple possible meanings. Do not ask if the topic names a concrete technology, subsystem, file, bug, architecture, or includes `-g`, `-c`, or `-gc`.

## Process

1. Parse flags and slugify the topic.
2. Create `codex/research/` if needed. Durable research belongs in `codex/research/`, not hidden tool scratch.
   - Start a timing ledger so the final summary can report total wall time (recorded, never estimated); run once and remember the path:
     `RUN=$(date -u +%Y%m%dT%H%M%SZ); L="codex/temp/research/$RUN/started.txt"; mkdir -p "codex/temp/research/$RUN"; { date +%s; date '+%Y-%m-%d %H:%M:%S'; } > "$L"; echo "timing ledger: $L"`
3. Explore the codebase first:
   - Read `AGENTS.md`, `CLAUDE.md`, README files, config, tests, and related source files.
   - Use `rg` and `rg --files` before slower search tools.
   - Record concrete file paths and line numbers.
4. If `-g` is set:
   - Discover the agy bridge MCP before the research call. If `tool_search` is available, search for `mcp__agy__agy_ask`, `mcp__agy__agy_continue`, and `mcp__agy__agy_status`; otherwise use whichever callable MCP tools are already exposed in the session.
   - Call `mcp__agy__agy_ask` with a prompt asking for practical patterns, pitfalls, trade-offs, reference implementations, and source URLs. If the MCP tool is not exposed, invoke `~/.local/bin/agy-ask` with the same prompt. This is the same router's CLI transport, not a separate provider route.
   - The repository-owned bridge first tries Antigravity `agy`, then auto-routes to its configured local Gemini-compatible fallback. It reports the actual route in every response.
   - Treat a response prefixed `[agy quota exhausted — auto-routed …]` as a valid Gemini research response, not as a degradation. Record the route in the output document.
   - If the response is truncated, continue with `mcp__agy__agy_continue` or `~/.local/bin/agy-ask continue` rather than starting over.
   - Do not invoke raw `agy`, `gemini`, a browser, Vertex, or Gemini API, and do not replace a requested `-g` pass with Claude, Codex, or inline-only research. Only degrade when both bridge transports are unavailable or the bridge errors after trying its own fallback.
   - If both bridge transports are missing or the bridge fails after its internal fallback, write a visible `Gemini unavailable` degradation note. Browser/web research may still provide labeled source research, but it is never a Gemini substitute.
   - Cite sources in the final doc. If Gemini returns uncited claims, verify/cite them separately or label them as uncited Gemini claims.
   - If the bridge was recently updated but still behaves like the old agy-only bridge, note that the MCP host must be restarted before the new fallback code is loaded.
5. If `-c` is set:
   - Run the first executable found at `$HOME/.agents/bin/claude-peer` or `./codex/bin/claude-peer`. Prefer the user-local bridge so an untrusted checkout cannot replace it.
   - Do not interpolate user topic text into a shell command. Write the topic to `codex/temp/research-topic.txt` and pass it with `--task-file`.
   - Pipe the codebase notes, relevant file excerpts, and any external source summary into:
     `<context> | <bridge> --mode research --task-file codex/temp/research-topic.txt`
   - The Claude bridge must use official `claude -p` subscription/quota auth only. It must refuse API-key auth and disable Claude tools/edits.
   - If unavailable or non-zero, perform a fresh inline second pass with a clear `Claude unavailable; independence degraded` note and include the bridge exit code when present.
6. Synthesize into `codex/research/<slug>.md`.

## Output Document

Use this structure:

```markdown
# Research: <topic>

Generated: <YYYY-MM-DD HH:MM>
Mode: codebase [+ Gemini/Antigravity] [+ browser fallback] [+ Claude or degraded independent implementation pass]
Degradation: <none or note>
Gemini route: <agy | bridge fallback | unavailable | not requested>

## Executive Summary

## Codebase Patterns

## External Patterns

## Pitfalls

## Recommended Approach

## Sources
```

In chat, return a short summary and a clickable link to the research file. Do not claim source-backed certainty for uncited external claims.

## Timing Receipt (always-on, total wall time)

Append the one-line total wall time to the in-chat summary, computed from the step-2 ledger — recorded, never estimated. Append the mode in parentheses when known (mirrors the agents actually used), e.g. `⏱ research (codebase+codex) | ...`; for parallel external passes this is **total wall time, not the sum of agent durations**. If the ledger path was lost, recover the newest run (RUN ids are UTC stamps, so lexical sort = chronological); if none exists, print the `UNVERIFIED` line.

```bash
MODE="codebase"   # set to the agents actually used, e.g. "codebase+claude"; leave empty if unknown
L=$(find codex/temp/research -name started.txt -type f 2>/dev/null | sort | tail -1)
if [ -z "$L" ]; then echo "⏱ research${MODE:+ ($MODE)} | TOTAL UNVERIFIED (start stamp not found)"; else
  S=$(sed -n 1p "$L"); SH=$(sed -n 2p "$L"); E=$(date +%s); EH=$(date '+%Y-%m-%d %H:%M:%S'); T=$((E - S))
  if [ "$T" -ge 3600 ]; then H=$(printf '%dh %02dm %02ds' $((T/3600)) $((T%3600/60)) $((T%60)));
  else H=$(printf '%dm %02ds' $((T/60)) $((T%60))); fi
  printf '⏱ research%s | %s → %s | TOTAL %s\n' "${MODE:+ ($MODE)}" "$SH" "$EH" "$H"
fi
```
