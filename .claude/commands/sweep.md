---
description: "Sweep the working tree after agents finish: classify every uncommitted path into discard/ignore/commit-main/commit-sidecar/stash/hold, then execute so the tree ends clean. Codex consult ON by default (--fast / --no-codex to skip). Never pushes; local commits only; secrets are hard-fenced from auto-commit."
argument-hint: "[--fast] [--no-codex] [--dry-run] [freeform hint]"
---

# /sweep — Working-Tree Sweep

Companion to `/gardener`. `/gardener` is periodic **deep** entropy removal across the whole repo; `/sweep` is the quick **end-of-session** pass over whatever the agents left uncommitted — it reads each leftover file, decides what it is, and disposes of it so `git status` ends clean.

**First line of every run, verbatim:** `sweep (19-jun-2026)`.

The job that used to be "hey, what are these files?" → read each one → delete / gitignore / commit / separate-chore-commit / stash, every time. This is that loop as one command.

## Usage

```text
/sweep [flags] [freeform hint]
```

**Default behavior (no flags):** classify every uncommitted path → **Codex verdict on the plan** → execute autonomously → prove the tree is clean. No human gate (you chose autonomous). Safety fences below are always on, independent of any verdict.

| Flag | Effect | Default? |
|---|---|---|
| `-c` | Codex consult on the disposition plan before executing (`mcp__codex-cli__codex`) | **DEFAULT ON** |
| `--no-codex` | Skip the Codex consult; classify and execute with normal verbosity | opt-in |
| `--fast` / `-f` | The "just make it clean, now" path: implies `--no-codex`, terse output, **bias hard toward STASH** for anything not dead-obvious. Clean tree is a hard postcondition. | opt-in |
| `--dry-run` / `-n` | Classify and print the plan only — touch nothing | opt-in |
| `--no-delete` | Never `rm`; route everything that would be DISCARD to STASH instead | opt-in |

A freeform hint after the flags (e.g. `the auth refactor is the main change`) biases the MAIN-vs-SIDECAR split — it is advisory, never overrides a safety fence.

**Never pushes. Local commits only, on the current branch.** Secrets are hard-fenced from auto-commit (HOLD bucket) regardless of mode or verdict.

## Flag detection (tokenized — word-boundary safe)

```bash
CODEX=true; FAST=false; DRY_RUN=false; NO_DELETE=false; HINT_TOKENS=()
set -f                              # noglob: a hint token like `*.ts` must not glob-expand during the parse
for tok in $ARGUMENTS; do
  case "$tok" in
    /sweep) ;;
    -c|-C)               CODEX=true ;;
    --no-codex)          CODEX=false ;;
    --fast|-f)           FAST=true ;;
    --dry-run|-n)        DRY_RUN=true ;;
    --no-delete)         NO_DELETE=true ;;
    *)                   HINT_TOKENS+=("$tok") ;;
  esac
done
set +f
[ "$FAST" = true ] && CODEX=false   # enforce AFTER the loop so `--fast -c` cannot re-enable Codex (last-word safety, not last-word wins)
HINT="${HINT_TOKENS[*]}"
echo "CODEX=$CODEX  FAST=$FAST  DRY_RUN=$DRY_RUN  NO_DELETE=$NO_DELETE"
[ -n "$HINT" ] && echo "HINT: $HINT"
```

## Phase 0: Snapshot + clean-tree early exit

```bash
echo "branch: $(git rev-parse --abbrev-ref HEAD)   HEAD: $(git rev-parse --short HEAD)"
BASELINE_SHA=$(git rev-parse HEAD)
# -uall enumerates untracked files INSIDE untracked dirs individually (not collapsed to `dir/`),
# so a child secret like `scratch/.env` is visible to the HOLD fence instead of hiding under `scratch/`.
PORC=$(git status --porcelain=v1 -uall)
if [ -z "$PORC" ]; then echo "working tree already clean — nothing to sweep."; exit 0; fi
echo "== uncommitted leaf paths (XY = index/worktree status) =="; printf '%s\n' "$PORC"
git stash list | tail -3   # existing stashes, so new sweep stashes are distinguishable
```

If the tree is clean, stop here — do not manufacture work. **Classify the leaf paths from `-uall`, never a collapsed directory** — a directory is never a commit unit (see the invariant in Phase 1).

## Phase 1: Classify (read each path, assign exactly one bucket)

For **every** path in `git status --porcelain` (staged and unstaged), inspect it — read the file or its diff (`git diff -- <path>`, or the content if untracked) — and assign **exactly one** bucket. Apply the **HOLD fence first**: it wins over every other bucket.

| Bucket | What lands here | Action at execute time |
|---|---|---|
| 🔒 `HOLD` | Secrets / machine-local state: `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12/.pfx`, `id_rsa*`, `*.keystore`, `*credential*`, `*secret*`, files with secret-looking high-entropy content, binaries larger than ~5 MB | **Never committed.** STASH it (reversible, stays local) and flag it loudly. The fence is independent of the Codex verdict. |
| `DISCARD` | Allowlisted junk **only** — untracked or trivially regenerable: `.DS_Store`, `Thumbs.db`, `*.swp/.swo`, `*~`, `*.orig`, `*.rej`, `*.bak`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, zero-byte scratch, files under known scratch dirs (`.claude/temp/`, `codex/temp/`, `*/tmp/`) | `rm`. Never a tracked source file's edits; never anything off this allowlist. With `--no-delete`, downgrade to STASH. |
| `IGNORE` | Regenerable / machine-local recurring artifacts not yet ignored: `node_modules/`, `dist/`, `build/`, `target/`, `.venv/`, `coverage/`, IDE dirs, recurring caches/logs | Append a `.gitignore` rule (+ `git rm --cached <path>` if currently tracked); the `.gitignore` change rides its own `chore:` commit. |
| `COMMIT-MAIN` | The dominant change — the largest coherent group (src + its tests) that forms the primary feature/fix this session | One commit, conventional message, inferred type. |
| `COMMIT-SIDECAR` | Files that only **lightly** depend on the main change: a README tweak, a config bump, a metrics/ledger file, an unrelated typo fix, a new helper script, formatting-only edits | A **separate** commit per coherent sidecar group, type **inferred** (not hardcoded `chore`): `docs:` for `*.md`, `test:` for `*test*/*spec*`, `ci:` for `.github/`/CI configs, `build:` for dep/build files, `style:` for whitespace/format-only, else `chore:`. |
| `STASH` | Genuinely unclear — possibly half-finished work, intent ambiguous, can't confidently bucket | `git stash push -u -m "sweep/unclear <ts>" -- <paths>`. Reversible; reported. |

**Heuristic notes:**
- **MAIN vs SIDECAR** is the call the user makes by hand every time. MAIN = the change the session was *about*. SIDECAR = "this happens to be in the tree but doesn't belong in the feature commit." Use the freeform `$HINT` to disambiguate when given. When in doubt between MAIN and SIDECAR, prefer SIDECAR (a focused feature commit is the goal).
- **`--fast` bias:** anything not dead-obvious (clear junk, clear secret, clear single coherent feature group) goes to STASH. Don't agonize over grouping in fast mode — clean the tree, keep everything reversible.
- Never invent a classification for a file you couldn't read — if inspection fails, it is `STASH` by definition.
- **A directory is never a commit unit.** Commits operate on the leaf files from `-uall`. A directory only ever maps to `IGNORE` (a `.gitignore` rule) or `DISCARD` (an allowlisted junk dir like `__pycache__/`). This closes the path where committing `dir/` would sweep a child secret into history.

Emit the plan as a table (`<path> → <bucket> → <commit-type/dest>`) so the disposition is visible before anything executes.

## Phase 2: Codex verdict on the plan (default; skipped by `--fast` / `--no-codex`)

If `CODEX=true`: send the **disposition plan** (the path→bucket table + one-line rationale each) to `mcp__codex-cli__codex`, prompt ending:
`Review this working-tree disposition plan for a cleanup command. Flag anything unsafe — especially any file that should be HOLD (secret/machine-local) but is slated to commit, any DISCARD that isn't obvious junk, and any MAIN/SIDECAR split that buries an unrelated change in the feature commit. End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>.`

- **APPROVED** → execute.
- **NEEDS_WORK** → since the run is autonomous, **act on the reason yourself**: downgrade any flagged item to the *safe* bucket (HOLD or STASH — never escalate toward commit/delete on a warning), then re-verify. Max **2** Codex iterations, then proceed with the safety-biased plan. A safety flag from Codex can only ever move an item toward STASH/HOLD, never toward commit.
- **Codex MCP missing or no reply within 5 min** → print `CODEX REVIEW SKIPPED - MCP missing` (or `... - timeout >5m`), proceed without it. The HOLD/DISCARD/STASH fences still hold; they are the real safety boundary, not the verdict.

Model + reasoning effort inherit from `~/.codex/config.toml` — do not override.

## Phase 3: Execute (ordered; skipped entirely under `--dry-run`)

Under `--dry-run`: print the plan and stop — touch nothing.

Otherwise execute in this order (safe-first). **Step 0 — empty the index once: `git reset -q`** (unstages everything; the worktree is untouched). This is what makes commits airtight: because the index starts empty and each commit below stages **only its own bucket** (`git add -- <group> && git commit -m …`), a pre-staged unrelated path can never leak into the wrong commit (`git commit` commits the whole index, so the empty-start + add-only-this-group discipline is mandatory).

1. **HOLD** 🔒 → `git stash push -u -m "sweep/sensitive <ts>" -- <hold-leaf-paths>`. Print a loud `🔒 HELD (not committed): <paths> → stash sweep/sensitive` line. Never committed, ever — independent of the Codex verdict.
2. **DISCARD** → `rm -f -- <file>` for junk files, `rm -rf -- <allowlisted-dir>` for allowlisted junk dirs (`__pycache__/`, `.pytest_cache/`) — allowlist-checked, one path at a time, `--` guards dash-leading names. Under `--no-delete`, route to the unclear stash instead. List exactly what was removed.
3. **IGNORE** → append each rule to `.gitignore`; for any tracked-but-now-ignored path use `git rm -r --cached -- <path>` (`-r` handles `dist/`, `node_modules/`; `--` handles dash-leading names); then `git add -- .gitignore && git commit -m "chore(gitignore): ignore <summary>"`.
4. **COMMIT-MAIN** → `git add -- <main-leaf-paths> && git commit -m "<inferred conventional message>"`.
5. **COMMIT-SIDECAR** → for each coherent sidecar group, a **separate** `git add -- <group-leaf-paths> && git commit -m "<inferred type>: …"`.
6. **STASH** → `git stash push -u -m "sweep/unclear <ts>" -- <unclear-leaf-paths>`.

Every commit `/sweep` creates ends with this exact trailer as its final line (fill `<model>` with the real session model id; omit `-<effort>` if effort is unknown — never guess it):

```text
Assisted-by: sweep<flags> <model>[-<effort>]
```

where `<flags>` echoes the active flags (e.g. ` -c`, ` --fast`). **Never `git push`. Never commit a HOLD path.**

## Phase 4: Verify + report

```bash
RESIDUE=$(git status --porcelain=v1 -uall)
if [ -n "$RESIDUE" ]; then
  echo "ANOMALY: tree not clean after execute — failing closed by stashing residue:"; printf '%s\n' "$RESIDUE"
  git stash push -u -m "sweep/residue $(date +%Y%m%dT%H%M%SZ)"   # reversible — keeps the clean-tree promise, loses nothing
fi
echo "== final tree =="; git status --porcelain=v1 -uall
echo "== sweep commits =="; git log --oneline "$BASELINE_SHA"..HEAD
echo "== new stashes =="; git stash list | grep -E 'sweep/(unclear|sensitive|residue)' || echo "(none)"
```

The clean-tree postcondition is **enforced, not just checked**: if anything survives the execute phase, fail closed by stashing it (`sweep/residue` — reversible, nothing lost) so the promise holds, then report the anomaly to investigate. Only claim a clean tree when the final `git status --porcelain -uall` is provably **empty**; if even the residue stash leaves something, stop and report `tree clean: no` with the exact remainder — never assert clean without the empty status.

Print a final **disposition table**: each path → bucket → outcome (commit SHA / stash ref / removed), plus recovery hints (`git stash pop <ref>` to restore, `git reset --soft HEAD~N` to unwind commits). End with `SWEEP COMPLETE — tree clean: <yes/no>`.

## Safety invariants (always on, every mode)

- A **HOLD** path is **never** committed — secrets/machine-local state only ever get stashed (reversible, local) or left, never written to history.
- **DISCARD** is restricted to the junk allowlist; nothing off-allowlist is ever `rm`'d. Ambiguity routes to **STASH** (reversible), never to delete.
- **Never `git push`**; never touch remotes; commits are local to the current branch.
- The Codex verdict is a second opinion, **not** a safety boundary — a missing/timed-out Codex never widens what `/sweep` is allowed to delete or commit.
- `--dry-run` touches nothing.

$ARGUMENTS
