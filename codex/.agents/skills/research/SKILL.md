---
name: research
description: Codex-native research workflow equivalent to Claude /research. Use when the user explicitly invokes $research, asks for a Codex equivalent of /research, asks to research a technical topic, compare implementation approaches, find codebase patterns, or combine local code exploration with external sources and practical recommendations.
---

# Research

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
2. Create `codex/.agents/codex/research/` if needed. Durable research belongs in `codex/.agents/codex/research/`, not hidden tool scratch.
3. Explore the codebase first:
   - Read `AGENTS.md`, `CLAUDE.md`, README files, config, tests, and related source files.
   - Use `rg` and `rg --files` before slower search tools.
   - Record concrete file paths and line numbers.
4. If `-g` is set:
   - Discover the agy bridge MCP before the research call. If `tool_search` is available, search for `mcp__agy__agy_ask`, `mcp__agy__agy_continue`, and `mcp__agy__agy_status`; otherwise use whichever callable MCP tools are already exposed in the session.
   - Call `mcp__agy__agy_ask` with a prompt asking for practical patterns, pitfalls, trade-offs, reference implementations, and source URLs. Use a bounded timeout when that argument is supported.
   - The bridge owns model selection and quota handling: it first tries Antigravity `agy`, detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`, and if free Gemini quota is exhausted automatically routes the same prompt to Vertex `gemini-3.5-flash` on project `gemini-keroga-260526-3895`, location `global`, using service account key `~/dev_local/temp/google300/vertex-key.json` unless overridden by bridge environment.
   - Treat a response prefixed `[agy quota exhausted — auto-routed to Vertex gemini-3.5-flash on project gemini-keroga-260526-3895]` as a valid Gemini research response, not as a degradation. Record the route in the output document.
   - If the response is truncated and `mcp__agy__agy_continue` is available, continue the same research conversation rather than starting over.
   - Do not replace a requested `-g` pass with Claude, Codex, or inline-only research because of perceived cost. The Vertex fallback is the intended Gemini fallback. Only degrade when the agy MCP tool is missing, errors, or times out after its own fallback path.
   - If the agy MCP tool is missing, write a visible `Gemini unavailable` degradation note. Use browser/web research only as a labeled fallback for source citations when browsing is available; do not pretend Gemini participated.
   - Cite sources in the final doc. If Gemini returns uncited claims, verify/cite them separately or label them as uncited Gemini claims.
   - If the bridge was recently updated but still behaves like the old agy-only bridge, note that the MCP host must be restarted before the new fallback code is loaded.
5. If `-c` is set:
   - Run the first executable found at `$HOME/.agents/bin/claude-peer` or `./codex/bin/claude-peer`. Prefer the user-local bridge so an untrusted checkout cannot replace it.
   - Do not interpolate user topic text into a shell command. Write the topic to `codex/.agents/codex/temp/research-topic.txt` and pass it with `--task-file`.
   - Pipe the codebase notes, relevant file excerpts, and any external source summary into:
     `<context> | <bridge> --mode research --task-file codex/.agents/codex/temp/research-topic.txt`
   - The Claude bridge must use official `claude -p` subscription/quota auth only. It must refuse API-key auth and disable Claude tools/edits.
   - If unavailable or non-zero, perform a fresh inline second pass with a clear `Claude unavailable; independence degraded` note and include the bridge exit code when present.
6. Synthesize into `codex/.agents/codex/research/<slug>.md`.

## Output Document

Use this structure:

```markdown
# Research: <topic>

Generated: <YYYY-MM-DD HH:MM>
Mode: codebase [+ Gemini/Antigravity] [+ browser fallback] [+ Claude or degraded independent implementation pass]
Degradation: <none or note>
Gemini route: <agy | Vertex fallback | unavailable | not requested>

## Executive Summary

## Codebase Patterns

## External Patterns

## Pitfalls

## Recommended Approach

## Sources
```

In chat, return a short summary and a clickable link to the research file. Do not claim source-backed certainty for uncited external claims.
