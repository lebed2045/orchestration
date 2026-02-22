# /reflect - Failure Reflection Command

Capture failures from conversation, log to appropriate locations, propose rules.

**Philosophy**: *"Every failure is a learning opportunity. Automate the capture, focus on the lesson."*

---

## Usage

```bash
/reflect                    # Reflect on failure from conversation
/reflect --list             # Show recent failures across all logs
/reflect --address ID       # Mark failure as addressed
```

---

## How It Works

### Step 1: EXTRACT from Conversation

Look back in conversation for trigger phrases:
- "You're right"
- "My mistake"
- "I was wrong"
- "Good catch"
- User correction

Extract:
- **What happened**: The failure + context (1 line)
- **Lesson**: Rule to prevent recurrence

If no clear failure in conversation, ASK:
```
What failure should I reflect on?
- What happened?
- What's the lesson?
```

---

### Step 2: CLASSIFY Scope

| Scope | Criteria | Log Location |
|-------|----------|--------------|
| **Universal** | Applies to all projects | `~/.claude/reflections/failures.md` |
| **Project** | Specific to this codebase | `.claude/reflections/failures.md` |
| **Both** | Universal lesson + project context | Log in BOTH locations |

**Default**: Log to BOTH if `.claude/` exists in current repo.

---

### Step 3: GENERATE ID

Format: `[SCOPE]-YYMMDD-N`

```bash
# Examples:
GLO-260221-1   # Global, Feb 21 2026, first of day
PRJ-260221-3   # Project, Feb 21 2026, third of day
```

**Auto-increment**: Read existing file, find last ID for today, increment N.

---

### Step 4: LOG Entry

Write to failure log(s):

```markdown
## [ID] | YYYY-MM-DD
**What happened:** [failure + context in 1 line]
**Lesson:** [rule to prevent recurrence]
**Status:** OPEN
```

---

### Step 5: PROPOSE Rule (Optional)

After logging, ask:

```
Should I add a CLAUDE.md rule to prevent this?

Proposed rule:
> [lesson converted to imperative rule]

Options:
1. Add to ~/.claude/CLAUDE.md (global)
2. Add to ./CLAUDE.md (project)
3. Skip rule
```

If rule added, update failure status:

```markdown
**Status:** ADDRESSED → [path/to/CLAUDE.md]
```

---

## Implementation

### On `/reflect` invocation:

```bash
# 1. Check for .claude/ in current repo
if [ -d ".claude" ]; then
  PROJECT_LOG=".claude/reflections/failures.md"
  mkdir -p .claude/reflections
fi

# 2. Global log always exists
GLOBAL_LOG="$HOME/.claude/reflections/failures.md"
mkdir -p "$HOME/.claude/reflections"

# 3. Generate today's date
TODAY=$(date +%Y-%m-%d)
TODAY_SHORT=$(date +%y%m%d)

# 4. Count existing entries for today to get N
GLOBAL_N=$(grep -c "^## GLO-${TODAY_SHORT}" "$GLOBAL_LOG" 2>/dev/null || echo 0)
GLOBAL_N=$((GLOBAL_N + 1))

PROJECT_N=$(grep -c "^## PRJ-${TODAY_SHORT}" "$PROJECT_LOG" 2>/dev/null || echo 0)
PROJECT_N=$((PROJECT_N + 1))
```

---

### Extract Failure from Conversation

1. Search recent messages for trigger phrases
2. Identify the correction/failure
3. Summarize in 1 line
4. Extract or generate lesson

If unclear, use `AskUserQuestion`:
```
I couldn't identify a clear failure. What should I reflect on?
```

---

### Log Entry Template

```markdown
## [ID] | [DATE]
**What happened:** [extracted or provided]
**Lesson:** [extracted or provided]
**Status:** OPEN
```

---

### Show Logged Entry

After logging, output:

```
✓ Logged to ~/.claude/reflections/failures.md
✓ Logged to .claude/reflections/failures.md

## GLO-260221-1 | 2026-02-21
**What happened:** Claimed 4 cops existed when only 3 were defined
**Lesson:** Always verify counts by searching for actual definitions

Propose CLAUDE.md rule? [Y/n]
```

---

## /reflect --list

Show recent failures from both logs:

```bash
echo "=== RECENT FAILURES ==="
echo ""
echo "GLOBAL (~/.claude/reflections/failures.md):"
tail -30 "$HOME/.claude/reflections/failures.md" | grep -A3 "^## "
echo ""
echo "PROJECT (.claude/reflections/failures.md):"
tail -30 ".claude/reflections/failures.md" | grep -A3 "^## " 2>/dev/null || echo "(no project log)"
```

Output format:
```
=== RECENT FAILURES ===

GLOBAL:
- GLO-260221-1 | Recommended wrong repo | OPEN
- GLO-260220-2 | Assumed path exists | ADDRESSED

PROJECT:
- PRJ-260221-1 | Wrong cop count | ADDRESSED
```

---

## /reflect --address ID

Mark a failure as addressed:

1. Find entry by ID in appropriate log
2. Update status line:
   ```markdown
   **Status:** ADDRESSED → [rule location or "manual fix"]
   ```
3. If rule was added, log to `failures-addressed.md`:
   ```markdown
   ## [ID] | ADDRESSED | [DATE]
   **Original:** [link to failure]
   **Rule added:** [path:line]
   **Monitoring:** Check for recurrence over next 7 days
   ```

---

## Integration with Conversation Flow

When Claude detects it made a mistake (triggers like "You're right"):

1. **Automatic prompt**:
   ```
   I should reflect on this. Running /reflect...
   ```

2. **Extract failure** from context
3. **Log** to both locations
4. **Propose rule** if pattern is preventable
5. **Continue conversation** (no longer BLOCKING)

---

## Examples

### Example 1: Simple Reflection

```
User: You said there were 4 cops but only 3 exist
Claude: You're right, I should reflect on this.

✓ Logged: GLO-260221-1
**What happened:** Claimed 4 cops in CLAUDE.md but only 3 defined in wf12.md
**Lesson:** Verify counts by searching for actual agent definitions

Propose rule? → Added to ./CLAUDE.md:
> Before claiming a count, search for actual definitions
```

### Example 2: List Failures

```
/reflect --list

=== RECENT FAILURES ===

GLOBAL:
| ID | Date | What | Status |
|----|------|------|--------|
| GLO-260221-1 | 2026-02-21 | Wrong repo recommendation | OPEN |

PROJECT:
| ID | Date | What | Status |
|----|------|------|--------|
| PRJ-260221-1 | 2026-02-21 | 4 vs 3 cops mismatch | ADDRESSED |
```

---

## File Structure

```
~/.claude/
└── reflections/
    ├── failures.md           # Global failures log
    └── failures-addressed.md # Tracking addressed failures

[project]/.claude/
└── reflections/
    ├── failures.md           # Project-specific failures
    └── failures-addressed.md # Project addressed tracking
```

---

## Summary

| Feature | Behavior |
|---------|----------|
| **Scope** | Logs to BOTH global + project (if .claude/ exists) |
| **ID format** | `GLO-YYMMDD-N` or `PRJ-YYMMDD-N` |
| **Entry format** | 2 fields: What happened + Lesson |
| **Rule proposal** | Optional, after logging |
| **Status tracking** | OPEN → ADDRESSED |
| **Non-blocking** | Log within 10 min, continue conversation |
