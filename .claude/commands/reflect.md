# /reflect - Address Failures with Rules

**Purpose**: Turn failures into CLAUDE.md rules. Not just logging — actual changes.

---

## Usage

```bash
/reflect                # Address failure → add rule to CLAUDE.md
/reflect -g             # Use Gemini to help craft better rule
/reflect -c             # Use Codex to help craft better rule
/reflect -gc            # Use both Gemini + Codex (same as -cg)
/reflect -cg            # Same as -gc
/reflect --list         # Show open failures (READ-ONLY, no changes)
/reflect --dry          # Dry run: show what would be added, don't edit
```

---

## Flag Detection

```bash
GEMINI=false
CODEX=false
DRY_RUN=false
LIST_ONLY=false

# Check for --list (read-only mode)
if [[ "$ARGUMENTS" == *"--list"* ]]; then
  LIST_ONLY=true
fi

# Check for --dry (dry run mode)
if [[ "$ARGUMENTS" == *"--dry"* ]]; then
  DRY_RUN=true
fi

# Check for review flags
if [[ "$ARGUMENTS" == *"-gc"* ]] || [[ "$ARGUMENTS" == *"-cg"* ]]; then
  GEMINI=true
  CODEX=true
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
| `/reflect` | failures.md | CLAUDE.md, failures-addressed.md | Self |
| `/reflect -g` | failures.md | CLAUDE.md, failures-addressed.md | Gemini |
| `/reflect -c` | failures.md | CLAUDE.md, failures-addressed.md | Codex |
| `/reflect -gc` | failures.md | CLAUDE.md, failures-addressed.md | Both |
| `/reflect --list` | failures.md | **NONE** | — |
| `/reflect --dry` | failures.md | **NONE** (shows preview) | Optional |

---

## Phase 1: EXTRACT Failure

Look back in conversation for:
- "You're right" / "My mistake" / "I was wrong"
- User correction
- Failed verification

Extract:
- **What happened**: The failure (1 line)
- **Root cause**: Why it happened
- **Lesson**: Rule to prevent recurrence

If unclear, ASK:
```
What failure should I reflect on?
```

---

## Phase 2: GENERATE ID

Format: `[SCOPE]-YYMMDD-N`

```bash
TODAY_SHORT=$(date +%y%m%d)

# Count existing entries for today
GLOBAL_N=$(grep -c "^## GLO-${TODAY_SHORT}" ~/.claude/reflections/failures.md 2>/dev/null || echo 0)
GLOBAL_N=$((GLOBAL_N + 1))

# Generate ID
ID="GLO-${TODAY_SHORT}-${GLOBAL_N}"
```

---

## Phase 3: CRAFT Rule

Convert lesson into imperative CLAUDE.md rule:

```
Lesson: "Always verify counts by searching for actual definitions"

Rule:
> ## Verify Before Claiming Counts
> Before claiming a count (e.g., "there are N items"), search for actual definitions.
```

### If `-g` flag (Gemini Review):

```bash
mcp__gemini__ask-gemini "
Review this failure and proposed rule:

FAILURE: [what happened]
ROOT CAUSE: [why]
PROPOSED RULE: [rule text]

Improve the rule to be:
1. More specific and actionable
2. Catch edge cases
3. Not overly broad

Output: Improved rule text only.
"
```

### If `-c` flag (Codex Review):

```bash
mcp__codex-cli__codex "
Review this failure and proposed rule:

FAILURE: [what happened]
ROOT CAUSE: [why]
PROPOSED RULE: [rule text]

Improve the rule based on:
1. Software engineering best practices
2. How elite developers prevent this
3. Minimal but effective wording

Output: Improved rule text only.
"
```

---

## Phase 4: DETERMINE Scope

| Scope | Criteria | Target File |
|-------|----------|-------------|
| **Global** | Applies to all projects | `~/.claude/CLAUDE.md` |
| **Project** | Specific to this codebase | `./CLAUDE.md` |
| **Both** | Universal lesson | Add to BOTH files |

**Default**: Both (if `./CLAUDE.md` exists).

---

## Phase 5: ADD Rule to CLAUDE.md

1. Read target CLAUDE.md
2. Find appropriate section (or create new section)
3. Add rule with reference ID

```markdown
## [Rule Title] (ref: GLO-260221-1)
[Rule text]
```

**Actually edit the file** using Edit tool.

---

## Phase 6: LOG to failures-addressed.md

After rule is added, create entry in `~/.claude/reflections/failures-addressed.md`:

```markdown
## GLO-260221-1 | ADDRESSED | 2026-02-21

**What happened:** [failure]
**Root cause:** [why]
**Rule added:** ~/.claude/CLAUDE.md → "Verify Before Claiming Counts"
**Reviewed by:** [Gemini/Codex/Self]
**Status:** MONITORING (7 days)
```

Also log to `.claude/reflections/failures-addressed.md` if project scope.

---

## Phase 7: OUTPUT Summary

```
✓ FAILURE ADDRESSED: GLO-260221-1

What happened: Claimed 4 cops when only 3 existed
Root cause: Didn't search for actual agent definitions
Rule added: ~/.claude/CLAUDE.md:142 → "Verify Before Claiming Counts"

Reviewed by: Gemini ✓

Monitoring: 7 days for recurrence
```

---

## /reflect --list

Show OPEN failures that need addressing:

```bash
grep -B1 "Status.*OPEN" ~/.claude/reflections/failures.md
grep -B1 "Status.*OPEN" .claude/reflections/failures.md 2>/dev/null
```

Output:
```
=== OPEN FAILURES ===

| ID | Date | What Happened | Scope |
|----|------|---------------|-------|
| GLO-260221-1 | 2026-02-21 | Wrong repo recommendation | Global |
| PRJ-260221-1 | 2026-02-21 | Misunderstood project structure | Project |

Run `/reflect` to address the most recent failure.
```

---

## Complete Flow Example

```
User: You said there were 4 cops but only 3 exist
Claude: You're right. Let me address this.

Running /reflect -g...

## Extracting Failure
- What happened: Claimed 4 cops in CLAUDE.md but only 3 defined
- Root cause: Didn't search for actual agent definitions before stating count
- Lesson: Verify counts by searching

## Crafting Rule
Proposed: "Before claiming a count, search for actual definitions"

## Gemini Review
Gemini suggests: "Before stating any count (N items, N files, etc.),
run a search to verify the actual count. Never trust memory or prior knowledge."

## Adding to CLAUDE.md
Added to ~/.claude/CLAUDE.md:142

## Logging
✓ GLO-260221-1 → failures-addressed.md

---
✓ FAILURE ADDRESSED: GLO-260221-1
Rule: "Verify counts by searching"
Location: ~/.claude/CLAUDE.md:142
Reviewed by: Gemini
```

---

## File Structure

```
~/.claude/
├── CLAUDE.md                      # Rules get added here
└── reflections/
    ├── failures.md                # Raw failures (OPEN status)
    └── failures-addressed.md      # Addressed with rules

[project]/.claude/
├── CLAUDE.md                      # Project-specific rules
└── reflections/
    ├── failures.md                # Project failures
    └── failures-addressed.md      # Project addressed
```

---

## Summary

| Feature | Behavior |
|---------|----------|
| **Action** | Adds rule to CLAUDE.md (not just logs) |
| **Flags** | `-g` Gemini, `-c` Codex, `-gc` both |
| **Scope** | Global + Project (if exists) |
| **ID format** | `GLO-YYMMDD-N` / `PRJ-YYMMDD-N` |
| **Output** | Rule added, location, reviewer |
| **Tracking** | Moves to `failures-addressed.md` |
| **Monitoring** | 7 days for recurrence |
