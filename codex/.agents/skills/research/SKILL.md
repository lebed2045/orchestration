---
name: research
description: Run Codex-led, multi-agent research across the local codebase, current primary web sources, Claude, and Gemini/Antigravity, with independent parallel first passes, evidence-based disagreement adjudication, and a durable cited artifact. Use when the user invokes $research or /research, asks for substantial technical research, compares implementation approaches, investigates codebase patterns, or needs a source-backed recommendation.
---

# Research

**Updated:** `21-jul-2026`

Print `research (21-jul-2026)` as the first response line of every run.

Lead a codebase-and-evidence research process. Keep first-pass viewpoints independent, adjudicate conflicts by inspecting sources rather than voting, and save the result at a collision-safe resolved path under `codex/research/`.

## Nested peer-call guard

If the request explicitly identifies this Codex invocation as a bounded external or peer first-pass contribution inside a parent research workflow, do not start a second research run. Answer inline as one Codex pass only: do not create a run directory or artifact, do not spawn subagents, do not call Claude or Gemini/Antigravity, and do not invoke `$research` or `$think` again. Return concise findings with primary-source URLs and dates directly to the parent caller. This guard prevents research-to-research recursion; standalone `$research` behavior below is unchanged.

## Invocation and flags

Use `$research [flags] <topic>`. Treat `/research` in Codex as `$research`; do not imply a `$r` alias.

- Default: Codex lead, with Claude and Gemini/Antigravity enabled when the effort tier warrants them and their approved transports are available.
- `-c`: explicitly request Claude. Preserve this Codex convention; here `c` means the other main model.
- `-g`: explicitly request Gemini/Antigravity.
- `-cg` / `-gc`: explicitly request both.
- `--no-claude`: disable Claude.
- `--no-agy` or `--no-gemini`: disable Gemini/Antigravity.

Explicit enable flags override effort-tier skips for that named external. Explicit opt-outs override enables if both appear; report the conflict and honor the opt-out. Strip only whole-token flags so punctuation and glob characters in the topic survive.

Ask at most one concise clarification only when the topic is genuinely ambiguous or the answer would materially change the research boundary. Otherwise proceed.

## Effort scaling

Choose the cheapest tier that can answer honestly:

| Question | Run |
|---|---|
| Simple fact or familiar narrow code question | Inline codebase/source check; skip subagents and default external consults unless explicitly enabled |
| Comparison or one unfamiliar area | Codex codebase + web pass; use 1-2 research subagents when the work decomposes; fire enabled externals when they add independent evidence |
| Consequential decision, unfamiliar domain, contested claim, or repo architecture | Full run: independent codebase threads, current web research, and every enabled external |

## Phase 0: start the run

1. Parse flags, retain the exact topic, and create a filesystem-safe slug. If the slug is empty, use a short deterministic fallback.
2. Create a collision-proof run directory under `codex/temp/research/`; use its basename as the current run ID. Record epoch plus human-readable local start time in `started.txt`. Use this ledger for measured wall time; never estimate.
3. Run `stat` on the candidate `codex/research/<slug>.md` before reserving it. If it exists, resolve the output to `codex/research/<slug>-<run-id>.md`, using the collision-proof current run ID, and `stat` that resolved candidate too before creating it. Never overwrite an existing research artifact. Persist the final resolved output path for all later writes and reporting. Scratch notes stay in the run directory.
4. Create `externals.txt`. Record one row for every enabled, disabled, skipped, successful, or failed Claude/Gemini attempt, with a short reason. The final receipt must be derived from this ledger, not memory.

## Phase 1: independent first passes

Run independent work concurrently when tooling permits. Do not feed one first-pass researcher another's findings or draft conclusion.

### Codex lead: codebase and web evidence

- Read applicable `AGENTS.md`, `CLAUDE.md`, README/config, implementation, and tests.
- Use `rg` and `rg --files` first. Cite local findings as clickable `path:line` references in chat and as `path:line` in the artifact.
- For time-sensitive, unfamiliar, externally sourced, or source-requested claims, browse. Prefer official docs, source repositories, standards, papers, and first-party engineering material. Record direct URLs and relevant publication/update dates.
- Go broad enough to find competing approaches, then narrow to primary sources that can adjudicate the decision.

For a broad sweep with genuinely independent threads, spawn research subagents when subagents are available. Give each a delegation contract containing: objective, output format, allowed tools/sources, exact boundary, and a requirement to cite evidence. Use separate threads such as codebase architecture, tests/constraints, or external prior art. Do not spawn for a narrow fact. If subagents are unavailable, perform separated passes inline and record `subagents unavailable; independence reduced`.

### External decision brief

Give Claude and Gemini only a short sanitized brief:

```text
DECISION BRIEF
- Question: <decision this research informs>
- Stack: <languages/frameworks>
- Hard constraints: <1-3 lines>
- Out of scope: <boundary>
```

Do not include secrets, proprietary source, Codex's findings, or conclusions. Ask each external for practical architecture patterns, pitfalls, trade-offs, real implementations, and a direct source URL plus publication/update date for every key external claim.

### Claude pass

Use the first executable bridge found at `$HOME/.agents/bin/claude-peer` or `codex/bin/claude-peer`, preferring the user-local bridge. Pass untrusted topic/context through files or stdin, never shell interpolation. Use `--mode research --task-file <run-dir>/topic.txt`.

The bridge must use official `claude -p` with Claude.ai subscription/quota auth, refuse API-key billing, and disable tools/edits. If the bridge is missing or exits non-zero, continue and log `claude fail <reason>`; do not simulate Claude with an inline Codex answer.

### Gemini/Antigravity pass

Use `mcp__agy__agy_ask`. If that MCP tool is not exposed, use `~/.local/bin/agy-ask`; these are two transports to the same Antigravity-first, local-Gemini-fallback router. Continue truncated responses through the matching bridge continuation mechanism.

Never call `agy`, `gemini`, a Gemini web page, Vertex, or the Gemini API directly. A router-reported local fallback is a valid Gemini pass; record its actual route. If both approved transports are unavailable or the router fails after its fallback, continue and log `gemini fail <reason>`; do not replace it with Claude or Codex.

## Phase 2: evidence normalization

Before synthesis:

1. Reduce each pass to discrete claims with author, evidence, scope, and uncertainty.
2. Open the cited primary source for every recommendation-critical external claim. Do not treat an external's URL list as verified merely because it looks plausible.
3. Verify codebase claims directly against current files. Externals cannot independently prove local-code claims they were not shown.
4. Label claims as `verified`, `partially verified`, `uncited`, or `unresolved`.
5. Treat model agreement as correlated opinion, not evidence. Promote a claim only on source quality and applicability.

After the independent passes, adjudicate disagreement by reading the underlying code or primary source. Never resolve by majority. Record an unresolved split when the evidence cannot settle competing positions. End the researcher interaction after the first passes; peer-critique rounds belong to `$think`.

## Phase 3: durable synthesis

Write the durable artifact to the resolved output path selected in Phase 0, with this structure:

```markdown
# Research: <topic>

Generated: <timestamp>
Mode: <actual participants and effort tier>
Degradation: <none or exact missing/skipped capability>

## Question and Scope
## Assumptions
## Executive Summary
## Codebase Patterns
## External Evidence and Reference Implementations
## Pitfalls and Trade-offs
## Disagreements and Adjudication
## Uncertainty and Unresolved Questions
## Recommended Approach
## Sources
```

In multi-viewpoint runs, make `Disagreements and Adjudication` a table with each position, its evidence, the adjudicating source, and the verdict. Preserve unresolved positions as provenance.

Separate sources into codebase files, primary web sources, secondary sources, and agent contributions. Do not claim source-backed certainty for unverified or uncited model claims.

## Phase 4: report

Return a compact summary containing:

- the key finding and recommended direction;
- actual participants, source counts, and disagreement/unresolved counts;
- a clickable absolute link to the resolved durable artifact path;
- one measured timing line and one external-call receipt.

Use `research` as the receipt producer. Report total wall time from `started.txt`; for parallel work, this is elapsed wall time, not summed agent time. If the ledger is missing or invalid, print `TOTAL UNVERIFIED (start stamp not found)`.

Summarize `externals.txt` on exactly one line, including success/failure counts, disabled flags, tier skips, and the actual Gemini route when known. Missing transports and failed calls are degradations, not reasons to abort the useful parts of the run. Never silently substitute one model for another.
