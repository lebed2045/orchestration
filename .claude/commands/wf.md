# /wf — Fast-Iteration TDD (Tier-Auto, Split-TDD, No-Worktree Default)

**WF_VERSION:** `v16` · **WF_COMMITTED:** `26-may-2026` · **Tag:** `[tier-auto | split-tdd | optional MCP | rewind-discard | no-auto-commit]`

**First line of every run must be, verbatim:** `wf v16 (26-may-2026)` — derived from the two values above. Bump both when the workflow body changes meaningfully.

`-g` = Antigravity CLI (`agy -p`, Gemini-MCP successor; Gemini CLI sunsets 2026-06-18). `-c` = Codex MCP. No-flag default: tier-auto, split TDD, no worktree, no reviewers, no gate, no commit.

## Usage

```text
/wf [flags] <task>
```

**Default behavior (no flags):** `tier=auto` (heuristic) · `split-tdd` · `no-worktree` · no MCP · no human gate · no auto-commit · MCP downgrade allowed.

| Flag | Effect | Default? |
|---|---|---|
| `--tier=auto` | Heuristic picks micro/small/full from task text | **DEFAULT** |
| `--tier=micro` | 1-line/comment/rename — skip plan mode, no cops, no gates | |
| `--tier=small` | 1-file feature/fix — optional plan mode, coverage-cop only | |
| `--tier=full` | Multi-file feature — plan mode + 3 cops + (optional) worktree | |
| `--split-tdd` | TWO zero-context agents: RED then GREEN | **DEFAULT** |
| `--unified-tdd` | ONE agent does RED+GREEN in SAME context (steipete catch-rate) | |
| `--no-worktree` | Work on current branch | **DEFAULT** |
| `--worktree` | Force-create isolated git worktree (steipete-counter: only when you want it) | |
| `-c` | Add Codex MCP reviewer at both gates | opt-in |
| `-g` | Add Antigravity CLI reviewer (`agy -p`) at both gates — successor to Gemini MCP (Gemini CLI sunsets 2026-06-18) | opt-in |
| `-h` | Human gate via `AskUserQuestion` after RED | opt-in |
| `--commit` | ff-only merge to main on success | opt-in |
| `--allow-mcp-downgrade` | Continue if requested reviewer is missing (Codex MCP or `agy` binary) | **DEFAULT** (was abort in v16.1) |
| `--abort-on-missing-mcp` | Old behavior: abort if `-c` Codex MCP or `-g` `agy` binary is missing | opt-in |
| `--cops-model=<m>` | Override cop model (default: inherit session model) | opt-in |
| `--coder-model=<m>` | Override coder model (default: inherit session model) | opt-in |
| `--effort=<level>` | Reasoning effort (default: inherit session setting) | opt-in |
| `--goal "<criterion>"` | Append explicit success contract to GREEN agent prompt (Boris `/goal` pattern) | opt-in |
| `--dry-run` | Stop after Phase 4. Print plan, no code touched | opt-in |

**Combinable.** Examples:
- `/wf fix typo in README` → auto picks `micro` → 1 agent, no worktree, no ceremony
- `/wf implement email validator` → auto picks `small` → 1 split-TDD pair + coverage cop
- `/wf implement OAuth refresh flow` → auto picks `full` → split TDD + 3 cops, still no worktree unless `--worktree`
- `/wf --tier=full --worktree -cg --commit implement payment flow` → kitchen sink

---

## Tier Matrix

| Tier | Phases active | Coders | Cops | Plan Mode | Worktree | MCP |
|---|---|---|---|---|---|---|
| micro | 1, 2, 5+6, 7, 9 | 1 (split or unified) | 0 (skip Phase 8) | skip | no (forced) | ignored even if `-c -g` |
| small | 1, 2, 3, 4, 5+6, 7, 8 (coverage only), 9 | 1 pair (split default) | 1 (coverage) | optional (active only if `-h`) | no (opt-in via `--worktree`) | optional |
| full | All 9 phases | 1 pair (split default) | 3 | optional (active only if `-h`) | no (opt-in via `--worktree`) | optional |

**Tier resolution order:**
1. Explicit `--tier=X` wins
2. Default tier: `auto` — heuristic scans task text (see `detect_tier_auto` in Flag Detection)
3. Conflicts: `--tier=micro --commit` → still ff-merges if green; `--tier=micro -c` → MCP flag silently ignored; missing MCP → continue without (default) unless `--abort-on-missing-mcp` passed

---

## Flag Detection (Tokenized — word-boundary safe)

```bash
# v16.2 defaults: tier=auto, split-tdd, no-worktree, no MCP, no human gate, MCP downgrade allowed
TIER="auto"
HUMAN_GATE=false
CODEX_REVIEW=false
AGY_REVIEW=false                    # `-g` flag: Antigravity CLI (`agy -p`), Gemini-MCP successor
AUTO_COMMIT=false
ALLOW_MCP_DOWNGRADE=true            # default flipped vs v16.1
ABORT_ON_MISSING_MCP=false          # opt-in to revert to v16.1 strict behavior
UNIFIED_TDD_OVERRIDE=""             # "" → tier-agnostic default = split
USE_WORKTREE_OVERRIDE=""            # "" → universal default = no
DRY_RUN=false
GOAL=""
COPS_MODEL=""                       # "" → inherit session model
CODER_MODEL=""
EFFORT=""
TASK_TOKENS=()

for tok in "$@"; do
  case "$tok" in
    /wf) ;;
    --tier=auto|--tier=micro|--tier=small|--tier=full) TIER="${tok#--tier=}" ;;
    --unified-tdd) UNIFIED_TDD_OVERRIDE="unified" ;;
    --split-tdd)   UNIFIED_TDD_OVERRIDE="split" ;;
    --no-worktree) USE_WORKTREE_OVERRIDE="no" ;;
    --worktree)    USE_WORKTREE_OVERRIDE="yes" ;;
    --commit)                AUTO_COMMIT=true ;;
    --allow-mcp-downgrade)   ALLOW_MCP_DOWNGRADE=true ;;
    --abort-on-missing-mcp)  ABORT_ON_MISSING_MCP=true; ALLOW_MCP_DOWNGRADE=false ;;
    --dry-run)               DRY_RUN=true ;;
    --cops-model=*)          COPS_MODEL="${tok#--cops-model=}" ;;
    --coder-model=*)         CODER_MODEL="${tok#--coder-model=}" ;;
    --effort=*)              EFFORT="${tok#--effort=}" ;;
    --goal=*)                GOAL="${tok#--goal=}" ;;
    --goal)                  GOAL="__NEXT_TOKEN__" ;;  # collected below
    -h|-H) HUMAN_GATE=true ;;
    -c|-C) CODEX_REVIEW=true ;;
    -g|-G) AGY_REVIEW=true ;;
    -[cghCGH][cghCGH]*)
      [[ "$tok" == *[cC]* ]] && CODEX_REVIEW=true
      [[ "$tok" == *[gG]* ]] && AGY_REVIEW=true
      [[ "$tok" == *[hH]* ]] && HUMAN_GATE=true
      ;;
    *)
      if [ "$GOAL" = "__NEXT_TOKEN__" ]; then GOAL="$tok"
      else TASK_TOKENS+=("$tok"); fi
      ;;
  esac
done
TASK="${TASK_TOKENS[*]}"

# === Tier auto-detection (heuristic) ===
detect_tier_auto() {
  local task="$1"
  local word_count=$(echo "$task" | wc -w | tr -d ' ')
  local lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

  # MICRO: trivial verbs OR short task without ceremony verbs
  if [[ "$lower" =~ ^(fix[[:space:]]+typo|rename|add[[:space:]]+comment|update[[:space:]]+copy|change[[:space:]]+text|fix[[:space:]]+the[[:space:]]+typo|bump[[:space:]]+version) ]]; then
    echo "micro"; return
  fi
  if [ "$word_count" -le 6 ] && [[ ! "$lower" =~ (implement|refactor|migrate|build|integrate) ]]; then
    echo "micro"; return
  fi

  # FULL: big-scope verbs OR long multi-clause task
  if [[ "$lower" =~ (implement|refactor|migrate|integrate|build[[:space:]]+.*flow|.*[[:space:]]and[[:space:]].*[[:space:]]and[[:space:]].*) ]]; then
    echo "full"; return
  fi
  if [ "$word_count" -gt 12 ]; then
    echo "full"; return
  fi

  # FALLBACK: small
  echo "small"
}

if [ "$TIER" = "auto" ]; then
  RESOLVED_TIER=$(detect_tier_auto "$TASK")
  echo "AUTO-DETECT: '$TASK' → tier=$RESOLVED_TIER"
  TIER="$RESOLVED_TIER"
fi

# === Resolve tier-dependent settings ===
# v16.2: default TDD = split for all tiers (was unified for micro/small in v16.1)
# v16.2: default worktree = NO for all tiers (was yes for small/full in v16.1)
case "$TIER" in
  micro)
    UNIFIED_TDD="${UNIFIED_TDD_OVERRIDE:-split}"
    USE_WORKTREE="${USE_WORKTREE_OVERRIDE:-no}"
    CODEX_REVIEW=false; AGY_REVIEW=false   # micro ignores reviewer flags
    SKIP_PLAN_MODE=true; SKIP_COPS=true; SKIP_GATE1=true; SKIP_GATE2=true
    ;;
  small)
    UNIFIED_TDD="${UNIFIED_TDD_OVERRIDE:-split}"
    USE_WORKTREE="${USE_WORKTREE_OVERRIDE:-no}"
    SKIP_PLAN_MODE=false; ACTIVE_PLAN_MODE=$HUMAN_GATE
    COPS_SUBSET="coverage"
    ;;
  full)
    UNIFIED_TDD="${UNIFIED_TDD_OVERRIDE:-split}"
    USE_WORKTREE="${USE_WORKTREE_OVERRIDE:-no}"   # opt-in even for full
    SKIP_PLAN_MODE=false; ACTIVE_PLAN_MODE=$HUMAN_GATE   # EnterPlanMode is interactive; only invoke with -h
    COPS_SUBSET="all"
    ;;
esac

echo "TIER=$TIER  TDD=$UNIFIED_TDD  WORKTREE=$USE_WORKTREE  HUMAN=$HUMAN_GATE  C=$CODEX_REVIEW  G=$AGY_REVIEW  COMMIT=$AUTO_COMMIT  DRY_RUN=$DRY_RUN"
[ -n "$GOAL" ] && echo "GOAL: $GOAL"
[ -n "$COPS_MODEL$CODER_MODEL$EFFORT" ] && echo "MODEL_OVERRIDES: cops=$COPS_MODEL coder=$CODER_MODEL effort=$EFFORT"
echo "TASK: $TASK"
```

**Word-boundary safety:** Flag parser tokenizes on whitespace; words like `force-commit`, `--commitment`, `-guide`, `-gpu` are NOT misread as flags.

**Heuristic transparency:** `auto` always prints the resolved tier (`AUTO-DETECT: '<task>' → tier=<X>`) so the user can override with `--tier=Y` on a re-run if the guess was wrong.

---

## Preflight: Reviewer Availability Check (Phase 0)

**Skip if both `CODEX_REVIEW=false` AND `AGY_REVIEW=false`** (always true for micro tier).

```text
# -c (Codex MCP) — tool-namespace check
ToolSearch({query: "select:mcp__codex-cli__codex,mcp__codex-cli__review", max_results: 2})

# -g (Antigravity CLI) — binary presence check (NOT an MCP; agy is a subprocess like `claude -p`)
command -v agy >/dev/null && agy --version
```

Antigravity CLI (`agy`) replaces the Gemini MCP path. Gemini CLI / Gemini Code Assist IDE stops serving AI Pro/Ultra requests on 2026-06-18 — Antigravity CLI is Google's named successor (binary installs to `~/.local/bin/agy`; install via `curl -fsSL https://antigravity.google/cli/install.sh | bash`).

On MISSING: ABORT by default; `--allow-mcp-downgrade` continues with the missing flag forced false. For `-g`, "missing" means `command -v agy` returns non-zero.

---

## Phase 1: CONTEXT_CAPTURE + TodoWrite + Hook Reminder

**Create TodoWrite with these items (tier-aware — micro has 4, small has 7, full has 9):**

| # | Item (full tier) | micro | small |
|---|---|---|---|
| 1 | MCP preflight check | ✓ (skip if no MCP flag) | ✓ | ✓ |
| 2 | Context capture | ✓ | ✓ | ✓ |
| 3 | Intake (spec.md) | ✓ | ✓ | ✓ |
| 4 | Planning (architecture.md) + plan-mode gate | skip | optional | ✓ |
| 5 | Gate 1/2: Plan review | skip | skip (unless `-h`) | ✓ |
| 6 | TDD (unified or split) | ✓ (unified) | ✓ | ✓ |
| 7 | Final verification (+7b if needed) | ✓ | ✓ | ✓ |
| 8 | Gate 2/2: Code review | skip | partial (coverage-cop only) | ✓ |
| 9 | Completion (merge if `--commit`) | ✓ | ✓ | ✓ |

**Hook recommendation (printed at end of Phase 1):**

```bash
HOOKS_INSTALLED=$(jq -r '.hooks // {} | length' .claude/settings.json 2>/dev/null || echo 0)
if [ "$HOOKS_INSTALLED" = "0" ]; then
  echo "[INFO] No hooks configured. Recommended for deterministic enforcement:"
  echo "  - Stop hook: block exit unless EXIT_CODE=0 line is present"
  echo "  - PostToolUse(Edit) hook: auto-format on every write"
  echo "  - SessionStart hook: inject git SHA + branch + TEST_CMD"
  echo "Run /wf-install-hooks (sibling command) to add them. Hooks are advisory; workflow proceeds either way."
fi
```

**Context capture (same as v1):** record git SHA, branch, MAIN_REPO path, dirty tree, auto-detect TEST_CMD/TEST_FILTER. Emit CONTEXT_BLOCK.

---

## Phase 2: INTAKE (Autonomous, all tiers)

Same as v1. Write spec → `.claude/temp/spec.md`. For micro tier, spec can be a 3-line note.

---

## Phase 3: PLANNING (Plan-Mode invoked only with `-h`; skip micro)

**If `SKIP_PLAN_MODE=true` (micro tier):** Write a stub architecture.md with just the Quick Test section. Skip Phase 4 entirely. Jump to Phase 5.

**Otherwise (small or full):**

### Step 1: Enter Plan Mode (only if `ACTIVE_PLAN_MODE=true`, i.e. `-h` was passed)

```text
if [ "$ACTIVE_PLAN_MODE" = "true" ]; then
  EnterPlanMode   // Claude Code primitive — interactive UI gate, requires user "approve plan" click to exit
fi
```

For autonomous runs (no `-h`), do NOT call `EnterPlanMode`. The "no source edits during planning" discipline is enforced by procedure: write `architecture.md` first; touch no source until Phase 5.

### Step 2: Write architecture.md

`.claude/temp/architecture.md` requires:
- Component design (minimal files)
- **Reuse existing patterns** (enumerated)
- **File structure**, with EACH new file declared as: `- New: path/to/file.ext — justification: <reason>` (parser will enforce)
- TDD test plan
- **Quick Test section** (Type, Test file(s), Filter, Run command, Rationale)

### Step 3: User Edit Gate (only if `ACTIVE_PLAN_MODE=true`, i.e. `-h`)

```text
if [ "$ACTIVE_PLAN_MODE" = "true" ]; then
AskUserQuestion({
  questions: [{
    question: "Plan written to .claude/temp/architecture.md. Edit in your editor (Ctrl+G to open), then choose:",
    header: "Plan gate",
    options: [
      {label: "Approve plan", description: "Continue to Gate 1/2 plan review and TDD."},
      {label: "I edited the plan — re-read and approve", description: "Orchestrator re-reads architecture.md before continuing."},
      {label: "Abort", description: "Discard, exit."}
    ]
  }]
})
fi
```

For autonomous runs (no `-h`), this prompt is skipped AND `EnterPlanMode` itself is not called. `EnterPlanMode` is a Claude Code primitive that always gates on a user "approve plan" click — there is no orchestrator-side bypass — so it is invoked only when the user has opted in to a human gate via `-h`.

### Step 4: File-Count Check (deterministic)

```bash
PLANNED_NEW=$(grep -c '^- New: ' .claude/temp/architecture.md 2>/dev/null || echo 0)
JUSTIFIED=$(grep -c '^- New: .* — justification: ' .claude/temp/architecture.md 2>/dev/null || echo 0)
if [ "$PLANNED_NEW" -gt 5 ] && [ "$JUSTIFIED" -lt "$PLANNED_NEW" ]; then
  echo "STOP: $PLANNED_NEW new files, $JUSTIFIED justified. Consolidate."
  exit 1
fi
```

### Step 5: Exit Plan Mode (only if Step 1 entered it)

```text
if [ "$ACTIVE_PLAN_MODE" = "true" ]; then
  ExitPlanMode   // Edits now permitted
fi
```

---

## Phase 4: GATE 1/2 — PLAN_REVIEW (Skip for micro; optional small; required full)

**If `SKIP_GATE1=true`:** Skip entirely.

Otherwise: same as v1 (self-review + optional external reviewers). For `small` tier without `-c -g`, only the self-review checklist runs.

### Reviewer invocation reference

| Flag | Surface | Invocation pattern |
|---|---|---|
| `-c` | MCP tool call | `mcp__codex-cli__review` (or `mcp__codex-cli__codex` for free-form ask) |
| `-g` | CLI subprocess | `agy -p --print-timeout 5m0s "<prompt>"` (run via Bash tool; capture stdout; parse for `APPROVED` / `NEEDS_WORK`) |

For `-g`: prepend the reviewer prompt with explicit verdict instructions, e.g. `"... End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>."` Orchestrator greps the last line for the verdict token. Typical latency: 30–60s per call; budget accordingly.

Aggregate block:

```text
┌─────────────────────────────────────────────┐
│ [4/9] GATE 1/2 (Plan Review)                │
├─────────────────────────────────────────────┤
│ Self-review: [PROCEED|REVISE]               │
│ Codex:       [APPROVED|NEEDS_WORK|N/A]      │
│ Antigravity: [APPROVED|NEEDS_WORK|N/A]      │
│ GATE STATUS: [PASS|BLOCKED]                 │
└─────────────────────────────────────────────┘
```

---

## Phase 5+6: TDD — Split or Unified

**Branch on `$UNIFIED_TDD`:**

### Variant A: SPLIT (`UNIFIED_TDD=split` — **default for all tiers in v16.2**)

Two zero-context agents. Phase 5 RED agent writes the failing test + commits. Phase 6 GREEN agent implements until the test passes + commits. Both run in `$WT_PATH` if `USE_WORKTREE=yes`, otherwise on current branch.

**Phase 5 (RED) Agent:**

```text
Agent({
  description: "Write failing quick test",
  subagent_type: "general-purpose",
  isolation: <"worktree" if USE_WORKTREE=yes; omit otherwise>,
  name: "tdd-red",
  // model + effort: inherit session unless --coder-model / --effort overrides
  prompt: <RED prompt — write test, run, must fail, commit "test: <feature> (RED)">
})
```

**Phase 6 (GREEN) Agent:**

```text
Agent({
  description: "Implement until quick test passes",
  subagent_type: "general-purpose",
  isolation: <omit if same-worktree continuation; or "worktree" for fresh>,
  name: "tdd-green",
  prompt: <GREEN prompt — see below, includes --goal if set>
})
```

GREEN agent prompt (with `--goal` interpolation):

```text
You are a TDD implementer in <worktree $WT_PATH | current branch>.

Read: .claude/temp/spec.md, .claude/temp/architecture.md, the RED-phase test files.

Quick test command: $QUICK_TEST_CMD

INNER LOOP (max 5 iterations, orchestrator enforces from your structured log):
  GREEN_ITER N/5: cmd=<cmd> exit=<code> error="<one-line or 'none'>"

When the quick test passes, commit `feat: <feature> (GREEN)`.

<<additional success contract (only if --goal was passed)>>
$GOAL
You must satisfy this contract IN ADDITION to the quick test passing.
Verify each clause before declaring GREEN.

FORBIDDEN: Running '$TEST_CMD' (full suite). Only '$QUICK_TEST_CMD'.
```

### Variant B: UNIFIED (`UNIFIED_TDD=unified` — opt-in via `--unified-tdd`)

**Rationale (steipete pattern):** "The model almost always finds issues when you ask it to write tests IN THE SAME CONTEXT as the implementation." One agent, one context, RED→GREEN sequence visible to itself. Higher catch rate, less honest separation between test author and implementer.

**Spawn ONE Agent:**

```text
Agent({
  description: "Unified TDD: write failing test, then implement until pass",
  subagent_type: "general-purpose",
  isolation: <"worktree" if USE_WORKTREE=yes; omit otherwise>,
  name: "tdd-unified",
  prompt: <unified prompt — RED then GREEN sequence, includes --goal if set>
})
```

Unified prompt structure:
- ENV_BLOCK (pwd + branch) first
- RED phase: write test → run → must fail → commit "test: (RED)" → emit RED_ITER log
- GREEN phase: implement → loop max 5 → must pass → commit "feat: (GREEN)" → emit GREEN_ITER log
- If `$GOAL` set, append: `Additional success contract: $GOAL — must satisfy in addition to quick test passing.`
- FORBIDDEN: running `$TEST_CMD` (full suite). Only the quick test command.

After agent returns (either variant), capture `WT_PATH` (if worktree), `QUICK_TEST_CMD`, `TEST_FILES`. Verify both commits exist.

### Orchestrator Circuit-Breaker Check (both variants)

```bash
ITER_COUNT=$(grep -c '^GREEN_ITER\|^ITER' /tmp/wf-tdd-output.txt)
FINAL_EXIT=$(grep 'EXIT_CODE:' /tmp/wf-tdd-output.txt | tail -1 | awk '{print $2}')
if [ "$FINAL_EXIT" != "0" ] || [ "$ITER_COUNT" -gt 5 ]; then
  echo "CIRCUIT BREAKER: TDD failed after $ITER_COUNT iterations."
  # Rewind-discard recovery (see below)
  exit 1
fi
```

---

## HUMAN GATE (only if `-h`) — between TDD and Final Verification

Same as v1: `AskUserQuestion` with options Approve / Revise / Abort. Discard worktree on Abort.

---

## Phase 7: FINAL_VERIFICATION

Orchestrator cd's into `$WT_PATH` (or stays in main branch if `--no-worktree`):

```bash
$TEST_CMD 2>&1 | tee "$WT_PATH/.wf-final-verification.txt"
echo "EXIT_CODE: $?"
```

EXECUTION_BLOCK (FULL). If exit=0 → Phase 8. If not → Phase 7b.

---

## Phase 7b: FULL_SUITE_FIX (Conditional, same worktree)

Same as v1: regression-fixer agent, max 3 iterations, structured `ITER N/3:` log. On failure → circuit breaker + rewind-discard.

---

## Phase 8: GATE 2/2 — CODE_REVIEW (Tier-Gated)

| Tier | Cops active | MCP active |
|---|---|---|
| micro | SKIP entire phase | n/a |
| small | coverage-cop only | optional (if `-c`/`-g`) |
| full | simplicity + coherence + coverage | optional |

**For small: ONE Agent call (coverage-cop) + optional MCP, single message, foreground.**

**For full: THREE Agent calls + optional MCP, single message, foreground parallel.** Each cop returns a verdict line `<name>: PASS|REJECT` (correlated by `name` field).

```text
┌─────────────────────────────────────────────┐
│ [8/9] GATE 2/2 VERDICT                      │
├─────────────────────────────────────────────┤
│ Simplicity:   [PASS|REJECT|SKIP]            │
│ Coherence:    [PASS|REJECT|SKIP]            │
│ Coverage:     [PASS|REJECT]                 │
│ Codex Review: [APPROVED|NEEDS_WORK|N/A]     │
│ Antigravity:  [APPROVED|NEEDS_WORK|N/A]     │
│ OVERALL: [ALL PASS|NEEDS_WORK]              │
└─────────────────────────────────────────────┘
```

`SKIP` rows don't block. Max 3 reject iterations per failed reviewer.

---

## Phase 9: COMPLETION (Tier-Aware Provenance + ff-only Merge if `--commit`)

### Provenance Check (tier-aware)

```text
PROVENANCE CHECK
----------------
CTX (Phase 1):                   [PRESENT|MISSING]
WT (Phase 5):                    [PRESENT|MISSING|N/A] (N/A if --no-worktree)
QT (Phase 5):                    [PRESENT|MISSING]
EXECUTION RED:                   [PRESENT|MISSING] — exit != 0?
EXECUTION GREEN:                 [PRESENT|MISSING] — exit = 0?
EXECUTION FULL (Phase 7):        [PRESENT|MISSING] — exit = 0?
EXECUTION FIX (Phase 7b):        [PRESENT|MISSING|N/A] — exit = 0?
Cops (Phase 8):                  [N/N PASS|<N|SKIPPED for tier]
MCP (Phase 8):                   [APPROVED|N/A]
----------------
PROVENANCE: [COMPLETE|INCOMPLETE]
TIER WARNINGS: [list any tier downgrades, e.g., "full tier ran with --no-worktree"]
```

INCOMPLETE: STOP, do not merge.

### Merge logic

If `AUTO_COMMIT=true`: `git merge --ff-only $WT_BRANCH` from `$MAIN_REPO`, then re-run `$TEST_CMD` post-merge as regression check. On any failure: worktree preserved, exit non-zero.

If `AUTO_COMMIT=false` (default): print worktree path + branch + the exact merge commands user should run. No merge happens automatically.

Output: `ORCHESTRATION COMPLETE (wf v16, tier=$TIER)`

---

## Rewind-Discard Failure Recovery (replaces "respawn agent")

**Boris's `/rewind` pattern applied programmatically:** when an agent fails (test stays red after 5 iterations, regression-fix gives up after 3, cop rejects 3 times), do NOT respawn the same agent with accumulated context. Instead:

1. **Capture the failure summary** — one line: `Phase X failed: <symptom>. Last error: <error>. Files touched: <list>.`
2. **Discard the failed worktree entirely**: `git worktree remove --force "$WT_PATH"`
3. **Forget the failed agent's transcript** — do not re-feed its output to the next attempt
4. **Re-prompt with: original spec + the one-line failure summary ONLY** — the new agent gets a clean context with just enough hint to avoid repeating the same dead end
5. **Max 2 rewind cycles per phase.** Third failure → MANUAL INTERVENTION

This avoids the anti-pattern where each retry inherits more polluted context than the last.

Failure-path language throughout this workflow uses "rewind-discard" as the verb of art. The orchestrator prints:

```text
REWIND-DISCARD: Phase X agent failed. Capturing summary: <summary>.
Removing worktree: $WT_PATH
Spawning fresh agent with clean context + failure summary.
```

---

## Circuit Breakers (Tier-Aware)

| Trigger | All tiers | Action |
|---|---|---|
| No CONTEXT_BLOCK | ✓ | STOP |
| Quick test fails > 5 iterations (parsed from agent log) | ✓ | Rewind-discard cycle 1; STOP after cycle 2 |
| FULL_SUITE_FIX > 3 iterations | ✓ | Rewind-discard; STOP after cycle 2 |
| Any cop REJECTS 3× | small/full only | STOP: REVIEW LOOP EXCEEDED |
| External reviewer (Codex MCP / Antigravity CLI) NEEDS_WORK 3× | if reviewer active | STOP: REVIEW LOOP EXCEEDED |
| Provenance INCOMPLETE | ✓ | STOP, do not merge |
| Merge not fast-forwardable | if `--commit` | STOP, worktree preserved |
| Post-merge full suite fails | if `--commit` | STOP, worktree preserved |
| File count > 5 unjustified | full tier | STOP, consolidate |
| Coder ran full suite during inner loop | ✓ | Rewind-discard, stricter prompt |
| "Pre-existing failures" claim from agent | ✓ | RETRACT, fix the code |
| `--tier=full --no-worktree` | full tier | WARN at provenance time; proceed |

---

## Test Filter Reference

| Runner | Full Suite | Single Test |
|---|---|---|
| jest/npm | `npm test` | `npm test -- --testPathPattern=FILE --testNamePattern=NAME` |
| dotnet | `dotnet test` | `dotnet test --filter FullyQualifiedName~NAME` |
| Unity | `dotnet test` | `dotnet test --filter FullyQualifiedName~NAME` |
| pytest | `pytest` | `pytest FILE::CLASS::NAME -v` |
| cargo | `cargo test` | `cargo test NAME` |
| go | `go test ./...` | `go test -run NAME ./PKG` |

---

## When to Use Each Tier

| Situation | Tier | Rationale |
|---|---|---|
| Fix typo, rename variable, single-line bugfix | `--tier=micro` | 5-7 agents for a typo is over-orchestration |
| Add a function, fix one logic bug in one file | `--tier=small` | One coder + coverage cop is enough |
| Multi-file feature, refactor, new module | `--tier=full` (default) | Full ceremony justified |
| Slow test suite (Unity/.NET), risky migration | `--tier=full -cg` | Add MCP perspectives |
| One-shot exploration, can't define quick test | refactor task to define one, or run free-form | `/wf` requires a quick test |

## Legacy generations

Older generations (`wf1`–`wf12`, `wf14`, `wf15`, plus `boris1-h`, `boris2`, `ddr`, `ddr2`) live in `legacy/` at the repo root — archived for evolutionary context only, not auto-loaded by Claude Code as commands.

---

## User's Task

$ARGUMENTS
