# Research: Auto-Reflection and Failure Tracking for Claude

Generated: 2026-02-21 22:15
Agents: Opus + Gemini + Codex

---

## Executive Summary

Your current failure tracking system in CLAUDE.md is solid but **missing the critical "bridge" between logging and rule promotion**. Best practice is a **two-lane pipeline**: immediate logging (you have this) + periodic curation/promotion (you're missing this). The key missing piece is `failures-addressed.md` and a **repeat-count threshold** before adding rules.

---

## Your Current System (Codebase Patterns)

### What You Have

| Component | Status | Location |
|-----------|--------|----------|
| Failure logging | Working | `~/.claude/reflections/failures.md` (universal) |
| | Working | `[repo]/.claude/reflections/failures.md` (project) |
| Log format | Good | Context, Failure, Root cause, Lesson |
| Trigger phrases | Good | "You're right", "My mistake", etc. |
| BLOCKING requirement | Good | Must log before continuing |
| Rule proposal | Partial | Step 5 says "propose rule" but no promotion pipeline |
| Addressed tracking | **Missing** | `failures-addressed.md` mentioned but doesn't exist |

### Gap Analysis

1. **No repeat-count tracking** - Can't tell if same failure occurred 3x
2. **No promotion pipeline** - Lessons stay in failures.md, never become rules
3. **No expiry/staleness** - Old failures never get cleaned up
4. **No metrics** - Can't measure improvement over time

---

## Expert Approaches (From Gemini + Codex)

### Hierarchical Memory Model (Recommended)

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: CLAUDE.md (Long-term Memory)               │
│ - Stable architectural rules                         │
│ - Patterns proven across 3+ incidents               │
│ - Rarely changes (monthly review)                   │
├─────────────────────────────────────────────────────┤
│ Layer 2: .claude/rules/*.md (Module Memory)         │
│ - Path-scoped rules (e.g., "/tests → use Vitest")   │
│ - Component-specific constraints                     │
│ - Changes when modules change                        │
├─────────────────────────────────────────────────────┤
│ Layer 3: failures.md (Short-term Memory)            │
│ - Transient, immediate corrections                   │
│ - Raw failure events (append-only)                   │
│ - Gets curated → promoted to Layer 1/2              │
└─────────────────────────────────────────────────────┘
```

### Two-Lane Pipeline

| Lane | Purpose | Frequency |
|------|---------|-----------|
| **Runtime** | Log failure immediately | Every occurrence |
| **Curation** | Review failures, promote to rules | Weekly/bi-weekly |

---

## Immediate vs Batch: When to Do Each

### Immediate (Hotfix Rule)

Add rule to CLAUDE.md **immediately** when:
- High severity (data loss, security, breaking changes)
- Clear pattern (not ambiguous)
- Same failure 2x in same session
- User explicitly requests it

### Batch (Deferred Curation)

Collect and review **weekly** when:
- Low severity (style, preference)
- Ambiguous root cause
- One-off occurrence
- Needs pattern confirmation

### Recommended Default: **Log Immediate, Promote Deferred**

```
Failure occurs → Log to failures.md (immediate)
                 ↓
Weekly review → Count repeats, identify patterns
                 ↓
Promotion threshold met (2+) → Add to CLAUDE.md
                 ↓
Move to failures-addressed.md with MONITORING status
```

---

## Prevention Patterns

### Pattern 1: Repeat-Count Threshold

Only promote to rule after **2+ occurrences** (prevents rule bloat):

```markdown
## failures-addressed.md

| ID | Failure Pattern | Count | Status | Rule Added |
|----|-----------------|-------|--------|------------|
| F001 | Assumed path exists | 3 | ADDRESSED | Fresh Verification Rule |
| F002 | Wrong test command | 2 | MONITORING | TDD Red Phase |
| F003 | Style preference | 1 | TRACKING | (pending 2nd occurrence) |
```

### Pattern 2: Negative Constraints

LLMs respond better to "NEVER" than "ALWAYS":

```markdown
# Less effective
- Always verify file exists before reading

# More effective
- NEVER assume a file exists - run `ls` first
```

### Pattern 3: Path-Scoped Rules

Don't force global rules when scope is limited:

```markdown
# .claude/rules/tests.md
globs: ["**/*.test.*", "**/tests/**"]

Rules:
- Use Vitest, not Jest
- Run `npm test` not `npm run test`
```

### Pattern 4: Proof-of-Lesson Prompt

After logging failure, explicitly ask Claude to acknowledge:

```markdown
Before next task: "Read failures.md and state which lesson applies to this task"
```

---

## Recommended File Structure

```text
.claude/
├── reflections/
│   ├── failures.md              # Raw failure log (append-only)
│   ├── failures-addressed.md    # Promotion tracking + postmortems
│   └── metrics.json             # Optional: repeat counts, trends
├── rules/
│   ├── tests.md                 # Path-scoped: test patterns
│   └── git.md                   # Path-scoped: git operations
└── CLAUDE.md                    # Global promoted rules
```

### failures-addressed.md Format

```markdown
# Failures Addressed Log

## F001 | 2026-02-15 | Fresh Verification Rule

**Original failures:**
- 2026-02-10: Assumed branch existed without checking
- 2026-02-12: Claimed file missing without ls
- 2026-02-14: Wrong path assumption

**Pattern identified:** Making claims about filesystem/git state without verification

**Rule added to:** ~/.claude/CLAUDE.md (Universal)

**Rule text:**
> Before ANY of these actions, run a FRESH command...

**Status:** MONITORING
**Effectiveness:** TBD (track if recurs)

---

## F002 | 2026-02-20 | RECURRENCE - Postmortem

**Original rule:** Fresh Verification Rule (F001)
**Recurrence date:** 2026-02-20
**What happened:** Still made assumption about workflow design without re-reading file

**Root cause of recurrence:**
- Rule said "verify filesystem" but didn't explicitly include "design claims"
- Gap in rule specificity

**Rule update:** Added "Making design claims → re-read source file" to Fresh Verification Rule

**Status:** MONITORING (updated rule)
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Rule Bloat** | Too many rules, Claude ignores middle | Promote only 2+ repeats |
| **Contradictory Rules** | Rule A conflicts with Rule B | Review rules for conflicts before adding |
| **Ghost Failures** | Old failures never cleaned | Add expiry (90 days) or "RESOLVED" status |
| **Over-correction** | One typo → new rule | Require pattern confirmation |
| **Missing Postmortem** | Recurrence without analysis | BLOCKING: postmortem on 2nd occurrence |

---

## Recommended Improvements to Your System

### 1. Create failures-addressed.md

```bash
touch ~/.claude/reflections/failures-addressed.md
touch [repo]/.claude/reflections/failures-addressed.md
```

### 2. Add Promotion Pipeline to CLAUDE.md

```markdown
## Failure Promotion Pipeline

When reviewing failures.md (weekly):
1. Count occurrences per failure pattern
2. If count >= 2 AND pattern is clear:
   - Draft rule (negative constraint preferred)
   - Add to appropriate layer (CLAUDE.md vs .claude/rules/)
   - Move failure(s) to failures-addressed.md with MONITORING status
3. If count == 1: Leave in failures.md, add TRACKING tag
4. If failure recurs after rule added:
   - Write postmortem in failures-addressed.md
   - Analyze why rule didn't prevent recurrence
   - Update rule or escalate
```

### 3. Add Recurrence Detection

```markdown
## Recurrence Protocol (BLOCKING)

If failure matches a pattern already in failures-addressed.md:
1. STOP - This is a recurrence
2. Add postmortem to failures-addressed.md:
   - Original rule reference
   - Why it didn't prevent recurrence
   - Rule update needed
3. Update the original rule
4. Status → MONITORING (reset)
```

### 4. Weekly Curation Ritual

```markdown
## Weekly Failure Curation (suggested: Friday)

1. Read failures.md for past week
2. Group by pattern
3. For each pattern with 2+ occurrences:
   - Draft rule
   - Get Gemini review
   - Add to appropriate layer
   - Move to failures-addressed.md
4. For single occurrences: Tag as TRACKING
5. For patterns > 90 days without recurrence: Mark RESOLVED
```

---

## Reference Implementations

| Tool | Pattern | Learn From |
|------|---------|------------|
| **Aider** | `.aider.conf.yml` + auto-lint/test loops | Runtime correction |
| **Cursor** | `.cursorrules` path-scoped rules | Module memory |
| **claude-mem** | Session snapshots + summarization | Context bridging |
| **SWE-agent** | `.traj` trajectory capture | Full replay for debugging |
| **Copilot Memory** | 28-day TTL, citation validation | Anti-staleness |

---

## Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | Create `failures-addressed.md` | 5 min |
| **P0** | Add promotion pipeline to CLAUDE.md | 15 min |
| **P1** | Add recurrence detection protocol | 10 min |
| **P2** | Set up weekly curation ritual | 5 min |
| **P3** | Consider path-scoped rules (`.claude/rules/`) | 30 min |

---

## Key Insight

Your system **logs well but doesn't promote**. The gap is:

```
failures.md (you have) → ??? → CLAUDE.md rules (you have)
```

The missing `???` is:
1. **Repeat-count tracking** (when to promote)
2. **failures-addressed.md** (where to track promotions)
3. **Postmortem on recurrence** (why rule didn't work)

Fill that gap and your reflection system becomes a true learning loop.

---

## Sources

### Codebase Files
- [~/.claude/CLAUDE.md:95-132](~/.claude/CLAUDE.md#L95-L132) - Error Admission Tracking
- [.claude/reflections/failures.md](.claude/reflections/failures.md) - 2 logged failures

### External Sources
- Aider lint/test loop: https://aider.chat/docs/usage/lint-test.html
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Claude Code memory: https://code.claude.com/docs/en/memory
- SWE-agent trajectories: https://swe-agent.com/latest/usage/trajectories/
- Copilot Memory: https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/copilot-memory
- Continue rules: https://docs.continue.dev/customize/rules

### Agent Contributions
- **Opus**: Codebase exploration, gap analysis
- **Gemini**: Hierarchical memory model, immediate vs batch trade-offs
- **Codex**: Storage formats, two-lane pipeline, reference implementations

---

Reviewed by Gemini
