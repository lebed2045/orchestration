# Council deliberation: tidy command for working tree cleanup

think v1 (08-jun-2026)
Generated: 2026-06-13 17:04 WITA
Mode: default
Independence: inline separated passes
Persona card: /Users/elpinguino/.claude/USER.md
Gemini route: unavailable

## Synthesis

### Convergent view

The command is valuable, but the design should be framed as "produce a reversible clean tree" rather than "decide the final truth of every leftover file." The sharpest improvement is to make `/tidy` a local janitor that creates commits/stashes only after a plan, with deletion constrained to a tiny allowlist. Default mode should be deliberate. Fast mode should be reversible and boring.

Name: `/tidy` is the best fit. It pairs well with `/gardener`: gardener is seasonal deep cleanup; tidy is after-work cleanup. `/sweep` sounds too delete-heavy. `/triage` is accurate but clinical and implies diagnosis more than completion.

Taxonomy: the five buckets are mostly right, but `GITIGNORE` should not be a peer bucket to files. It is an action that may consume one or more files plus a `.gitignore` edit. Rename the operational buckets to `discard-junk`, `ignore-pattern`, `commit-main`, `commit-sidecar`, `stash-unclear`. The sidecar commit should not default to `chore:`; infer `docs:`, `test:`, `build:`, `ci:`, `refactor:` when obvious.

Safety: the biggest hole is not deletion. It is committing secrets, machine-local config, or accidental generated artifacts because a diff looks plausible. The command needs secret scanning, max-size/binary handling, `.env*` rules, and a human approval gate for any commit in default mode. Fast mode can skip Codex, but should not skip the final local plan unless explicitly told to.

Postcondition: "clean tree" is a valid command goal, but not for every mode. Make it hard for `--fast`, because that is the promise. In default mode, allow `--leave-unclear` or stop with a small unresolved list if the safer action is to not touch something like an actively edited `.env.local`. The default should still prefer named stash over leaving noise.

Ambiguity in fast mode: stash-everything is least surprising. WIP commits are too permanent and pollute history. Leave-in-place violates the command promise. Use a named stash such as `tidy: unclear leftovers <timestamp>` and include a recovery hint.

### Strongest dissenting take

This command risks becoming an agent that authors repository history from weak context. Splitting feature/chore commits after the fact is semantic work; automation can help, but it should not pretend it knows the user's intended main change unless the branch, recent commits, and diff point clearly in one direction. The default should maybe be "plan then ask" rather than "Codex verdict then execute."

### What might be wrong about the framing

The design assumes the dirty tree is mostly residue after agents finish. Sometimes it is the user's live scratchpad. A hard clean-tree postcondition can erase useful working context into stashes the user never revisits.

It also assumes commit grouping is reliably inferable from file diffs. In many repos, generated files, snapshots, lockfiles, migrations, and fixture updates are semantically tied to a feature even when they look orthogonal.

### Concrete next moves

1. Use `/tidy`.
2. Make default mode: inspect, classify, run Codex review, show plan, require confirmation before destructive actions or commits.
3. Make `--fast`: no Codex, no confirmation only if the operation is fully reversible except allowlisted junk deletion; ambiguous means named stash.
4. Add hard guards: never push, never amend unless explicit, no untracked secret-like files committed, no `.env*` committed by default, no binary/large files committed without explicit inclusion, no deletion outside allowlist.
5. Report final state as a table plus exact stash name and commit SHAs.

### Council provenance

No independent subagents were used because the available subagent tool requires explicit user authorization for delegation. No Gemini/Antigravity bridge was available through tool discovery. The persona card was found at `/Users/elpinguino/.claude/USER.md`, but it appears to be a template rather than substantive user context.

## Raw perspectives

### Perspective 1: First principles and steel-man

Suspect assumption: that a dirty tree can be classified purely by artifact type. The real primitive is reversibility under uncertainty.

Mechanically, the command observes paths, reads diffs, classifies intent, executes local actions, and proves the resulting tree state. The irreversible operations are deletion and commit history creation; the reversible operation is stash; the persistent policy operation is `.gitignore` modification.

Steel-man: the user does not want a report. They want an after-action cleanup command that can turn a messy agent run into an intentional repo state: junk gone, recurring junk ignored, meaningful work committed, side effects separated, uncertainty preserved.

Answer: the command is justified, but it should be designed around uncertainty and reversibility. `/tidy` is the right name because it promises practical cleanup without implying deep refactoring.

## What I might be wrong about

- The repo's existing `/gardener` semantics may make `/tidy` feel too cute if commands are otherwise literal.
- The user may prefer one-command execution over confirmation gates even in default mode.
- The current workflow culture may tolerate automated commits more than I assume.

### Perspective 2: Contrarian and inversion

Assume this fails in six months. The failure mode is likely not a single bad delete; it is a steady erosion of trust. Users run `/tidy`, then discover a sidecar commit mixed in something sensitive, a stash swallowed work they expected to see, or a `.gitignore` rule hid a legitimate future file.

The earliest signal would be users repeatedly running `git stash list`, `git reflog`, and `git show` after `/tidy` because they do not trust what happened.

Answer: default mode must be legible. The table is not decoration; it is the trust surface. Plans should include why each file was classified and whether the action is reversible. Fast mode can be terse only because its ambiguity policy is simple: stash.

## What I might be wrong about

- Overemphasizing trust may slow the command enough that users keep doing manual cleanup.
- If this is personal-only, a stricter confirmation model might feel like unnecessary friction.
- Some generated artifacts may be obvious enough that a broader delete allowlist is acceptable.

### Perspective 3: Expansionist and analogy

Analogy: an operating-room count at the end of a procedure. The goal is not to debate every instrument; it is to leave the room in a known safe state. Sharps have special handling, reusable tools return to trays, waste goes to a controlled bin, and uncertain items are escalated rather than guessed.

What transfers: strong categories, end-state proof, special handling for dangerous classes, and a bias toward quarantine for uncertain items.

What does not transfer: medical cleanup is more standardized than software diffs. A code file can be both a side effect and essential feature work depending on intent.

Answer: `/tidy` should be an end-of-run cleanup protocol. Stash is the quarantine bin. Delete is a locked sharps container with a small allowlist. Commits are the labeled trays and require high confidence.

## What I might be wrong about

- The analogy may overstate the danger of local commits, which are reversible with Git.
- It may understate the cost of stash sprawl.
- It may make the command sound procedural when the user wants a fast habit.
