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
- `-g`: include external web/current-doc research when browsing is available.
- `-c`: include a Claude research pass if a callable Claude tool is available; if not, do a separated second pass inline and label `Claude unavailable`.
- `-gc` or `-cg`: include both.

If the user writes `/research` in Codex, treat it as `$research`. Do not create or imply a `$r` alias in this repo.

## Clarify Scope

Ask one concise clarification only when the topic is too vague to research safely, such as a one-word topic with multiple possible meanings. Do not ask if the topic names a concrete technology, subsystem, file, bug, architecture, or includes `-g`, `-c`, or `-gc`.

## Process

1. Parse flags and slugify the topic.
2. Create `.codex/research/` if needed.
3. Explore the codebase first:
   - Read `AGENTS.md`, `CLAUDE.md`, README files, config, tests, and related source files.
   - Use `rg` and `rg --files` before slower search tools.
   - Record concrete file paths and line numbers.
4. If `-g` is set:
   - Browse or use official docs/current sources when external facts, recommendations, product behavior, or library details may be current.
   - Cite sources in the final doc.
   - If network or browsing is unavailable, write a visible degradation note and do not invent sources.
5. If `-c` is set:
   - Use an available Claude tool for an independent implementation-pattern view.
   - If unavailable, perform a fresh inline second pass with a clear `Claude unavailable; independence degraded` note.
6. Synthesize into `.codex/research/<slug>.md`.

## Output Document

Use this structure:

```markdown
# Research: <topic>

Generated: <YYYY-MM-DD HH:MM>
Mode: codebase [+ external] [+ Claude or degraded independent implementation pass]
Degradation: <none or note>

## Executive Summary

## Codebase Patterns

## External Patterns

## Pitfalls

## Recommended Approach

## Sources
```

In chat, return a short summary and a clickable link to the research file. Do not claim source-backed certainty for uncited external claims.
