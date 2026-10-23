# /reflect - Turn Failures into Rules with Escalation

**Updated:** `14-oct-2026`

**Purpose**: Record every failure in full in the log (`~/.claude/reflections/`), track recurrence, escalate mechanically. The global rules file stays lean: it gets at most one added or tightened line per reflection.

---

## Usage

```bash
/reflect                # Address failure → full rule to the log, at most one lean line in the rules file
/reflect -g             # Use Gemini to help craft rule
/reflect -c             # Use Codex to help craft rule
/reflect -gc            # Use both Gemini + Codex
/reflect --list         # Show unaddressed failures (READ-ONLY)
/reflect --dry          # Dry run: show what would change, don't edit
```

---

## Flag Detection

```bash
GEMINI=false
CODEX=false
DRY_RUN=false
LIST_ONLY=false

if [[ "$ARGUMENTS" == *"--list"* ]]; then LIST_ONLY=true; fi
if [[ "$ARGUMENTS" == *"--dry"* ]]; then DRY_RUN=true; fi

if [[ "$ARGUMENTS" == *"-gc"* ]] || [[ "$ARGUMENTS" == *"-cg"* ]]; then
  GEMINI=true; CODEX=true
elif [[ "$ARGUMENTS" == *"-g"* ]]; then
  GEMINI=true
elif [[ "$ARGUMENTS" == *"-c"* ]]; then
  CODEX=true
fi
```

---

## Mode Behaviors

| Mode | Reads | Writes | Reviews |
|------|-------|--------|---------|
| `/reflect` | incidents.jsonl, failures.md | rules file (at most one line), incidents.jsonl, failures.md, failures-addressed.md, reflection-log.md | Self |
| `/reflect -g` | same | same | Gemini |
| `/reflect -c` | same | same | Codex |
| `/reflect -gc` | same | same | Both |
| `/reflect --list` | incidents.jsonl, failures.md | **NONE** | — |
| `/reflect --dry` | same | **NONE** (shows preview) | Optional |

---

## Phase 1: EXTRACT Failure

Look back in conversation for:
- "You're right" / "My mistake" / "I was wrong"
- User correction or frustration
- Failed verification
- Self-caught error

Extract these fields (keep each to 1-2 lines max):
- **what**: The failure (1 line)
- **root_cause**: Why it happened (1 line)
- **lesson**: Rule to prevent recurrence (1 line)

If unclear, ASK: "What failure should I reflect on?"

---

## Phase 2: GENERATE ID + CHECK RECURRENCE

### Generate ID

Format: `[PROJ]-[BRANCH]-[COMMIT6]-[N]`

| Component | Source | Example | If absent |
|-----------|--------|---------|-----------|
| PROJ | 3-4 letter project code | `SIM`, `ORCH`, `GLO` | Required |
| BRANCH | `git branch --show-current` | `ai-merge`, `master` | Omit (global/no git) |
| COMMIT6 | `git rev-parse --short=6 HEAD` | `68817e` | Omit (no commits) |
| N | Increment within same prefix | `1`, `2`, `3` | Required |

```bash
PROJ="GLO"  # or detect from repo name
BRANCH=$(git branch --show-current 2>/dev/null || echo "")
COMMIT=$(git rev-parse --short=6 HEAD 2>/dev/null || echo "")

if [ -n "$BRANCH" ] && [ -n "$COMMIT" ]; then
  PREFIX="${PROJ}-${BRANCH}-${COMMIT}"
elif [ -n "$BRANCH" ]; then
  PREFIX="${PROJ}-${BRANCH}"
else
  PREFIX="${PROJ}"
fi

EXISTING=$(grep -c "\"id\":\"${PREFIX}-" ~/.claude/reflections/incidents.jsonl 2>/dev/null || echo 0)
N=$((EXISTING + 1))
ID="${PREFIX}-${N}"
```

### Check Recurrence

**CRITICAL:** Before logging, search incidents.jsonl for matching root_cause patterns:

```bash
# Search for similar root causes
grep -i "<root_cause_keywords>" ~/.claude/reflections/incidents.jsonl
```

If match found:
1. If multiple matches, pick the MOST SIMILAR root_cause (or ask if ambiguous)
2. Set `recurrence_of` to the matching incident ID
3. Look up that incident's current escalation level in failures-addressed.md
4. Bump level: L1→L2, L2→L3, L3→L4

If no match: this is L1 (first occurrence).

---

## Phase 3: CRAFT Rule in WHEN/DO/PROVE Format

Convert lesson into structured rule. This full rule is recorded in the log (Phase 6); the global rules file only ever gets the one-line version (Phase 5):

```markdown
### [Rule Title] (ref: [ID])
WHEN [trigger condition]:
DO [specific action to take].
PROVE [verifiable evidence that DO was followed].
```

**Example:**
```markdown
### Verify Counts Before Claiming (ref: GLO-1)
WHEN stating a count ("there are N items"):
DO search for actual definitions before claiming.
PROVE grep/search output showing exact count.
```

### If `-g` flag (Antigravity Review via agy bridge MCP):

```
mcp__agy__agy_ask  prompt="
Review this failure and proposed WHEN/DO/PROVE rule:

FAILURE: [what]
ROOT CAUSE: [root_cause]
RECURRENCE OF: [previous ID or 'none']
ESCALATION LEVEL: [L1/L2/L3/L4]
PROPOSED RULE:
WHEN [trigger]
DO [action]
PROVE [evidence]

Improve the rule:
1. Make PROVE mechanically verifiable (not subjective)
2. If L2+, strengthen the PROVE requirement
3. If L3+, add a workflow gate (cannot proceed without proof)
4. Keep it minimal — one trigger, one action, one proof

Output: Improved WHEN/DO/PROVE rule only.
"
```

### If `-c` flag (Codex Review):

```
mcp__codex-cli__codex "
Review this failure and proposed WHEN/DO/PROVE rule:

FAILURE: [what]
ROOT CAUSE: [root_cause]
RECURRENCE OF: [previous ID or 'none']
ESCALATION LEVEL: [L1/L2/L3/L4]
PROPOSED RULE:
WHEN [trigger]
DO [action]
PROVE [evidence]

Improve based on:
1. Software engineering best practices
2. Minimal but effective — one sentence each
3. PROVE must be checkable (command output, not feelings)

Output: Improved WHEN/DO/PROVE rule only.
"
```

---

## Phase 4: DETERMINE Scope + Pillar

### Scope

| Scope | Criteria | Target File |
|-------|----------|-------------|
| **Global** | Applies to all projects | the shared rules file (`~/.claude/CLAUDE.md` is a link to it; Codex loads the same file) |
| **Project** | Specific to this codebase | `./CLAUDE.md` |

**Default**: Global (the shared rules file applies everywhere — do NOT duplicate into project). A failure tied to one project, tool or domain is project scope.

### Pillar (recorded in the log; placement in a project CLAUDE.md)

| Pillar | When rule is about... |
|--------|----------------------|
| **1: VERIFICATION** | Proving things work, checking before claiming |
| **2: GIT & STATE** | Branch ops, values, merge, environment |
| **3: COMMUNICATION** | Listening, answering, formatting output |
| **4: AUTONOMY & CODE** | Writing code, testing, scope, delegation |
| **5: REFLECTION** | Learning from mistakes, postmortems |
| **Standalone** | Doesn't fit a pillar (platform-specific, project-specific) |

---

## Phase 5: UPDATE the rules file — at most one lean line (MANDATORY)

The full rule from Phase 3 goes to the log in Phase 6. The rules file itself must stay lean.

**Global scope.** The target is the shared rules file, loaded by Claude Code and Codex on every machine. `~/.claude/CLAUDE.md` is a link to it — edit the real file (`readlink ~/.claude/CLAUDE.md`), never the link.

1. Read the file and look for the line that already covers this failure.
2. If one exists, tighten that line. Only if none does, add ONE new line in the fitting section.
3. One line per rule: plain imperative. No ID, no incident story, no WHEN/DO/PROVE block, no level tag.

**Project scope** (`./CLAUDE.md`): add the WHEN/DO/PROVE rule with its reference ID; for L3+ prefix it with `**ESCALATION L3** (strikes: [ID1]→[ID2]→[ID3])`.

**Actually edit the file** using Edit tool, or state why an existing line already covers the failure unchanged.

---

## Phase 5.5: LINE BUDGET (global rules file)

The budget is the number in the file's own header (`# Budget: N lines`).

```bash
F=$(readlink ~/.claude/CLAUDE.md || echo ~/.claude/CLAUDE.md)
echo "rules file: $(wc -l < "$F") lines; $(grep -m1 '^# Budget' "$F")"
```

Over budget → merge or remove a line before finishing. Never raise the budget yourself. Removing a line loses nothing: every rule's full text stays in `reflection-log.md`.

---

## Phase 6: LOG to incidents.jsonl + failures-addressed.md

### Append to incidents.jsonl

Use the **Write/Edit tool** (not bash echo) to append a JSON line. This prevents escaping issues with quotes in failure descriptions.

```jsonl
{"id":"[ID]","ts":"[ISO8601]","trigger":"[user_correction|self_caught|failed_verification|frustration]","what":"[1 line]","root_cause":"[1 line]","rule_id":"[rule title]","level":"[L1|L2|L3|L4]","recurrence_of":[previous ID string or null],"pillar":[1-5]}
```

**Field rules:**
- `recurrence_of`: Use `null` (no quotes) for first occurrence, `"GLO-6"` (quoted string) for recurrence
- `level`: Must match escalation ladder (L1/L2/L3/L4)
- `pillar`: Integer 1-5 from Phase 4

### Append to failures-addressed.md

```markdown
## [ID] | ADDRESSED | [date]

**What happened:** [failure]
**Root cause:** [why]
**Rule added:** [file] → "[Rule Title]" (Pillar [N])
**Escalation:** [L1/L2/L3/L4]
**Recurrence of:** [previous ID or "none"]
**Reviewed by:** [Gemini/Codex/Self]
**Status:** MONITORING (7 days)
```

### Also log to failures.md (legacy prose format, for human reading)

```markdown
## [ID] | [date] | [scope]

**Context:** [what was happening]
**Failure:** [what went wrong]
**Root cause:** [why]
**Rule:** [WHEN/DO/PROVE summary]
```

### Append verbatim to reflection-log.md (PERMANENT HISTORY — append-only, NEVER edited)

`~/.claude/reflections/reflection-log.md` is the immutable canonical record: every reflection's **full rule text** + metadata, appended forever, **never edited, compressed, or pruned**. The rules file carries only a one-line version, or nothing; this is where the detail lives.

Append with the Edit tool (add below the "NEW REFLECTIONS APPEND BELOW" marker — never rewrite content above it):

```markdown
## [ID] | [ISO8601 timestamp] | [L1/L2/L3/L4] | Pillar [N] | scope=[global|project] | reviewed=[Gemini|Codex|Self]
**What:** [failure]
**Root cause:** [why]
**Recurrence of:** [previous ID or none]
**Rule (full text):**
### [Rule Title] (ref: [ID])
WHEN [trigger]:
DO [action].
PROVE [evidence].
---
```

The full rule survives here permanently whatever happens to its line in the rules file.

---

## Phase 7: OUTPUT Summary

```
✓ FAILURE ADDRESSED: [ID]

What: [1 line]
Root cause: [1 line]
Recurrence of: [previous ID or "first occurrence"]
Escalation: [L1/L2/L3/L4]
Rule: WHEN [trigger] DO [action] PROVE [evidence]
Rules file: [file]:[line] — [line added | line tightened | already covered]
Reviewed by: [reviewer] ✓
```

---

## /reflect --list

Show unaddressed failures from incidents.jsonl and failures.md:

```bash
# From incidents.jsonl — find entries not in failures-addressed.md
# From failures.md — find entries with no matching addressed entry
```

Scan both files, cross-reference with failures-addressed.md, show unaddressed:

```
=== UNADDRESSED FAILURES ===

| ID | Date | What Happened | Scope | Recurrence? |
|----|------|---------------|-------|-------------|
| GLO-23 | 2026-02-23 | Delegated to user | Global | No |
| SIM-ai-merge-68817e-1 | 2026-02-23 | Wrong pattern | Project | Yes (GLO-13) |

Run `/reflect` to address the most recent failure.
```

Also show escalation status:
```
=== ESCALATION WATCH ===

| Pattern | Level | Strike Chain | Next = |
|---------|-------|-------------|--------|
| Value substitution | L3 | GLO-6→GLO-9→GLO-26 | L4 HALT |
| Ignoring questions | L2 | GLO-13→GLO-14 | L3 gate |
```

---

## Escalation Ladder Reference

| Level | Trigger | Rule Change | PROVE Requirement |
|-------|---------|-------------|-------------------|
| **L1** | First occurrence | Add WHEN/DO/PROVE rule | Standard |
| **L2** | Same pattern recurs 1x | Strengthen PROVE | Must show execution output |
| **L3** | Recurs 2x | Add workflow gate | Cannot proceed without printed proof |
| **L4** | Recurs 3x | HALT | "MANUAL INTERVENTION — pattern X failed 3 rules" |

---

## File Structure

```
~/.claude/
├── CLAUDE.md                      # Link to the shared lean rules file (one line per rule, line budget in its header)
└── reflections/                   # The log — may itself be a link into the shared log folder
    ├── incidents.jsonl             # Structured incident log (source of truth)
    ├── failures.md                 # Prose failures (human-readable)
    ├── failures-addressed.md      # Addressed with rules + escalation
    └── reflection-log.md          # PERMANENT append-only verbatim history — every rule's original full text, never edited

[project]/.claude/
├── CLAUDE.md                      # Project-specific rules only
└── reflections/
    ├── incidents.jsonl             # Project incidents
    ├── failures.md                 # Project failures
    └── failures-addressed.md      # Project addressed
```

---

## Summary

| Feature | Old | Current |
|---------|----------|--------------|
| **Rule format** | Prose paragraphs | WHEN/DO/PROVE |
| **Storage** | failures.md only | incidents.jsonl + failures.md |
| **Recurrence** | Manual cross-reference | Auto-detect via root_cause grep |
| **Escalation** | None (same rule re-added) | L1→L2→L3→L4 ladder |
| **Phase 5** | Full rule appended to CLAUDE.md | Full rule to the log; rules file gets at most one lean line |
| **--list** | Broken (grepped non-existent field) | Cross-references addressed table |
| **Pillar placement** | Appended anywhere | Routed to correct pillar |
| **Flags** | `-g` Gemini, `-c` Codex, `-gc` both | Same |
| **Scope** | Global + Project duplicate | Global only (unless project-specific) |
