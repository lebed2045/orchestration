# /research - Evidence Research

**Updated:** `24-jul-2026`

**Help banner.** Unless the invoking command already printed one (the `/r` wrapper prints its own), print exactly this line first:

`/research — evidence research: single-agent Claude by default; -c adds Codex, -g adds Antigravity, --multi-agent enables Explore fan-out (/r for short).`

Research a topic using codebase exploration + optional external research (Codex MCP / agy bridge MCP).

**Philosophy**: *"Stand on shoulders of giants, don't reinvent the bicycle."*

---

## Usage

```bash
/research <topic>                       # Claude lead only: codebase + web when warranted
/research -c <topic>                    # Add one bounded Codex first pass
/research -g <topic>                    # Add one bounded Antigravity first pass
/research -cg <topic>                   # Add both bounded external first passes
/research --multi-agent <topic>         # Explicitly permit Explore subagent fan-out
/research -cg --multi-agent <topic>     # Full opt-in fan-out
```

External reviewers and Explore subagents are OFF by default. `-c`, `-g`, `-gc`/`-cg`, and `--multi-agent` are explicit opt-ins. `--no-codex` and `--no-agy` remain accepted as explicit overrides for composed aliases or saved invocations. Missing/broken MCPs never interrupt the run (see Phase 2: silent degradation); the only place they surface is the one-line externals receipt in Phase 5.

---

## Flag Detection

```bash
AGY=false                    # Explicitly enabled by -g / -gc / -cg
CODEX=false                  # Explicitly enabled by -c / -gc / -cg
MULTI_AGENT=false            # Explicitly enabled by --multi-agent
TOPIC="$ARGUMENTS"

# Token-aware flag parse — whole words only, so topics like "e-commerce" or "g-code"
# survive intact, and no globbing (set -f) so "*" in a topic never expands to filenames.
set -f; set -- $TOPIC; set +f
TOPIC=""
for w in "$@"; do
  case "$w" in
    -g)            AGY=true ;;
    -c)            CODEX=true ;;
    -gc|-cg)       AGY=true; CODEX=true ;;
    --multi-agent) MULTI_AGENT=true ;;
    --no-codex)    CODEX=false ;;
    --no-agy)      AGY=false ;;
    *)             TOPIC="${TOPIC:+$TOPIC }$w" ;;
  esac
done

# Generate filename from topic
FILENAME=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')

echo "TOPIC: $TOPIC"
echo "AGY (agy bridge MCP): $AGY"
echo "CODEX: $CODEX"
echo "MULTI_AGENT: $MULTI_AGENT"

# Timing ledger (always-on). Total wall time is computed from this file in Phase 5; never estimated.
R_RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)                  # UTC stamp; lexical sort == chronological
mkdir -p .claude/temp/research
R_DIR=$(mktemp -d ".claude/temp/research/${R_RUN_ID}-XXXX")  # run-scoped intermediates — never /tmp; mktemp is collision-proof even same-second
R_LEDGER="$R_DIR/started.txt"
{ date +%s; date '+%Y-%m-%d %H:%M:%S'; } > "$R_LEDGER"   # line 1 = epoch, line 2 = human start
OUTPUT=".claude/research/${FILENAME}.md"
while stat "$OUTPUT" >/dev/null 2>&1; do
  # The current proposal exists. Generate a fresh collision-proof run ID, then loop so
  # stat explicitly probes the fallback proposal too before it can be selected.
  R_COLLISION_RUN_DIR=$(mktemp -d "$R_DIR/artifact-XXXX")
  R_COLLISION_RUN_ID="$(basename "$R_DIR")-$(basename "$R_COLLISION_RUN_DIR")"
  OUTPUT=".claude/research/${FILENAME}-${R_COLLISION_RUN_ID}.md"
done
echo "OUTPUT: $OUTPUT"
echo "timing ledger: $R_LEDGER"
```

---

## Effort Scaling

Scale the run to the question — fan-out is expensive (multi-agent research burns an order of magnitude more tokens than a single pass; Anthropic's research-system numbers, not a universal law):

| Question shape | Effort |
|---|---|
| Simple fact / familiar domain | Inline Claude codebase pass only; no WebSearch unless freshness requires it |
| Comparison / one unfamiliar area | Claude codebase pass + WebSearch |
| Consequential decision / unfamiliar domain / repo-specific architecture | Deeper Claude codebase + WebSearch; only explicitly enabled externals fire |

**External precedence:** `-c` and `-g` request their named external even for a simple topic. `--no-codex` and `--no-agy` disable a previously enabled reviewer; when conflicting flags appear, the last whole-token flag wins.

**Subagent gate:** do not use the Agent tool or spawn any Explore subagent unless `MULTI_AGENT=true`. When explicitly enabled, every subagent gets a delegation contract: objective, output format, tools/sources, and task boundary. Parallelize only genuinely independent threads.

---

## Phase 0: TOPIC_CLARIFICATION (If Needed)

**Before researching, evaluate if the topic is clear enough.**

### When to Ask Clarifying Questions

Ask if ANY of these are true:
- Topic is 1-2 generic words (e.g., "why", "how", "auth")
- Topic could mean multiple things
- Scope is unclear (codebase-specific vs general best practices?)
- Domain is ambiguous

### How to Clarify

Use `AskUserQuestion` tool with targeted questions:

```markdown
Your research topic "[TOPIC]" could go several directions. Help me focus:

**Questions:**
1. What specifically do you want to understand?
   - [ ] How this is done in our codebase
   - [ ] Best practices from industry
   - [ ] Both

2. What's the context?
   - [ ] Planning a new feature
   - [ ] Understanding existing code
   - [ ] Learning/exploration

3. Any specific aspects to focus on?
   [Free text]
```

### When NOT to Ask

Skip clarification if:
- Topic is 3+ specific words (e.g., "game bastion defense patterns")
- Topic mentions specific technology (e.g., "React authentication flow")
- User included flags (`-g`, `-c`, `-gc`/`-cg`, `--multi-agent`, `--no-codex`, or `--no-agy`) indicating they know what they want

**After clarification, proceed to Phase 1.**

---

## Research Goals

| Agent | Researches | Focus |
|-------|------------|-------|
| **Claude (lead)** | Codebase | Existing patterns, conventions, constraints |
| **Antigravity (agy bridge MCP)** | Internet | Best practices, architecture patterns, pitfalls |
| **Codex** | Internet | Real-world implementations, common mistakes, expert approaches |

**Combined goal**: Learn how experts build this feature/architecture, then map to our codebase.

**Independence rule (anti-anchoring, anti-groupthink):** Phase 1 and Phase 2 run in PARALLEL, and the external agents' first pass gets the decision brief only — never Claude's codebase findings or draft conclusions. Cross-model agreement is NOT evidence (models share correlated training data); it's the *disagreements* that carry information, and they get adjudicated with sources in Phase 4.

---

## Phase 1: CODEBASE_RESEARCH (Claude lead — Always Runs)

Research existing patterns in the codebase inline. If and only if `MULTI_AGENT=true`, a broad sweep may spawn parallel Explore subagents, each with a delegation contract (objective, output format, tools, boundary). Otherwise the Claude lead performs the complete pass itself.

### Search Strategy

```bash
# Find related files
glob "**/*[keyword]*"

# Find similar implementations
grep "[keyword]" --type ts

# Find tests
glob "**/*.test.*"

# Check CLAUDE.md for constraints
cat CLAUDE.md | grep -i "[keyword]"
```

### Capture to run dir

```bash
echo "# Codebase Research: $TOPIC" > "$R_DIR/codebase.md"
```

After exploration, append findings to `$R_DIR/codebase.md`:
- File paths with line numbers
- Code snippets showing patterns
- Constraints from CLAUDE.md
- Current conventions

---

## Phase 2: EXTERNAL_RESEARCH (Opt-in — runs in PARALLEL with Phase 1)

Only explicitly enabled external consults launch. When both are enabled, launch them together in the same turn, concurrent with Phase 1 and with each other.

### Silent degradation + call ledger

A missing or broken external NEVER interrupts the run and never produces mid-run warnings — the run just continues without it. Every attempt appends one space-separated row to `$R_DIR/externals.txt` (`<codex|gemini> <ok|fail|skipped|off> <short note>`); this ledger is the sole source for the Phase 5 one-liner, the only place failures surface:

Every call row starts with the agent name so the Phase 5 receipt can count it with `^codex ` / `^gemini `.

- Successful call → `codex ok -` / `gemini ok -` (one row per call).
- Codex tool not loaded (ToolSearch `select:mcp__codex-cli__codex` comes back empty) → `codex fail MCP missing`, continue.
- AGY MCP not loaded → try `~/.local/bin/agy-ask`; if that's dead too → `gemini fail bridge unreachable`, continue.
- Call errors or times out mid-run → `codex fail <short reason>` / `gemini fail <short reason>`, continue.
- Not requested → `codex off not requested` / `gemini off not requested`.
- Explicitly disabled after being enabled → `codex off --no-codex` / `gemini off --no-agy`.

### Decision brief (both external agents get this, and only this)

Build a short sanitized brief — the external agents need enough context to give fitting answers, but no anchoring material and no secrets:

```text
DECISION BRIEF
- Question: [TOPIC — what decision this research feeds]
- Stack: [languages/frameworks, 1 line]
- Hard constraints: [e.g. no new deps, single-threaded, offline — 1-3 lines]
- Out of scope: [what NOT to research]
- Execution contract: This is one bounded first-pass contribution inside a parent `/research` run. Answer inline in this call only. Do not invoke `/research`, `$research`, `/think`, or any other skill/workflow; do not spawn or delegate to agents; do not consult another model; do not create files.
```

Include NO proprietary code, credentials, or Claude's own findings/hypotheses. First pass must be independent.

### If AGY=true (Antigravity via the `agy` bridge MCP)

**Preflight:** confirm the bridge tool is loaded: `ToolSearch({query: "select:mcp__agy__agy_ask,mcp__agy__agy_continue,mcp__agy__agy_status", max_results: 3})`. If it is missing, invoke `~/.local/bin/agy-ask` with the same prompt. This is the bridge's CLI transport, not a different Gemini route.

Call the `mcp__agy__agy_ask` MCP tool, or `~/.local/bin/agy-ask` only when the tool is not exposed. The repository-owned bridge tries AGY first, then the configured local Gemini-compatible fallback, and prefixes the response with the actual route. Treat either route as valid Gemini research, not a downgrade. Never call raw `agy`, `gemini`, a browser, Vertex, or Gemini API instead. If the response is truncated, use `mcp__agy__agy_continue` or `~/.local/bin/agy-ask continue`. Restart Claude Code after bridge updates.

```text
mcp__agy__agy_ask  prompt="
Research best practices for: [TOPIC]

[DECISION BRIEF]

You are a bounded external reviewer inside a parent research run. Follow the execution contract above.

I'm building this in a software project. Research:

1. **Architecture patterns**: How do experts design this? What's the recommended structure?
2. **Best practices**: What are the proven approaches? What do popular frameworks do?
3. **Common pitfalls**: What mistakes do people make? What should I avoid?
4. **Real examples**: Reference implementations, open-source projects that do this well.
5. **Trade-offs**: What are the pros/cons of different approaches?

Focus on practical, actionable insights. I want to learn from those who've already solved this.
Cite a URL and publish date for every key claim — uncited claims can't be adjudicated.

Output format:
## Expert Approaches
[How experts build this]

## Best Practices
[Proven patterns]

## Pitfalls to Avoid
[Common mistakes]

## Reference Implementations
[Projects/repos that do this well]

## Trade-offs
[Pros/cons of approaches]
"
```

Typical latency 30–60s per call. Save the tool's returned text to `$R_DIR/agy.md`.

### If CODEX=true

Call `mcp__codex-cli__codex`:

```text
Research real-world implementations of: [TOPIC]

[DECISION BRIEF]

You are a bounded external reviewer inside a parent research run. Follow the execution contract above.

Search for:
1. How is this typically implemented in production systems?
2. What are common architectural patterns?
3. What pitfalls do developers encounter?
4. What are the best open-source examples?
5. What do experts recommend?

Focus on practical code patterns and real implementations.
I want to stand on shoulders of giants, not reinvent the wheel.
Cite a URL and publish date for every key claim — uncited claims can't be adjudicated.

Output format:
## Implementation Patterns
[How this is typically built]

## Code Examples
[Patterns from real projects]

## Common Mistakes
[What to avoid]

## Recommended Libraries/Tools
[What experts use]

## Expert Recommendations
[Advice from experienced developers]
```

Save to `$R_DIR/codex.md`

---

## Phase 3: WEB_SEARCH (Claude lead — all tiers except simple/familiar)

Skipped only in the simple-fact tier of the Effort Scaling table; runs on every other tier. Use WebSearch to find additional context:

```text
Search: "[TOPIC] best practices architecture 2026"
Search: "[TOPIC] common mistakes pitfalls"
Search: "[TOPIC] implementation patterns"
```

**Source quality:** go broad → narrow; prefer primary sources (official docs, source repos, papers, first-party engineering blogs) over SEO aggregators; note publish dates on anything fast-moving. Extract key insights and add to consolidation.

---

## Phase 4: CONSOLIDATE (Claude lead)

Merge all research into a single document. Where sources or models disagree, adjudicate with evidence — never by vote, and never assume agreement settles it.

```bash
mkdir -p .claude/research
```

Write to `$OUTPUT` (the canonical topic path when unused; otherwise the run-tagged no-clobber path selected during setup):

```markdown
# Research: [TOPIC]

Generated: [YYYY-MM-DD HH:MM]
Agents: Claude [+ Antigravity (agy bridge MCP)] [+ Codex]

---

## Question & Scope

[The decision this research feeds; what's in scope, what's explicitly out]

## Assumptions

[What was taken as given without verification]

---

## Executive Summary

[2-3 sentences: Key finding and recommended approach]

---

## Codebase Patterns (How We Do It)

### Existing Implementations
[Patterns found in our codebase with file paths]

### Current Conventions
[Style and architecture we already use]

### Constraints
[Rules from CLAUDE.md and project config]

---

## Expert Approaches (How Giants Do It)

### Architecture Patterns
[From Antigravity/Codex research]

### Best Practices
[Proven approaches]

### Reference Implementations
[Open-source projects, repos]

---

## Pitfalls to Avoid

### Common Mistakes
[What others got wrong]

### Our Specific Risks
[Based on our codebase]

---

## Disagreements & Adjudication

[Only in multi-agent runs. One row per conflict — agreement is not evidence, disagreement is signal:]

| Claim | Claude | Antigravity | Codex | Adjudicating source | Verdict |
|---|---|---|---|---|---|

## Uncertainty & Unresolved Questions

[Claims that couldn't be verified; open questions the user should know remain open]

---

## Recommended Approach

[Synthesis: Combine expert knowledge with our codebase patterns]

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Sources

### Codebase Files
- [file:line] - [what was found]

### Web Sources
- [URL] - [key insight]

### Agent Contributions
- Claude: Codebase exploration
- Antigravity (agy bridge MCP): [if used]
- Codex: [if used]
```

---

## Phase 5: OUTPUT

### Write the Research Document

Save consolidated research to `$OUTPUT`. Never overwrite an existing research artifact; setup chooses a run-tagged path when the canonical topic path already exists.

### Show Summary to User

**CRITICAL: Output must include CLICKABLE link using markdown format.**

Output this EXACT format (substitute actual values):

```markdown
## Research Complete: [TOPIC]

| Metric | Value |
|--------|-------|
| Agents | Claude [+ Antigravity] [+ Codex] |
| Codebase files | [N] analyzed |
| Web sources | [N] referenced ([N] primary) |
| Patterns found | [N] |
| Pitfalls found | [N] |
| Disagreements adjudicated | [N] ([N] unresolved) |

### Key Finding

[1-2 sentence summary of most important insight]

### Summary

| Section | Key Points |
|---------|------------|
| **Codebase** | [What we already have] |
| **Expert** | [What giants recommend] |
| **Pitfalls** | [What to avoid] |
| **Approach** | [Recommended path forward] |

### Full Document

**Click to open**: [<actual output filename>](<actual `$OUTPUT` path>)
```

### Timing receipt (always-on, total wall time)

After the metric table, compute the total from the setup ledger (`R_LEDGER`) and print the one-line receipt. If the path was lost, recover the newest run (RUN_IDs are UTC stamps, so lexical sort = chronological); if no ledger exists, print the `UNVERIFIED` line — never estimate. Append the mode in parentheses when known (mirrors the agents actually used), e.g. `⏱ research (codebase+codex) | ...`. For parallel external fan-out this is **total wall time, not the sum of agent durations**.

```bash
LEDGER="$R_LEDGER"
[ -f "$LEDGER" ] || LEDGER=$(find .claude/temp/research -name started.txt -type f 2>/dev/null | sort | tail -1)
MODE="codebase"   # set to the agents actually used, e.g. "codebase+agy+codex"; leave empty if unknown
if [ -z "$LEDGER" ] || [ ! -f "$LEDGER" ]; then
  echo "⏱ research${MODE:+ ($MODE)} | TOTAL UNVERIFIED (start stamp not found)"
else
  S=$(sed -n 1p "$LEDGER"); SH=$(sed -n 2p "$LEDGER")
  E=$(date +%s); EH=$(date '+%Y-%m-%d %H:%M:%S'); T=$((E - S))
  if [ "$T" -ge 3600 ]; then H=$(printf '%dh %02dm %02ds' $((T/3600)) $((T%3600/60)) $((T%60)));
  else H=$(printf '%dm %02ds' $((T/60)) $((T%60))); fi
  echo "⏱ research${MODE:+ ($MODE)} | $SH → $EH | TOTAL $H"
fi
```

### Externals receipt (always-on, ONE line)

Directly under the timing receipt, print exactly ONE line — successful call counts per external plus a short error in parentheses when the success count is zero. Never more than one line, never a table:

```bash
EXT="$R_DIR/externals.txt"
OUT=""
for a in codex gemini; do
  n=$(grep -c "^$a ok" "$EXT" 2>/dev/null); n=${n:-0}
  f=$(grep -c "^$a fail" "$EXT" 2>/dev/null); f=${f:-0}
  if [ "$n" -gt 0 ]; then S="$a $n"; [ "$f" -gt 0 ] && S="$S, $f fail"
  else NOTE=$(grep -m1 "^$a " "$EXT" 2>/dev/null | cut -d' ' -f3-); S="$a 0 (${NOTE:-not attempted})"; fi
  OUT="${OUT:+$OUT · }$S"
done
echo "🔌 research externals: $OUT"
```

Examples: `🔌 research externals: codex 0 (not requested) · gemini 0 (not requested)` · `🔌 research externals: codex 1 · gemini 0 (not requested)` · `🔌 research externals: codex 0 (MCP missing) · gemini 1`

Like the `⏱` line, the receipt names its producing skill (`research`) — receipts must be attributable when they land in a longer transcript.

**IMPORTANT**: The link MUST be in markdown format `[text](path)` to be clickable in VSCode.

Example output:
```markdown
**Click to open**: [game-bastion-design.md](.claude/research/game-bastion-design.md)
```

---

## Examples

### Default (Single-Agent)

```
/research authentication flow
```
→ Claude codebase + web research when warranted; no external reviewers or Explore subagents
→ Output: `.claude/research/authentication-flow.md`

### Explicit Full Fan-out

```
/research -cg --multi-agent microservices architecture
```
→ Claude + bounded Antigravity + bounded Codex first passes; Explore fan-out permitted
→ Output: `.claude/research/microservices-architecture.md`

---

## When to Use Each Mode

| Mode | Use When |
|------|----------|
| Default (no flags) | Single-agent Claude research with codebase/web depth scaled to the topic |
| `-c` / `-g` | Add one bounded independent external first pass |
| `-gc` / `-cg` | Add both bounded external first passes |
| `--multi-agent` | Explicitly permit Explore subagent fan-out for a decomposable sweep |

For low-stakes questions, plain conversation (no `/research`) is fine. `/research` earns its cost on consequential, unfamiliar, or repo-specific decisions — where cross-model triangulation and the persistent artifact matter.

---

## Integration with Workflows

After research, you can:
1. **Read the doc** and decide approach manually
2. **Distill** key insights into CLAUDE.md rules when they should become permanent workflow rules
3. **Feed to workflow**: `/workflow <task>` (or `/wf`) and reference the research

Research docs are Claude command outputs under `.claude/research/` like before. Scratch notes belong under `.claude/temp/`.

---

## User's Topic

$ARGUMENTS
