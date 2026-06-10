# /research - Multi-Agent Research

Research a topic using codebase exploration + optional external research (Codex MCP / agy bridge MCP).

**Philosophy**: *"Stand on shoulders of giants, don't reinvent the bicycle."*

---

## Usage

```bash
/research <topic>           # Opus only (codebase patterns)
/research -g <topic>        # Opus + Antigravity via agy bridge MCP (`mcp__agy__agy_ask`)
/research -c <topic>        # Opus + Codex MCP
/research -gc <topic>       # Opus + Antigravity + Codex (full research)
/research -cg <topic>       # Same as -gc
```

---

## Flag Detection

```bash
AGY=false                    # `-g` flag: Antigravity via agy bridge MCP (`mcp__agy__agy_ask`)
CODEX=false
TOPIC="$ARGUMENTS"

# Parse flags
if [[ "$ARGUMENTS" == *"-gc"* ]] || [[ "$ARGUMENTS" == *"-cg"* ]]; then
  AGY=true
  CODEX=true
  TOPIC="${ARGUMENTS//-gc/}"
  TOPIC="${TOPIC//-cg/}"
elif [[ "$ARGUMENTS" == *"-g"* ]]; then
  AGY=true
  TOPIC="${ARGUMENTS//-g/}"
elif [[ "$ARGUMENTS" == *"-c"* ]]; then
  CODEX=true
  TOPIC="${ARGUMENTS//-c/}"
fi

TOPIC="${TOPIC## }"  # trim leading space
TOPIC="${TOPIC%% }"  # trim trailing space

# Generate filename from topic
FILENAME=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')

echo "TOPIC: $TOPIC"
echo "AGY (agy bridge MCP): $AGY"
echo "CODEX: $CODEX"
echo "OUTPUT: .claude/research/${FILENAME}.md"
```

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
- User included flags (`-g`, `-c`, `-gc`) indicating they know what they want

**After clarification, proceed to Phase 1.**

---

## Research Goals

| Agent | Researches | Focus |
|-------|------------|-------|
| **Opus** | Codebase | Existing patterns, conventions, constraints |
| **Antigravity (agy bridge MCP)** | Internet | Best practices, architecture patterns, pitfalls |
| **Codex** | Internet | Real-world implementations, common mistakes, expert approaches |

**Combined goal**: Learn how experts build this feature/architecture, then map to our codebase.

---

## Phase 1: CODEBASE_RESEARCH (Opus — Always Runs)

Research existing patterns in the codebase.

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

### Capture to temp file

```bash
mkdir -p research
echo "# Codebase Research: $TOPIC" > /tmp/opus-research.md
echo "" >> /tmp/opus-research.md
echo "## Existing Patterns" >> /tmp/opus-research.md
```

After exploration, append findings to `/tmp/opus-research.md`:
- File paths with line numbers
- Code snippets showing patterns
- Constraints from CLAUDE.md
- Current conventions

---

## Phase 2: EXTERNAL_RESEARCH (Conditional)

### If AGY=true (Antigravity via the `agy` bridge MCP)

**Preflight:** confirm the bridge tool is loaded: `ToolSearch({query: "select:mcp__agy__agy_ask,mcp__agy__agy_continue,mcp__agy__agy_status", max_results: 3})`. If missing, skip this phase and warn (register the bridge once with `claude mcp add agy -- ~/.claude/mcp-servers/agy-bridge/.venv/bin/python ~/.claude/mcp-servers/agy-bridge/server.py`, then restart Claude Code).

Call the `mcp__agy__agy_ask` MCP tool (Gemini 3.5 Flash via the agy bridge — it returns the model's final answer directly; no stdout parsing). The bridge detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`; if free Gemini quota is exhausted, it automatically routes the same prompt to Vertex `gemini-3.5-flash` on project `gemini-keroga-260526-3895`, location `global`, using service account key `~/dev_local/temp/google300/vertex-key.json` unless overridden by environment. Treat a response prefixed `[agy quota exhausted — auto-routed to Vertex gemini-3.5-flash on project gemini-keroga-260526-3895]` as valid Gemini research, not a downgrade. Do not substitute Codex/self-research because Vertex credits would be used; Vertex is the intended Gemini fallback. If the response is truncated and `mcp__agy__agy_continue` is available, continue the same research conversation. If the bridge was updated but still behaves like the old agy-only bridge, restart Claude Code so the MCP server reloads.

```text
mcp__agy__agy_ask  prompt="
Research best practices for: [TOPIC]

I'm building this in a software project. Research:

1. **Architecture patterns**: How do experts design this? What's the recommended structure?
2. **Best practices**: What are the proven approaches? What do popular frameworks do?
3. **Common pitfalls**: What mistakes do people make? What should I avoid?
4. **Real examples**: Reference implementations, open-source projects that do this well.
5. **Trade-offs**: What are the pros/cons of different approaches?

Focus on practical, actionable insights. I want to learn from those who've already solved this.

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

Typical latency 30–60s per call. Save the tool's returned text to `/tmp/agy-research.md`.

### If CODEX=true

Call `mcp__codex-cli__codex`:

```text
Research real-world implementations of: [TOPIC]

Search for:
1. How is this typically implemented in production systems?
2. What are common architectural patterns?
3. What pitfalls do developers encounter?
4. What are the best open-source examples?
5. What do experts recommend?

Focus on practical code patterns and real implementations.
I want to stand on shoulders of giants, not reinvent the wheel.

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

Save to `/tmp/codex-research.md`

---

## Phase 3: WEB_SEARCH (Always — Opus)

Use WebSearch to find additional context:

```text
Search: "[TOPIC] best practices architecture 2026"
Search: "[TOPIC] common mistakes pitfalls"
Search: "[TOPIC] implementation patterns"
```

Extract key insights and add to consolidation.

---

## Phase 4: CONSOLIDATE (Opus)

Merge all research into single document.

```bash
mkdir -p .claude/research
```

Write to `.claude/research/${FILENAME}.md`:

```markdown
# Research: [TOPIC]

Generated: [YYYY-MM-DD HH:MM]
Agents: Opus [+ Antigravity (agy bridge MCP)] [+ Codex]

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
- Opus: Codebase exploration
- Antigravity (agy bridge MCP): [if used]
- Codex: [if used]
```

---

## Phase 5: OUTPUT

### Write the Research Document

Save consolidated research to `.claude/research/${FILENAME}.md`

### Show Summary to User

**CRITICAL: Output must include CLICKABLE link using markdown format.**

Output this EXACT format (substitute actual values):

```markdown
## Research Complete: [TOPIC]

| Metric | Value |
|--------|-------|
| Agents | Opus [+ Antigravity] [+ Codex] |
| Codebase files | [N] analyzed |
| Web sources | [N] referenced |
| Patterns found | [N] |
| Pitfalls found | [N] |

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

**Click to open**: [[FILENAME].md](.claude/research/[FILENAME].md)
```

**IMPORTANT**: The link MUST be in markdown format `[text](path)` to be clickable in VSCode.

Example output:
```markdown
**Click to open**: [game-bastion-design.md](.claude/research/game-bastion-design.md)
```

---

## Examples

### Basic (Codebase Only)

```
/research authentication flow
```
→ Explores codebase for auth patterns
→ Output: `.claude/research/authentication-flow.md`

### With Antigravity (agy bridge MCP)

```
/research -g game bastion design
```
→ Codebase + Antigravity web research
→ Output: `.claude/research/game-bastion-design.md`

### Full Research

```
/research -gc microservices architecture
```
→ Codebase + Antigravity + Codex
→ Maximum coverage
→ Output: `.claude/research/microservices-architecture.md`

---

## When to Use Each Mode

| Mode | Use When |
|------|----------|
| No flags | Quick codebase check, familiar domain |
| `-g` | Need best practices, architecture guidance |
| `-c` | Need implementation patterns, code examples |
| `-gc` | Major decision, unfamiliar domain, want comprehensive research |

---

## Integration with Workflows

After research, you can:
1. **Read the doc** and decide approach manually
2. **Distill** key insights into CLAUDE.md rules when they should become permanent workflow rules
3. **Feed to workflow**: `/wf12 <task>` and reference the research

Research docs are Claude command outputs under `.claude/research/` like before. Scratch notes belong under `.claude/temp/`.

---

## User's Topic

$ARGUMENTS
