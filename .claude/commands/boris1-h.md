# /boris1-h - 0-rev, 1-gate (Simple Organic)

> Based on how Boris actually uses Claude Code daily.
> Simple, practical, no over-engineering.

---

## Setup (One-Time)

**5 Parallel Instances**
Boris runs 5 Claude Code instances in separate git checkouts/worktrees:
```
~/repo-1  # Feature work
~/repo-2  # Testing
~/repo-3  # Code review
~/repo-4  # Debugging
~/repo-5  # Documentation
```

**Enable notifications** so you know when any session needs input.

---

## The Workflow

### Step 1: Plan Mode First

**Always start in Plan Mode** (`Shift+Tab` twice or say "enter plan mode").

```
1. Describe what you want to build
2. Claude drafts a plan
3. Iterate: "What about X?" / "Consider Y instead"
4. Keep refining until the plan is solid
```

> "A good plan is really important to avoid issues down the line"

**If work derails mid-implementation** → go back to Plan Mode, don't push forward.

---

### Step 2: Execute with Auto-Accept

Once plan is solid:
1. Exit Plan Mode
2. Enable auto-accept (`Shift+Tab` or `/auto`)
3. Let Claude implement
4. Claude uses subagents if needed:
   - `code-simplifier` — cleanup after completion
   - `verify-app` — test the implementation

---

### Step 3: Verify

**Boris's #1 tip:** Give Claude a way to verify its work. Quality improves 2-3x.

Verification methods:
- Run tests: `bun test` / `npm test`
- Type check: `tsc --noEmit`
- Build: `bun run build`
- Browser testing (Claude uses Chrome extension)
- Domain-specific: simulators, E2E, etc.

---

### Step 4: Commit

Use `/commit-push-pr` or similar slash command.

---

## Key Principles

| Principle | Implementation |
|-----------|----------------|
| Plan first | Always start in Plan Mode |
| Iterate the plan | Don't accept first draft |
| Verify everything | Tests, builds, type checks |
| Learn from mistakes | Add errors to CLAUDE.md |
| Modular agents | Subagents for specific tasks |
| Pre-allow safe commands | `/permissions Bash(bun test:*) --allow` |

---

## CLAUDE.md as Memory

Update CLAUDE.md constantly:
- When Claude does something wrong → add correction
- Style preferences → add rule
- Past mistakes → add to `## Past Mistakes` section

> "Anytime we see Claude do something incorrectly we add it to the CLAUDE.md"

This creates **Compounding Engineering** — Claude gets better over time.

---

## Subagents (in .claude/agents/)

| Agent | Purpose |
|-------|---------|
| `code-simplifier.md` | Simplify code after implementation |
| `verify-app.md` | E2E testing instructions |
| `oncall-guide.md` | On-call processes |

Call subagents when needed, not as forced phases.

---

## PostToolUse Hook

Auto-format after every edit:
```json
"PostToolUse": [{
  "matcher": "Write|Edit",
  "hooks": [{"type": "command", "command": "bun run format || true"}]
}]
```

---

## MCP Integrations (optional)

Configure in `.mcp.json`:
- Slack — search/post messages
- BigQuery — data queries
- Sentry — error logs

Tools don't consume context until invoked.

---

## What Boris Does NOT Do

- No rigid phase gates
- No mandatory review loops
- No complex state tracking
- No forced TDD ceremony
- No EXECUTION_BLOCK proof requirements

**He keeps it simple:** Plan → Execute → Verify → Commit

---

## User's Task

$ARGUMENTS
