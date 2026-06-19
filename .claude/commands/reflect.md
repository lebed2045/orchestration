# /reflect - Turn Failures into Rules with Escalation

**Updated:** `19-jun-2026`

**Purpose**: Turn failures into WHEN/DO/PROVE rules in CLAUDE.md. Track recurrence. Escalate mechanically.

---

## Usage

```bash
/reflect                # Address failure → add WHEN/DO/PROVE rule
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
| `/reflect` | incidents.jsonl, failures.md | CLAUDE.md (+compress if >30k), incidents.jsonl, failures.md, failures-addressed.md, reflection-log.md | Self |
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

Convert lesson into structured rule:

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
| **Global** | Applies to all projects | `~/.claude/CLAUDE.md` |
| **Project** | Specific to this codebase | `./CLAUDE.md` |

**Default**: Global (rules in `~/.claude/CLAUDE.md` apply everywhere — do NOT duplicate into project).

### Pillar (for placement in CLAUDE.md)

| Pillar | When rule is about... |
|--------|----------------------|
| **1: VERIFICATION** | Proving things work, checking before claiming |
| **2: GIT & STATE** | Branch ops, values, merge, environment |
| **3: COMMUNICATION** | Listening, answering, formatting output |
| **4: AUTONOMY & CODE** | Writing code, testing, scope, delegation |
| **5: REFLECTION** | Learning from mistakes, postmortems |
| **Standalone** | Doesn't fit a pillar (platform-specific, project-specific) |

---

## Phase 5: ADD Rule to CLAUDE.md (MANDATORY)

**This phase is NOT optional. A reflection without a rule is just a diary entry.**

1. Read target CLAUDE.md
2. Find the correct Pillar section
3. Add WHEN/DO/PROVE rule with reference ID
4. If escalation level is L3+, add `**ESCALATION L3**` prefix with strike history

```markdown
### [Rule Title] (ref: [ID])
WHEN [trigger]:
DO [action].
PROVE [evidence].
```

For L3 escalation:
```markdown
### [Rule Title] (ref: [ID])
**ESCALATION L3** (strikes: [ID1]→[ID2]→[ID3]): [mechanical gate description]
WHEN [trigger]:
DO [action].
PROVE [mandatory proof — cannot proceed without this].
```

**Actually edit the file** using Edit tool. If you skip this phase, the reflection is worthless.

---

## Phase 5.5: SIZE-GATE COMPRESSION (append-first, compress only above 30k)

**Rules are ALWAYS appended in Phase 5 — never blocked, never merged-instead-of-added.** The budget is enforced AFTER the append, not before. CLAUDE.md is loaded in full into context every session; the official guidance is to keep it small (under ~200 lines / well under the 40k-char warning). The budget keeps it there without ever refusing a new rule.

```bash
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak       # always refresh backup first
SIZE=$(wc -c < ~/.claude/CLAUDE.md)
echo "CLAUDE.md size: $SIZE chars (budget: 30000)"
[ "$SIZE" -gt 30000 ] && echo "OVER 30k → COMPRESSION REQUIRED this run" || echo "under budget → no compression needed"
```

**If `$SIZE <= 30000`: do nothing. Stop here, go to Phase 6.**

**If `$SIZE > 30000`: run ONE compression pass** on `~/.claude/CLAUDE.md`, applying these levers in order, stopping as soon as `wc -c <= 30000` (or all levers exhausted):

1. **Collapse provenance.** Replace any `**ESCALATION Lx** (strikes: …): <prose>` line with just the level tag `**[Lx]**`. Move the stripped strike-chain + rationale verbatim to `~/.claude/CLAUDE_ARCHIVE.md`, keyed by rule heading — **archive FIRST, then strip** (the perl alone would delete the provenance):
   `{ echo; echo "## Provenance moved by compression pass $(date '+%Y-%m-%d %H:%M:%S')"; grep '^\*\*ESCALATION L' ~/.claude/CLAUDE.md; } >> ~/.claude/CLAUDE_ARCHIVE.md`
   `perl -i -pe 's/^\*\*ESCALATION (L\d(?: HALT)?)\*\*.*$/**[$1]**/' ~/.claude/CLAUDE.md`
2. **Trim illustrative examples.** In the longest blocks, collapse multi-item example lists / parentheticals to a single example. Move nothing structural.
3. **Drop redundant restatements.** A trailing "If X, the rule failed." that only restates the PROVE may be removed.

**HARD GUARDRAILS — compression must NEVER:**
- delete or weaken any `WHEN` / `DO` / `PROVE` / `HALT` directive
- remove an entire `###` rule block
- demote or remove a safety / destructive gate — no-sudo, no-delete/stash/reset without permission, mounts & daemons (GLO-38), daily-driver browser (GLO-44), Exact Values, Questions-Are-Not-Authorization, and any `**[L4]**`/`HALT` rule stay in CLAUDE.md verbatim
- alter a level tag (`**[Lx]**`)

**PROVE (mandatory) before declaring the run done:** paste `wc -c` before/after AND confirm these counts are UNCHANGED vs the `.bak`:
```bash
b=~/.claude/CLAUDE.md.bak; f=~/.claude/CLAUDE.md
for pat in '^### ' '^WHEN ' '^DO ' '^PROVE ' '^HALT'; do
  printf '%s now=%s was=%s\n' "$pat" "$(grep -c "$pat" "$f")" "$(grep -c "$pat" "$b")"
done
```
Any count that dropped = compression corrupted a rule → **restore from `~/.claude/CLAUDE.md.bak` and retry more conservatively.**

---

## Phase 6: LOG to incidents.jsonl + failures-addressed.md

### Append to incidents.jsonl

Use the **Write/Edit tool** (not bash echo) to append a JSON line. This prevents escaping issues with quotes in failure descriptions.

```jsonl
{"id":"[ID]","ts":"[ISO8601]","trigger":"[user_correction|self_caught|failed_verification|frustration]","what":"[1 line]","root_cause":"[1 line]","rule_id":"[rule title in CLAUDE.md]","level":"[L1|L2|L3|L4]","recurrence_of":[previous ID string or null],"pillar":[1-5]}
```

**Field rules:**
- `recurrence_of`: Use `null` (no quotes) for first occurrence, `"GLO-6"` (quoted string) for recurrence
- `level`: Must match escalation ladder (L1/L2/L3/L4)
- `pillar`: Integer 1-5 matching CLAUDE.md pillar number

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

`~/.claude/reflections/reflection-log.md` is the immutable canonical record: every reflection's **full rule text** + metadata, appended forever, **never edited, compressed, or pruned** — even when the rule is later compressed (Phase 5.5) or retired in CLAUDE.md. This is the unchanged history; CLAUDE.md is the live working copy.

Append with the Edit tool (add below the "NEW REFLECTIONS APPEND BELOW" marker — never rewrite content above it):

```markdown
## [ID] | [ISO8601 timestamp] | [L1/L2/L3/L4] | Pillar [N] | scope=[global|project] | reviewed=[Gemini|Codex|Self]
**What:** [failure]
**Root cause:** [why]
**Recurrence of:** [previous ID or none]
**Rule (verbatim as added to CLAUDE.md):**
### [Rule Title] (ref: [ID])
WHEN [trigger]:
DO [action].
PROVE [evidence].
---
```

The full original survives here permanently even if CLAUDE.md shrinks.

---

## Phase 7: OUTPUT Summary

```
✓ FAILURE ADDRESSED: [ID]

What: [1 line]
Root cause: [1 line]
Recurrence of: [previous ID or "first occurrence"]
Escalation: [L1/L2/L3/L4]
Rule: WHEN [trigger] DO [action] PROVE [evidence]
Location: [file]:[line] → Pillar [N]: "[Rule Title]"
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
├── CLAUDE.md                      # Rules (5 pillars + standalone) — live working copy, budget 30k (compressed above it, Phase 5.5)
├── CLAUDE.md.bak                  # Auto-refreshed backup before each compression pass
├── CLAUDE_ARCHIVE.md              # Provenance (strike-chains, trimmed examples) moved out by compression — never loaded
└── reflections/
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
| **Phase 5** | Often skipped | MANDATORY — reflection without rule = worthless |
| **--list** | Broken (grepped non-existent field) | Cross-references addressed table |
| **Pillar placement** | Appended anywhere | Routed to correct pillar |
| **Flags** | `-g` Gemini, `-c` Codex, `-gc` both | Same |
| **Scope** | Global + Project duplicate | Global only (unless project-specific) |
