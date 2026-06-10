# /wf — Fast-Iteration TDD (Tier-Auto, Split-TDD, No-Worktree Default)

**WF_VERSION:** `v19` · **WF_COMMITTED:** `10-jun-2026` · **Tag:** `[tier-auto | split-tdd | optional MCP | rewind-discard | no-auto-commit | evidence-graded-gates]`

**First line of every run must be, verbatim:** `wf v19 (10-jun-2026)` — derived from the two values above. Bump both when the workflow body changes meaningfully.

`-g` = Antigravity via agy bridge MCP (`mcp__agy__agy_ask`, Gemini 3.5 Flash). `-c` = Codex MCP. No-flag default: tier-auto, split TDD, no worktree, no reviewers, no gate, no commit.

## Usage

```text
/wf [flags] <task>
```

**Default behavior (no flags):** `tier=auto` (heuristic) · `split-tdd` · `no-worktree` · no MCP · no human gate · no auto-commit · MCP downgrade allowed.

| Flag | Effect | Default? |
|---|---|---|
| `--tier=auto` | Heuristic picks micro/small/full from task text | **DEFAULT** |
| `--tier=micro` | 1-line/comment/rename — skip plan mode, no cop agents, no plan gate; Phase 8a signals run (batch-size/dup can block) | |
| `--tier=small` | 1-file feature/fix — optional plan mode, coverage + metrics cops | |
| `--tier=full` | Multi-file feature — plan mode + 4 cops + (optional) worktree | |
| `--split-tdd` | TWO zero-context agents: RED then GREEN | **DEFAULT** |
| `--unified-tdd` | ONE agent does RED+GREEN in SAME context (steipete catch-rate) | |
| `--no-worktree` | Work on current branch | **DEFAULT** |
| `--worktree` | Force-create isolated git worktree (steipete-counter: only when you want it) | |
| `-c` | Add Codex MCP reviewer at both gates | opt-in |
| `-g` | Add Antigravity reviewer (`mcp__agy__agy_ask` bridge, Gemini 3.5 Flash) at both gates | opt-in |
| `-h` | Human gate via `AskUserQuestion` after RED | opt-in |
| `--commit` | ff-only merge to main on success | opt-in |
| `--allow-mcp-downgrade` | Continue if requested reviewer is missing (Codex MCP or agy bridge MCP) | **DEFAULT** (was abort in v16.1) |
| `--abort-on-missing-mcp` | Old behavior: abort if `-c` Codex MCP or `-g` agy bridge MCP is missing | opt-in |
| `--cops-model=<m>` | Override cop model (default: inherit session model) | opt-in |
| `--coder-model=<m>` | Override coder model (default: inherit session model) | opt-in |
| `--effort=<level>` | Reasoning effort (default: inherit session setting) | opt-in |
| `--goal "<criterion>"` | Append explicit success contract to GREEN agent prompt (Boris `/goal` pattern) | opt-in |
| `--dry-run` | Stop after Phase 4. Print plan, no code touched | opt-in |

**Combinable.** Examples:
- `/wf fix typo in README` → auto picks `micro` → 1 agent, no worktree, no ceremony
- `/wf implement email validator` → auto picks `small` → 1 split-TDD pair + coverage cop
- `/wf implement OAuth refresh flow` → auto picks `full` → split TDD + 4 cops, still no worktree unless `--worktree`
- `/wf --tier=full --worktree -cg --commit implement payment flow` → kitchen sink

---

## Tier Matrix

| Tier | Phases active | Coders | Cops | Plan Mode | Worktree | MCP |
|---|---|---|---|---|---|---|
| micro | 1, 2, 5+6, 7, 8a, 9 | 1 (split or unified) | 0 agents (Phase 8a signals only) | skip | no (forced) | ignored even if `-c -g` |
| small | 1, 2, 3, 4, 5+6, 7, 8 (coverage + metrics), 9 | 1 pair (split default) | 2 (coverage + metrics) | optional (active only if `-h`) | no (opt-in via `--worktree`) | optional |
| full | All 9 phases | 1 pair (split default) | 4 (simplicity + coherence + coverage + metrics) | optional (active only if `-h`) | no (opt-in via `--worktree`) | optional |

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
AGY_REVIEW=false                    # `-g` flag: Antigravity via agy bridge MCP (mcp__agy__agy_ask)
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
    SKIP_PLAN_MODE=true; SKIP_COPS=true; SKIP_GATE1=true; SKIP_GATE2=true   # SKIP_GATE2/SKIP_COPS = skip cop AGENTS (8b) only
    COPS_SUBSET="none"; SIZE_CHECK=true   # v19: Phase 8a deterministic signals still run on micro (gated by SIZE_CHECK, not SKIP_GATE2) — batch/size/dup
    ;;
  small)
    UNIFIED_TDD="${UNIFIED_TDD_OVERRIDE:-split}"
    USE_WORKTREE="${USE_WORKTREE_OVERRIDE:-no}"
    SKIP_PLAN_MODE=false; ACTIVE_PLAN_MODE=$HUMAN_GATE
    COPS_SUBSET="coverage+metrics"; SIZE_CHECK=true   # v18: metrics-cop joins coverage-cop
    ;;
  full)
    UNIFIED_TDD="${UNIFIED_TDD_OVERRIDE:-split}"
    USE_WORKTREE="${USE_WORKTREE_OVERRIDE:-no}"   # opt-in even for full
    SKIP_PLAN_MODE=false; ACTIVE_PLAN_MODE=$HUMAN_GATE   # EnterPlanMode is interactive; only invoke with -h
    COPS_SUBSET="all"; SIZE_CHECK=true   # v18: all = simplicity + coherence + coverage + metrics (4 cops)
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
# -c (Codex MCP) — tool-namespace check (official `codex mcp-server`: 2 tools, `codex` + `codex-reply`)
ToolSearch({query: "select:mcp__codex-cli__codex,mcp__codex-cli__codex-reply", max_results: 2})

# -g (Antigravity via agy bridge MCP) — tool-namespace check (bridge: 3 tools, agy_ask/agy_continue/agy_status)
ToolSearch({query: "select:mcp__agy__agy_ask,mcp__agy__agy_status", max_results: 2})
```

The `-g` reviewer runs through the **agy bridge MCP** (`mcp__agy__agy_ask`, Gemini 3.5 Flash) — register once with `claude mcp add agy -- ~/.claude/mcp-servers/agy-bridge/.venv/bin/python ~/.claude/mcp-servers/agy-bridge/server.py`, then restart Claude Code. The bridge wraps `agy` and reads its transcript files, working around the `agy -p` headless-stdout bug.

On MISSING: ABORT by default; `--allow-mcp-downgrade` continues with the missing flag forced false. For `-g`, "missing" means the `mcp__agy__agy_ask` tool is not loaded.

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
| 8 | Gate 2/2: Code review | 8a signals only | coverage + metrics cops | ✓ (4 cops) |
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

**Required for Phase 8a:** explicitly capture the run baseline SHA so the batch-size and file-size signals can measure cumulative growth across the whole run (not just the last commit):

```bash
export BASELINE_SHA=$(git rev-parse HEAD)   # start-of-run commit; Phase 8a diffs touched files against this
echo "BASELINE_SHA=$BASELINE_SHA"
```

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
| `-c` | MCP tool call | `mcp__codex-cli__codex` with a review-style prompt ending in `End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>.` Model + reasoning effort inherit from `~/.codex/config.toml` — do not pass `model` or reasoning override unless you need to deviate. |
| `-g` | MCP tool call | `mcp__agy__agy_ask` with `prompt="<review prompt>"` (Gemini 3.5 Flash via the agy bridge; returns the model's text directly — parse it for `APPROVED` / `NEEDS_WORK`) |

For `-g`: end the reviewer prompt with explicit verdict instructions, e.g. `"... End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>."` Orchestrator greps the returned text's last line for the verdict token. Typical latency: 30–60s per call; budget accordingly.

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

| Tier | Phase 8a (deterministic signals) | Cop agents active | MCP active |
|---|---|---|---|
| micro | signals (runs) | none | n/a |
| small | signals (runs) | coverage + metrics | optional (if `-c`/`-g`) |
| full | signals (runs) | simplicity + coherence + coverage + metrics | optional |

### Phase 8a — Evidence-graded signals (batch size · file size · duplication)

**v19 — realigned to the evidence** (see [`.claude/research/ai-generated-code-best-practices.md`](../research/ai-generated-code-best-practices.md)). Hard file-size/complexity *caps* are folklore-tier as blockers (cyclomatic complexity ≈ 0.93·LOC — no independent signal; no empirical basis for a "300/500-line" cutoff). The two practices that ARE evidence-backed — **small batch size** (DORA 2024: large changesets drive a −7.2% stability hit) and **low duplication** (GitClear: AI quadruples clones) — were previously *missing*. So in v19:

- **Batch size** (changed LOC — added+deleted — this run vs `$BASELINE_SHA`) is the only **size-derived** hard block — 🟢 the strongest AI-era lever (duplication also hard-blocks, below).
- **Duplication** blocks only when **egregious** — 🟢 risk signal, gated high to avoid punishing intentional dup.
- **File size** is **WARN-only** now (demoted from REJECT) — 🟡 a soft anti-balloon signal for review, not a gate.

Runs whenever `SIZE_CHECK=true` (every tier). No LLM judgment, no agent spawn — pure measurement.

```bash
if [ -n "$BASELINE_SHA" ]; then BASE="$BASELINE_SHA"
else BASE="HEAD~1"; echo "SIGNALS DEGRADED: BASELINE_SHA unset — batch/size measured against HEAD~1 only"; fi
BATCH_WARN=400; BATCH_BLOCK=800     # 🟢 batch size (DORA) — the only size-derived hard block
SIZE_WARN=300                       # 🟡 file size — soft WARN only (hard caps are folklore)
DUP_WARN=3; DUP_BLOCK=5             # 🟢 duplication % (GitClear) — block only when egregious
GATE_VERDICT="PASS"

# Scope to production source: drop deps/build/generated, pure docs, lockfiles.
FILES=$(git diff --name-only "$BASE" 2>/dev/null \
          | grep -vE '(^|/)(node_modules|dist|build|vendor|__snapshots__|migrations|\.git)/' \
          | grep -vE '\.(min\.js|generated\.[a-z]+|lock|md|mdx|rst|txt)$' \
          | grep -vE '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml)$' || true)
if [ -z "$FILES" ]; then echo "PHASE_8a: no production source touched"; echo "PHASE_8a GATE_VERDICT: PASS";
else

# 1) BATCH SIZE — 🟢 evidence-backed, the only size-derived hard block (duplication also blocks, below).
#    Batch size = total churn (added + deleted), the DORA changeset-size notion — a big refactor
#    is still a big batch. (Distinct from per-file net growth, which the size signal below uses.)
BATCH=$(git diff --numstat "$BASE" -- $FILES 2>/dev/null | awk '{a+=$1+$2} END{print a+0}')
if   [ "$BATCH" -gt "$BATCH_BLOCK" ]; then echo "BATCH REJECT: ${BATCH} changed LOC (added+deleted) > ${BATCH_BLOCK} — split into smaller changes (DORA: large batches drive instability)"; GATE_VERDICT="REJECT"
elif [ "$BATCH" -gt "$BATCH_WARN" ]; then echo "BATCH WARN: ${BATCH} changed LOC (added+deleted) > ${BATCH_WARN} — prefer smaller batches"; fi

# 2) FILE SIZE — 🟡 soft signal, WARN only (never blocks; reviewer/metrics-cop decides if a split is worth it)
for f in $FILES; do
  [ -f "$f" ] || continue
  sloc=""
  command -v scc  >/dev/null && sloc=$(scc --format json "$f" 2>/dev/null | grep -o '"Code":[0-9]*' | head -1 | grep -o '[0-9]*')
  [ -z "$sloc" ] && command -v cloc >/dev/null && sloc=$(cloc --quiet --csv "$f" 2>/dev/null | awk -F, 'END{print $5}')
  [ -z "$sloc" ] && sloc=$(grep -cvE '^\s*$' "$f")
  case "$f" in *test*|*spec*|*fixture*) warn=$((SIZE_WARN*3/2));; *) warn=$SIZE_WARN;; esac
  [ "${sloc:-0}" -gt "$warn" ] && echo "SIZE WARN: $f = ${sloc} SLOC > ${warn} (soft signal — consider extracting; not a blocker)"
done

# 3) DUPLICATION — 🟢 risk signal; WARN >3%, REJECT only when egregious (>5%)
if command -v jscpd >/dev/null; then
  dup=$(jscpd --silent --threshold 100 $FILES 2>/dev/null | grep -oE '[0-9.]+%' | head -1 | tr -d '%')
  if   [ -n "$dup" ] && awk "BEGIN{exit !($dup > $DUP_BLOCK)}"; then echo "DUP REJECT: ${dup}% duplicated > ${DUP_BLOCK}% — deduplicate (GitClear: AI inflates clones)"; GATE_VERDICT="REJECT"
  elif [ -n "$dup" ] && awk "BEGIN{exit !($dup > $DUP_WARN)}"; then echo "DUP WARN: ${dup}% duplicated > ${DUP_WARN}%"
  elif [ -n "$dup" ]; then echo "DUP: ${dup}% (clean)"; fi
else echo "DUP: jscpd not installed — duplication unmeasured (install for the GitClear-class gate)"; fi

echo "PHASE_8a GATE_VERDICT: $GATE_VERDICT"
fi
```

`GATE_VERDICT=REJECT` (egregious batch size or duplication) blocks the gate on **all** tiers, **independent of `SKIP_GATE2`/`SKIP_COPS`** (those govern the cop *agents* in Phase 8b). File-size WARNs never block — they inform the reviewer / `metrics-cop`. See [`.claude/reference/code-quality-metrics.md`](../reference/code-quality-metrics.md) for the full metric set and evidence tiers.

### Phase 8b — Cop agents (small / full only)

**For small: TWO Agent calls (coverage-cop + metrics-cop) + optional MCP, single message, foreground.**

**For full: FOUR Agent calls (simplicity + coherence + coverage + metrics) + optional MCP, single message, foreground parallel.** Each cop returns a verdict line `<name>: PASS|REJECT` (correlated by `name` field). Pass `$BASELINE_SHA` to metrics-cop so it measures cumulative growth, not just the diff.

```text
┌─────────────────────────────────────────────┐
│ [8/9] GATE 2/2 VERDICT                      │
├─────────────────────────────────────────────┤
│ Signals (8a): [PASS|REJECT] (batch/dup)     │
│ Simplicity:   [PASS|REJECT|SKIP]            │
│ Coherence:    [PASS|REJECT|SKIP]            │
│ Coverage:     [PASS|REJECT|SKIP]            │
│ Metrics:      [PASS|REJECT|SKIP]            │
│ Codex Review: [APPROVED|NEEDS_WORK|N/A]     │
│ Antigravity:  [APPROVED|NEEDS_WORK|N/A]     │
│ OVERALL: [ALL PASS|NEEDS_WORK]              │
└─────────────────────────────────────────────┘
```

`SKIP` rows don't block. Phase 8a REJECT blocks on all tiers. Max 3 reject iterations per failed reviewer.

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
Signals (Phase 8a):              [PASS|REJECT] — batch/dup block; size warns; runs on all tiers
Cops (Phase 8b):                 [N/N PASS|<N|SKIPPED for tier]
MCP (Phase 8):                   [APPROVED|N/A]
----------------
PROVENANCE: [COMPLETE|INCOMPLETE]
TIER WARNINGS: [list any tier downgrades, e.g., "full tier ran with --no-worktree"]
```

INCOMPLETE: STOP, do not merge.

### Merge logic

If `AUTO_COMMIT=true`: `git merge --ff-only $WT_BRANCH` from `$MAIN_REPO`, then re-run `$TEST_CMD` post-merge as regression check. On any failure: worktree preserved, exit non-zero.

If `AUTO_COMMIT=false` (default): print worktree path + branch + the exact merge commands user should run. No merge happens automatically.

Output: `ORCHESTRATION COMPLETE (wf v19, tier=$TIER)`

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
| Phase 8a signals REJECT (batch >800 changed LOC, or duplication egregious) | all tiers | STOP: split into smaller changes / deduplicate (DORA + GitClear evidence) |
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
