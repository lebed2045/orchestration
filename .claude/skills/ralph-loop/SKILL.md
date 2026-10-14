---
name: ralph-loop
description: Fresh-context brute-force loop (Geoffrey Huntley's "Ralph Wiggum") — drive a checklist/PRD to completion by starting each iteration with a CLEAN context that re-derives state from git + filesystem + the checklist, never from prior reasoning. One item per iteration, commit every time, git is the memory. Use when the user runs /ralph-loop or wants long autonomous greenfield grind against a task list. Runs on a feature branch, never the default/protected branch (master/main).
---

# ralph-loop — fresh-context brute-force

**Updated:** `22-jun-2026`

**Charter:** Ralph's insight (named for the obliviously persistent cartoon kid): stop fighting context limits — *embrace* the fresh start. Each loop the agent wakes up with no memory of its last attempt and reconstructs everything from durable state: the checklist, the filesystem, and `git log`. State that matters gets committed; reasoning that doesn't get committed is meant to be forgotten. Crude, and it works for long unattended builds.

**Loop archetype:** brute-force restart loop. **Defaults:** 10 iterations; stop after 2 consecutive no-progress passes.

## Steps

1. **Guarantee a checklist + a branch.** Ensure a `PRD.md` / `TASKS.md` exists with discrete, independently-verifiable items, each with a "done when" line. Build it from `$ARGUMENTS` if absent. **Verify you're on a feature branch, not the default/protected branch (`master`/`main`)** — create one if needed. (Print the branch name before any commit.)

2. **Begin each iteration cold.** Do NOT carry reasoning from the previous pass. Read: the checklist, `git log --oneline -15`, and the relevant files. That — plus the working tree — is your entire memory.

3. **One item.** Pick the next unchecked item, implement only it, verify it against its "done when" (show the check), **tick its box in the checklist file, then commit the change and the ticked box together.** Order matters: the commit must already contain the checked box, or the next fresh pass re-does an item that was actually finished.

4. **Restart fresh.** Drop context and go to step 2 for the next item. Never assume what a prior iteration "intended" — re-derive it from files. *(In-session caveat: a model can't truly wipe its own context — approximate it by re-deriving strictly from files/`git log` and ignoring prior reasoning. For genuine fresh starts, use the headless form below — that's real Ralph.)*

5. **Stop** when: every item is checked (show the final green run), the iteration cap (10) is hit, or two iterations in a row check nothing new (stuck → escalate with the blocked item). Report items done / items left.

## The one guardrail that matters
**Commit every iteration; never run on the default/protected branch (`master`/`main`).** Git is the memory layer — an uncommitted iteration's work is lost on the next fresh start, and an unattended loop on a protected branch is how brute force becomes destruction.

## True headless Ralph (outside this session)
For a fully unattended run, the canonical form is a shell loop driving the agent until the checklist is clean:
```bash
for i in $(seq 1 50); do          # hard outer cap — brute force needs a fuse
  claude -p "Read PRD.md and git log. Do the next unchecked item, verify it, tick its box, then commit the change and ticked box together. If EVERY item is checked, write ALL-DONE to .ralph-status." \
    || break
  grep -q "ALL-DONE" .ralph-status 2>/dev/null && break
done
```
The prompt writes the sentinel to `.ralph-status` so the `grep` can actually see it. Run in a worktree/branch (never the protected branch), with a token budget, and `git` as the source of truth.

_Source: Geoffrey Huntley's Ralph Wiggum loop (devinterrupted interview); `github.com/snarktank/ralph` (PRD-driven loop)._
