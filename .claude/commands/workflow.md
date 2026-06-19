---
description: "TDD workflow - invoke ONLY when the user explicitly types /workflow or /wf; never auto-route code changes here. Codex MCP review runs by DEFAULT on every tier; --no-codex opts out."
argument-hint: "[flags] <task>"
---

# /workflow — Fast-Iteration TDD (Tier-Auto, Split-TDD, No-Worktree, Codex-Default) — `/wf` for short

**WF_VERSION:** `v0.27` · **WF_COMMITTED:** `19-jun-2026` · **Tag:** `[tier-auto | split-tdd | codex-default | rewind-discard | no-auto-commit | evidence-graded-gates | timing-receipt | segment-timing | assisted-by-trailer | longitudinal-ratchet | reviewer-timeout]`

**First line of every run must be, verbatim:** `workflow v0.27 (19-jun-2026)` — derived from the two values above. Bump both when the workflow body changes meaningfully.

**Second line — help banner:** if invoked via the `/wf` wrapper (the wrapper says so), print `/wf — short for /workflow: tier-auto TDD with cop reviews and Codex gate.` — otherwise print `/workflow — tier-auto TDD with cop reviews and Codex gate (/wf for short).`

`-g` = Antigravity via agy bridge MCP (`mcp__agy__agy_ask`, Gemini 3.5 Flash). `-c` = Codex MCP — **DEFAULT-ON since v22** (all tiers; `--no-codex` disables). No-flag default: tier-auto, split TDD, no worktree, Codex reviewer ON, no Antigravity, no gate, no commit.

## Usage

```text
/wf [flags] <task>
```

**Default behavior (no flags):** `tier=auto` (heuristic) · `split-tdd` · `no-worktree` · **Codex MCP reviewer ON** · no Antigravity · no human gate · no auto-commit · MCP downgrade allowed.

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
| `-c` | Codex MCP reviewer at both active gates (micro: Gate 2 only) | **DEFAULT** (since v22; flag kept for explicitness) |
| `--no-codex` | Disable the default Codex reviewer for this run (last flag wins if combined with `-c`) | opt-in |
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
- `/wf fix typo in README` → auto picks `micro` → 1 agent, no worktree, Codex spot-review at Gate 2
- `/wf implement email validator` → auto picks `small` → 1 split-TDD pair + coverage cop + Codex at both gates
- `/wf implement OAuth refresh flow` → auto picks `full` → split TDD + 4 cops + Codex, still no worktree unless `--worktree`
- `/wf --no-codex fix typo in README` → micro with zero MCP calls (old v21 behavior)
- `/wf --tier=full --worktree -g --commit implement payment flow` → kitchen sink (Codex already on by default)

---

## Tier Matrix

| Tier | Phases active | Coders | Cops | Plan Mode | Worktree | MCP |
|---|---|---|---|---|---|---|
| micro | 1, 2, 5+6, 7, 8a, 9 | 1 (split or unified) | 0 agents (Phase 8a signals only) | skip | no (forced) | Codex default at Gate 2 (`--no-codex` disables); `-g` ignored |
| small | 1, 2, 3, 4, 5+6, 7, 8 (coverage + metrics), 9 | 1 pair (split default) | 2 (coverage + metrics) | optional (active only if `-h`) | no (opt-in via `--worktree`) | Codex default; agy opt-in |
| full | All 9 phases | 1 pair (split default) | 4 (simplicity + coherence + coverage + metrics) | optional (active only if `-h`) | no (opt-in via `--worktree`) | Codex default; agy opt-in |

**Tier resolution order:**
1. Explicit `--tier=X` wins
2. Default tier: `auto` — heuristic scans task text (see `detect_tier_auto` in Flag Detection)
3. Conflicts: `--tier=micro --commit` → still ff-merges if green; `--tier=micro` runs the default Codex review at Gate 2 (`-g` is still ignored on micro); missing MCP → continue without (default) unless `--abort-on-missing-mcp` passed

---

## Flag Detection (Tokenized — word-boundary safe)

```bash
# v22 defaults: tier=auto, split-tdd, no-worktree, CODEX ON, no agy, no human gate, MCP downgrade allowed
TIER="auto"
HUMAN_GATE=false
CODEX_REVIEW=true                   # v22: Codex reviewer default-ON for everything; --no-codex opts out
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
    --no-codex)              CODEX_REVIEW=false ;;
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
    AGY_REVIEW=false   # micro ignores -g; CODEX_REVIEW keeps its default/flag value (v22) — single Codex review at Gate 2
    SKIP_PLAN_MODE=true; SKIP_COPS=true; SKIP_GATE1=true; SKIP_GATE2=true   # SKIP_GATE2/SKIP_COPS = skip cop AGENTS (8b) only; Codex review still runs in Phase 8
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

# v21: provenance trailer — appended as the LAST line of EVERY commit message this run creates.
# Model = the coder agent's actual model id; effort = its actual effort. If effort is unknown, OMIT the
# "-<effort>" suffix — never guess it.
WF_FLAGSTR=""
[ "$CODEX_REVIEW" = true ]  && WF_FLAGSTR+=" -c"
[ "$AGY_REVIEW" = true ]    && WF_FLAGSTR+=" -g"
[ "$HUMAN_GATE" = true ]    && WF_FLAGSTR+=" -h"
[ "$AUTO_COMMIT" = true ]   && WF_FLAGSTR+=" --commit"
[ "$USE_WORKTREE" = "yes" ] && WF_FLAGSTR+=" --worktree"
ASSIST_MODEL="${CODER_MODEL:-}"   # must be the ACTUAL session model id (from --coder-model or the session); never a guessed literal
ASSIST_EFFORT="${EFFORT:-}"       # empty when effort is unknown → the :+ expansion below omits the -<effort> suffix entirely
if [ -z "$ASSIST_MODEL" ]; then
  # HARD STOP: no trailer is constructed until the orchestrator fills ASSIST_MODEL with the real
  # session model id. TDD phases MUST NOT commit while ASSIST_TRAILER is unset.
  unset ASSIST_TRAILER
  echo "TRAILER: UNRESOLVED — fill ASSIST_MODEL with the real session model id before any commit"
else
  ASSIST_TRAILER="Assisted-by: wf${WF_FLAGSTR} ${ASSIST_MODEL}${ASSIST_EFFORT:+-$ASSIST_EFFORT}"
  echo "TRAILER: $ASSIST_TRAILER"   # e.g. "Assisted-by: wf -c opus-4.8-xhigh"
fi
```

**Word-boundary safety:** Flag parser tokenizes on whitespace; words like `force-commit`, `--commitment`, `-guide`, `-gpu` are NOT misread as flags.

**Heuristic transparency:** `auto` always prints the resolved tier (`AUTO-DETECT: '<task>' → tier=<X>`) so the user can override with `--tier=Y` on a re-run if the guess was wrong.

---

## Preflight: Reviewer Availability Check (Phase 0)

**Skip if both `CODEX_REVIEW=false` AND `AGY_REVIEW=false`** (since v22 this only happens with `--no-codex` — Codex is on by default on every tier).

```text
# -c (Codex MCP) — tool-namespace check (official `codex mcp-server`: 2 tools, `codex` + `codex-reply`)
ToolSearch({query: "select:mcp__codex-cli__codex,mcp__codex-cli__codex-reply", max_results: 2})

# -g (Antigravity via agy bridge MCP) — tool-namespace check (bridge: 3 tools, agy_ask/agy_continue/agy_status)
ToolSearch({query: "select:mcp__agy__agy_ask,mcp__agy__agy_continue,mcp__agy__agy_status", max_results: 3})
```

The `-g` reviewer runs through the **agy bridge MCP** (`mcp__agy__agy_ask`, Gemini 3.5 Flash) — register once with `claude mcp add agy -- ~/.claude/mcp-servers/agy-bridge/.venv/bin/python ~/.claude/mcp-servers/agy-bridge/server.py`, then restart Claude Code. The bridge wraps `agy` and reads its transcript files, working around the `agy -p` headless-stdout bug.

The bridge owns quota handling. It detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`; if free Gemini quota is exhausted, it automatically routes the same prompt to Vertex `gemini-3.5-flash` on project `<vertex-project>`, location `global`, using service account key `<vertex-sa-key-path>` unless overridden by environment. A response prefixed `[agy quota exhausted — auto-routed to Vertex gemini-3.5-flash on project <vertex-project>]` is a valid Gemini response, not a downgrade. Do not substitute Codex/self-review because Vertex credits would be used; Vertex is the intended Gemini fallback. If the bridge was updated but still behaves like the old agy-only bridge, restart Claude Code so the MCP server reloads.

On MISSING: continue with the missing reviewer disabled for execution (its internal flag forced false) and print the downgrade loudly (default — `ALLOW_MCP_DOWNGRADE=true` since v16.2; with Codex default-on this means `CODEX REVIEW SKIPPED - MCP missing` must appear in the final output). **Record it at the gate as `UNREACH (MCP missing)`, not `N/A`** — "forced false" here means "tried, unreachable," which is the same downgrade family as a timeout; `N/A` is reserved for a reviewer the user intentionally did not run (`--no-codex`, or not active for the tier). `--abort-on-missing-mcp` restores the abort behavior. For `-g`, "missing" means the `mcp__agy__agy_ask` tool is not loaded. **A reviewer that does not reply within the 5-minute cap is treated as unreachable too** — same downgrade path; see "Reviewer wall-clock cap" immediately below.

### Reviewer wall-clock cap (v0.27, always-on) — 5 minutes, no reply ⇒ unreachable, no retry

A reviewer MCP call that hasn't returned within **5 minutes** (`REVIEWER_TIMEOUT = 300s`) is treated as **UNREACHABLE** — the exact same downgrade path as "MCP missing." This fixes the failure mode where a Codex review that drops to the background or stalls leaves the orchestrator blocked for up to ~28h (the default tool-call timeout) "doing nothing meaningful."

- **No retry.** A timeout is **not** a `NEEDS_WORK` verdict, so it does **not** consume an iteration of the "reviewer NEEDS_WORK 3×" circuit breaker. It is one-shot: print the skip line and move to the next phase. Do **not** call the reviewer a second time.
- **Skip line (loud downgrade contract):** `CODEX REVIEW SKIPPED - timeout >5m (treated as unreachable)` for `-c`; `ANTIGRAVITY REVIEW SKIPPED - timeout >5m (treated as unreachable)` for `-g`. One of these must appear in the final output, just like the MCP-missing line.
- **Gate verdict semantics:** the reviewer row reads `UNREACHABLE (timeout >5m)`, **not** bare `N/A`. The gate still **PASSes** on that row because `ALLOW_MCP_DOWNGRADE=true` (default). Under `--abort-on-missing-mcp`, an unreachable reviewer **BLOCKS** instead (strict mode), identical to the missing-MCP rule.
- **Segment stamp:** write the `end` stamp for the call even on the timeout (the harness returns an error tool-result, so the call *does* return) — otherwise the Phase 9 timing receipt shows `UNCLOSED`. Same label as a normal call (`codex:gate2`, etc.).

**Enforcement — the real lever (not folklore).** The markdown cannot interrupt a blocking tool call by itself; the cap is enforced by Claude Code's per-tool-call execution timeout, **`MCP_TOOL_TIMEOUT`** (milliseconds), set in `.claude/settings.local.json` → `env`. This repo sets `MCP_TOOL_TIMEOUT=300000`. When it fires, the harness aborts the hung call and returns an error tool-result, so the orchestrator regains control and applies the unreachable path above. The setting is read **at session start**, so a Claude Code restart is required for a change to take effect, and it does **not** retroactively rescue a call already hung in the current session. (Behavior-on-fire — error tool-result vs. session abort — is undocumented upstream; "returns control to the orchestrator" is the designed behavior but is UNVERIFIED until a live >5m hang is observed post-restart.)

**Scope — reviewers only, by design.** The 5-min cap governs reviewer **MCP** calls (`mcp__codex-cli__codex`, `mcp__agy__agy_ask`). Coder/TDD `Agent()` subagents are **not** MCP calls and are **not** wall-clock-capped here — real implementation work can legitimately exceed 5 minutes. Coders keep their existing **iteration-based** circuit breakers (5 inner-loop iters, 3 regression-fix passes, 2 rewind-discard cycles); a wedged coder is caught by those, not by this timeout. (Known limitation: the skill has no way to impose a wall-clock cap on an `Agent()` call.)

**Blast radius (acknowledged).** `MCP_TOOL_TIMEOUT` is global to *all* MCP tool calls, but it lives in project-scoped `settings.local.json`, so other projects are unaffected. In this project every MCP tool is either a reviewer (`codex-cli`, `agy`) or an occasional quick Google call that never approaches 5 minutes, so the cap only ever bites a genuinely hung reviewer. To cap a single server instead, add a per-server `timeout` field (ms) to that server's `.mcp.json` entry — it overrides `MCP_TOOL_TIMEOUT` for that server only.

---

## Phase 1: CONTEXT_CAPTURE + TodoWrite + Hook Reminder

**Create TodoWrite with these items (tier-aware — micro has 4, small has 7, full has 9):**

| # | Item (full tier) | micro | small |
|---|---|---|---|
| 1 | MCP preflight check | ✓ (skip only with `--no-codex`) | ✓ | ✓ |
| 2 | Context capture | ✓ | ✓ | ✓ |
| 3 | Intake (spec.md) | ✓ | ✓ | ✓ |
| 4 | Planning (architecture.md) + plan-mode gate | skip | optional | ✓ |
| 5 | Gate 1/2: Plan review | skip | skip (unless `-h`) | ✓ |
| 6 | TDD (unified or split) | ✓ (unified) | ✓ | ✓ |
| 7 | Final verification (+7b if needed) | ✓ | ✓ | ✓ |
| 8 | Gate 2/2: Code review | 8a signals + Codex review | coverage + metrics cops + Codex | ✓ (4 cops + Codex) |
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

**Timing ledger (always-on):** start the wall-clock now so Phase 9 can print a total. Env vars do **not** persist across separate Bash calls — carry the echoed `WF_LEDGER` path to Phase 9 (or recover it there). The file is the verifiable record; the total is computed from it, never estimated.

```bash
WF_RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)                 # UTC stamp; lexical sort == chronological
WF_LEDGER=".claude/temp/wf/$WF_RUN_ID/started.txt"
WF_SEGMENTS=".claude/temp/wf/$WF_RUN_ID/segments.tsv"
mkdir -p ".claude/temp/wf/$WF_RUN_ID"
{ date +%s; date '+%Y-%m-%d %H:%M:%S'; } > "$WF_LEDGER"   # line 1 = epoch, line 2 = human start
: > "$WF_SEGMENTS"                                        # per-call timing rows (see Segment timing below)
echo "timing ledger: $WF_LEDGER"
echo "segment ledger: $WF_SEGMENTS"
```

### Segment timing (v25, always-on — measures subagents + Codex/agy waits)

Every **blocking external call** the orchestrator waits on gets a start row immediately before the call and an end row immediately after it returns. These calls are foreground, so each segment's duration **is** the additional wait it imposed on the main process. The file is the verifiable record; Phase 9 prints absolute start→end per call plus per-class wait totals — never estimated.

**Wrap rule** — run these Bash stamps around each call (`$WF_SEGMENTS` is carried/recovered exactly like `$WF_LEDGER`; set-u-safe recovery: `WF_SEGMENTS="$(dirname "${WF_LEDGER:-$(find .claude/temp/wf -name started.txt | sort | tail -1)}")/segments.tsv"`):

```bash
# BEFORE the blocking call:
printf '%s\tstart\t%s\t%s\n' "<label>" "$(date +%s)" "$(date '+%H:%M:%S')" >> "$WF_SEGMENTS"
# AFTER it returns:
printf '%s\tend\t%s\t%s\n'   "<label>" "$(date +%s)" "$(date '+%H:%M:%S')" >> "$WF_SEGMENTS"
```

**Labels** — `<class>:<call>`; class is the prefix before `:` and drives the per-class totals:

| Call | Label |
|---|---|
| Phase 5 RED agent | `agent:tdd-red` |
| Phase 6 GREEN agent | `agent:tdd-green` |
| Unified TDD agent | `agent:tdd-unified` |
| Phase 7b regression-fixer agent | `agent:fix` |
| Phase 8b cop batch (one segment around the whole parallel batch — wall wait, not sum) | `agent:cops` |
| Codex MCP review (Gate 1 / Gate 2) | `codex:gate1` / `codex:gate2` |
| agy MCP review (Gate 1 / Gate 2) | `agy:gate1` / `agy:gate2` |

**Every repetition of the same call appends `#N`** — re-review iterations (`codex:gate2#2`), rewind-discard respawns (`agent:tdd-green#2`), repeated fix passes (`agent:fix#2`) — so every segment label is unique; pairing in Phase 9 is by label, and a duplicate label would silently overwrite the earlier segment and undercount wait. A start row with no matching end row prints as `UNCLOSED` in the receipt (the call died or the stamp was skipped) — never silently dropped. The stamp snippets must be `set -u` safe: if `$WF_SEGMENTS` may be unset in a fresh Bash call, recover it first (`WF_SEGMENTS="$(dirname "${WF_LEDGER:-$(find .claude/temp/wf -name started.txt | sort | tail -1)}")/segments.tsv"`).

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

Otherwise: same as v1 (self-review + external reviewers). Codex reviews the plan by default (v22); for `small` tier with `--no-codex` and no `-g`, only the self-review checklist runs.

### Reviewer invocation reference

**Segment stamps (v25):** wrap each MCP reviewer call in the start/end stamps from Phase 1's Segment timing section — `codex:gate1` / `agy:gate1` here, `codex:gate2` / `agy:gate2` in Phase 8 (`#N` suffix on re-review iterations).

| Flag | Surface | Invocation pattern |
|---|---|---|
| `-c` | MCP tool call | `mcp__codex-cli__codex` with a review-style prompt ending in `End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>.` Model + reasoning effort inherit from `~/.codex/config.toml` — do not pass `model` or reasoning override unless you need to deviate. |
| `-g` | MCP tool call | `mcp__agy__agy_ask` with `prompt="<review prompt>"` (Gemini 3.5 Flash via the agy bridge; may auto-route to Vertex on agy quota exhaustion; returns the model's text directly — parse it for `APPROVED` / `NEEDS_WORK`) |

For `-g`: end the reviewer prompt with explicit verdict instructions, e.g. `"... End with one line: VERDICT: APPROVED or VERDICT: NEEDS_WORK <reason>."` Orchestrator greps the returned text's last line for the verdict token. Typical latency: 30–60s per call; budget accordingly. **Either reviewer is capped at 5 min** — if the call has not returned by then it is treated as UNREACHABLE (no retry, downgrade, proceed) per "Reviewer wall-clock cap" in Phase 0.

If the agy response is truncated and `mcp__agy__agy_continue` is available, continue the same reviewer conversation before marking the Antigravity review failed or starting another pass.

Aggregate block:

```text
┌─────────────────────────────────────────────┐
│ [4/9] GATE 1/2 (Plan Review)                │
├─────────────────────────────────────────────┤
│ Self-review: [PROCEED|REVISE]               │
│ Codex:       [APPROVED|NEEDS_WORK|UNREACH|N/A] │
│ Antigravity: [APPROVED|NEEDS_WORK|UNREACH|N/A] │
│ GATE STATUS: [PASS|BLOCKED]                 │
└─────────────────────────────────────────────┘
```

`UNREACH` = reviewer unreachable — MCP missing **or** the 5-min cap fired (timeout); the row passes via downgrade (`BLOCKED` only under `--abort-on-missing-mcp`). `N/A` = reviewer not run (`--no-codex`, or not active for this tier). See "Reviewer wall-clock cap" in Phase 0.

---

## Phase 5+6: TDD — Split or Unified

**Segment stamps (v25):** wrap every agent spawn below in the start/end stamps from Phase 1's Segment timing section — labels `agent:tdd-red`, `agent:tdd-green`, `agent:tdd-unified`, `agent:fix` (Phase 7b).

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
  prompt: <RED prompt — write test, run, must fail, commit "test: <feature> (RED)" with $ASSIST_TRAILER as the final commit-message line>
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
Every commit message you create must end with this exact trailer line: $ASSIST_TRAILER

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
- Every commit message ends with the trailer line `$ASSIST_TRAILER`
- FORBIDDEN: running `$TEST_CMD` (full suite). Only the quick test command.

After agent returns (either variant), capture `WT_PATH` (if worktree), `QUICK_TEST_CMD`, `TEST_FILES`. Verify both commits exist and each ends with the `Assisted-by:` trailer.

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
| micro | signals (runs) | none | Codex (default; `--no-codex` disables) |
| small | signals (runs) | coverage + metrics | Codex (default) + agy if `-g` |
| full | signals (runs) | simplicity + coherence + coverage + metrics | Codex (default) + agy if `-g` |

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
if [ -z "$FILES" ]; then echo "PHASE_8a: no production source touched (longitudinal ratchet still runs below)";
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

fi

# 4) LONGITUDINAL RATCHET + DEBT (v24) — runs on EVERY run, even when FILES is empty
RATCHET=.claude/metrics/ratchet.tsv; DEBT=.claude/metrics/debt.tsv
RUN_ID="${WF_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
CUR_DUP=NA
if command -v jscpd >/dev/null; then
  CUR_DUP=$(jscpd --silent --threshold 100 . 2>/dev/null | grep -oE '[0-9.]+%' | head -1 | tr -d '%')
  [ -n "$CUR_DUP" ] || CUR_DUP=NA   # jscpd present but unparseable → NA, never empty
fi
CUR_SUP=$(git grep -nE 'eslint-disable|ts-ignore|@ts-nocheck|type:\s*ignore|@SuppressWarnings|NOSONAR' -- ':!*.md' ':!tests/' 2>/dev/null | wc -l | tr -d ' ')
CUR_CYC=NA
if command -v madge >/dev/null; then
  # parse the COUNT from "✖ Found N circular dependencies!" — not mere presence (1 cycle vs 5 must differ)
  CUR_CYC=$(madge --circular . 2>/dev/null | grep -oE 'Found [0-9]+ circular' | grep -oE '[0-9]+' | head -1)
  CUR_CYC=${CUR_CYC:-0}   # madge ran, no "Found N" line → zero cycles
fi
LAST=$(grep -v '^#' "$RATCHET" 2>/dev/null | tail -1)
if [ -n "$LAST" ]; then
  L_DUP=$(printf '%s' "$LAST" | cut -f2); L_SUP=$(printf '%s' "$LAST" | cut -f3); L_CYC=$(printf '%s' "$LAST" | cut -f4)
  if [ "$CUR_DUP" != "NA" ] && [ "$L_DUP" != "NA" ] && awk -v c="$CUR_DUP" -v l="$L_DUP" 'BEGIN{exit !(c > l + 0.5)}'; then
    echo "RATCHET REJECT: repo dup ${CUR_DUP}% > last ${L_DUP}% + 0.5pt"; GATE_VERDICT="REJECT"; fi
  [ "$CUR_DUP" = "NA" ] && echo "RATCHET dup: unmeasured (jscpd missing/unparseable) — skipped, NOT a pass"
  if [ "${CUR_SUP:-0}" -gt "${L_SUP:-0}" ] 2>/dev/null; then
    echo "RATCHET REJECT: suppressions $CUR_SUP > last $L_SUP"; GATE_VERDICT="REJECT"; fi
  if [ "$CUR_CYC" != "NA" ] && [ "$L_CYC" != "NA" ] && [ "$CUR_CYC" -gt "$L_CYC" ] 2>/dev/null; then
    echo "RATCHET REJECT: prod cycles $CUR_CYC > last $L_CYC"; GATE_VERDICT="REJECT"; fi
  [ "$CUR_CYC" = "NA" ] && echo "RATCHET cycles: unmeasured (madge missing) — skipped, NOT a pass"
else echo "RATCHET: no prior row — baseline run, comparisons start next run"; fi
# debt append + 3-strikes escalation; any non-numeric sloc field (waiver:/recovered:) breaks a streak
for f in $FILES; do
  [ -f "$f" ] || continue
  sloc=$(grep -cvE '^\s*$' "$f")
  case "$f" in *test*|*spec*|*fixture*) warn=$((SIZE_WARN*3/2));; *) warn=$SIZE_WARN;; esac
  if [ "$sloc" -gt "$warn" ]; then
    printf '%s\t%s\t%s\n' "$RUN_ID" "$f" "$sloc" >> "$DEBT"
    HIST=$(grep -v '^#' "$DEBT" | awk -F'\t' -v f="$f" '$2==f {print $3}' | tail -3)
    N=$(printf '%s\n' "$HIST" | grep -c .)
    if [ "$N" -ge 3 ] && ! printf '%s\n' "$HIST" | grep -q '[^0-9]'; then
      S1=$(printf '%s\n' "$HIST" | sed -n 1p); S2=$(printf '%s\n' "$HIST" | sed -n 2p); S3=$(printf '%s\n' "$HIST" | sed -n 3p)
      if [ "$S2" -ge "$S1" ] && [ "$S3" -ge "$S2" ]; then   # pairwise non-decreasing (500→400→500 must NOT reject)
        echo "DEBT ESCALATION REJECT: $f warned 3 consecutive appearances, non-decreasing SLOC ($S1→$S2→$S3) — extract a responsibility or record a waiver row"; GATE_VERDICT="REJECT"; fi
    fi
  elif [ -f "$DEBT" ] && awk -F'\t' -v f="$f" '$2==f{found=1} END{exit !found}' "$DEBT"; then
    printf '%s\t%s\trecovered:%s\n' "$RUN_ID" "$f" "$sloc" >> "$DEBT"   # shrank below warn → streak breaker
  fi
done
echo "PHASE_8a GATE_VERDICT: $GATE_VERDICT"
```

`GATE_VERDICT=REJECT` (egregious batch size or duplication) blocks the gate on **all** tiers, **independent of `SKIP_GATE2`/`SKIP_COPS`** (those govern the cop *agents* in Phase 8b). File-size WARNs never block — they inform the reviewer / `metrics-cop`. See [`.claude/reference/code-quality-metrics.md`](../reference/code-quality-metrics.md) for the full metric set and evidence tiers.

### Phase 8b — Cop agents (small / full only) + Codex review (all tiers)

**Segment stamps (v25):** one `agent:cops` segment around the whole parallel cop batch (wall wait, not per-cop sum), plus `codex:gate2` / `agy:gate2` around each MCP review call.

**For micro: no cop agents, but the default Codex review still runs here** — one `mcp__codex-cli__codex` call reviewing the diff vs `$BASELINE_SHA`, verdict-line protocol as in the Gate 1 reference. `SKIP_GATE2`/`SKIP_COPS` govern cop *agents* only, not the Codex reviewer. This call is subject to the 5-min cap: no reply by then ⇒ UNREACHABLE, print the skip line, no retry, proceed (Phase 0 "Reviewer wall-clock cap").

**For small: TWO Agent calls (coverage-cop + metrics-cop) + Codex (default) / agy MCP, single message, foreground.**

**For full: FOUR Agent calls (simplicity + coherence + coverage + metrics) + Codex (default) / agy MCP, single message, foreground parallel.** Each cop returns a verdict line `<name>: PASS|REJECT` (correlated by `name` field).

**metrics-cop prompt (small + full):** pass it both `$BASELINE_SHA` (so it measures cumulative growth, not just the diff) AND the instruction to run its **Debt Escalation** section against `.claude/metrics/debt.tsv` (3 consecutive non-decreasing-SLOC warnings on a touched file → REJECT until it shrinks or a waiver row is recorded).

```text
┌─────────────────────────────────────────────┐
│ [8/9] GATE 2/2 VERDICT                      │
├─────────────────────────────────────────────┤
│ Signals (8a): [PASS|REJECT] (batch/dup)     │
│ Simplicity:   [PASS|REJECT|SKIP]            │
│ Coherence:    [PASS|REJECT|SKIP]            │
│ Coverage:     [PASS|REJECT|SKIP]            │
│ Metrics:      [PASS|REJECT|SKIP]            │
│ Codex Review: [APPROVED|NEEDS_WORK|UNREACH|N/A] │
│ Antigravity:  [APPROVED|NEEDS_WORK|UNREACH|N/A] │
│ OVERALL: [ALL PASS|NEEDS_WORK]              │
└─────────────────────────────────────────────┘
```

`SKIP` rows don't block. `UNREACH` (reviewer unreachable — MCP missing or the 5-min cap fired) passes via downgrade — it is not a `NEEDS_WORK` and does not count toward the 3-iteration cap; `--abort-on-missing-mcp` makes it BLOCK. `N/A` = reviewer not run (`--no-codex` / not active for tier). Phase 8a REJECT blocks on all tiers. Max 3 reject iterations per failed reviewer.

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
MCP (Phase 8):                   [APPROVED|UNREACHABLE|N/A] — N/A only via --no-codex; UNREACHABLE = missing MCP or 5-min timeout; state which
----------------
PROVENANCE: [COMPLETE|INCOMPLETE]
TIER WARNINGS: [list any tier downgrades, e.g., "full tier ran with --no-worktree"]
```

INCOMPLETE: STOP, do not merge.

### Ratchet row append (v24, always-on — after provenance COMPLETE, before the timing receipt)

Append this run's repo-wide measurements to `.claude/metrics/ratchet.tsv` so the next run has a baseline to ratchet against. The block is **fully self-contained** (env does NOT persist between Bash calls — everything is recomputed; safe under `set -u` even when Phase 8a took the FILES-empty path); the orchestrator must re-export `ASSIST_TRAILER` (and `WF_RUN_ID`) into this Bash call, the same way it carries `WF_LEDGER` — the trailer is never guessed. `NA` means unmeasured (tool missing) — never guess a number.

```bash
RUN_ID="${WF_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
CUR_DUP=NA; command -v jscpd >/dev/null && { CUR_DUP=$(jscpd --silent --threshold 100 . 2>/dev/null | grep -oE '[0-9.]+%' | head -1 | tr -d '%'); [ -n "$CUR_DUP" ] || CUR_DUP=NA; }
CUR_SUP=$(git grep -nE 'eslint-disable|ts-ignore|@ts-nocheck|type:\s*ignore|@SuppressWarnings|NOSONAR' -- ':!*.md' ':!tests/' 2>/dev/null | wc -l | tr -d ' ')
CUR_CYC=NA; command -v madge >/dev/null && { CUR_CYC=$(madge --circular . 2>/dev/null | grep -oE 'Found [0-9]+ circular' | grep -oE '[0-9]+' | head -1); CUR_CYC=${CUR_CYC:-0}; }
FOW=$(git ls-files '*.sh' '*.py' '*.ts' '*.js' '*.cs' 2>/dev/null | while read -r f; do n=$(grep -cvE '^\s*$' "$f"); [ "$n" -gt 300 ] && echo 1; done | wc -l | tr -d ' ')
printf '%s\t%s\t%s\t%s\t%s\n' "$RUN_ID" "$CUR_DUP" "$CUR_SUP" "$CUR_CYC" "$FOW" >> .claude/metrics/ratchet.tsv
if [ -z "${ASSIST_TRAILER:-}" ]; then
  echo "ratchet commit skipped: ASSIST_TRAILER unset — re-export it in this shell (orchestrator carries it like WF_LEDGER)"
else
  git add .claude/metrics/ && git commit -m "chore(metrics): ratchet row $RUN_ID

$ASSIST_TRAILER" --quiet && echo "ratchet row committed" || echo "ratchet commit skipped (no change)"
fi
```

**Known limitation:** the deterministic debt gate is scoped to production source as filtered by Phase 8a — markdown workflow files (this repo's "source") are excluded from it by the generic `*.md` filter; their size/trend is owned by metrics-cop judgment and the gardener, not the deterministic gate. This avoids blocking on prose length, which would be a folklore gate.

### Merge logic

If `AUTO_COMMIT=true`: `git merge --ff-only $WT_BRANCH` from `$MAIN_REPO`, then re-run `$TEST_CMD` post-merge as regression check. On any failure: worktree preserved, exit non-zero.

If `AUTO_COMMIT=false` (default): print worktree path + branch + the exact merge commands user should run. No merge happens automatically.

### Timing receipt (always-on, total wall time + per-call segments)

Compute the total from the Phase 1 ledger and print the receipt just above the completion line. `LEDGER` is the `WF_LEDGER` path echoed in Phase 1; if that path was lost, recover the newest run (RUN_IDs are UTC stamps, so lexical sort = chronological). If no ledger is found, print `UNVERIFIED` — never estimate. This measures wall-clock from the Phase 1 stamp (not from when the user pressed enter), not CPU/active time.

The segment block reads `segments.tsv` (same run dir; see Segment timing in Phase 1) and prints, per blocking call: absolute start → end and duration; then per-class wait totals (`agent`/`codex`/`agy`), the combined blocking wait, and `orchestrator-own` = TOTAL − combined wait (time the main process was itself working, not waiting). Since all wrapped calls are foreground, per-segment duration = the extra wait that call imposed on the main process.

```bash
LEDGER="${WF_LEDGER:-}"   # :- keeps this set-u safe when the env var was lost between Bash calls
[ -f "$LEDGER" ] || LEDGER=$(find .claude/temp/wf -name started.txt -type f 2>/dev/null | sort | tail -1)
if [ -z "$LEDGER" ] || [ ! -f "$LEDGER" ]; then
  echo "⏱ workflow v0.27 tier=$TIER | TOTAL UNVERIFIED (start stamp not found)"
else
  S=$(sed -n 1p "$LEDGER"); SH=$(sed -n 2p "$LEDGER")
  E=$(date +%s); EH=$(date '+%Y-%m-%d %H:%M:%S'); T=$((E - S))
  if [ "$T" -ge 3600 ]; then H=$(printf '%dh %02dm %02ds' $((T/3600)) $((T%3600/60)) $((T%60)));
  else H=$(printf '%dm %02ds' $((T/60)) $((T%60))); fi
  echo "⏱ workflow v0.27 tier=$TIER | $SH → $EH | TOTAL $H"
  SEG="$(dirname "$LEDGER")/segments.tsv"
  if [ -s "$SEG" ]; then
    awk -F'\t' -v total="$T" '
      function fmt(d){ return sprintf("%dm %02ds", d/60, d%60) }
      $2=="start"{ s[$1]=$3; sh[$1]=$4; if(!seen[$1]++){ order[++n]=$1 } }
      $2=="end"  { e[$1]=$3; eh[$1]=$4 }
      END{
        for(i=1;i<=n;i++){ l=order[i]
          if(e[l]==""){ printf "  %-22s %s → ?         UNCLOSED (no end stamp)\n", l, sh[l]; continue }
          d=e[l]-s[l]; cls=l; sub(/:.*/,"",cls); wait[cls]+=d; allwait+=d
          printf "  %-22s %s → %s  %s\n", l, sh[l], eh[l], fmt(d) }
        line="  WAIT"
        split("agent codex agy", cls_order, " ")   # fixed order — for(c in wait) is nondeterministic
        for(i=1;i<=3;i++){ c=cls_order[i]; if(c in wait) line=line sprintf(" %s=%s |", c, fmt(wait[c])) }
        printf "%s all-blocking=%s | orchestrator-own=%s\n", line, fmt(allwait), fmt(total-allwait)
      }' "$SEG"
  else
    echo "  segments: none recorded (segments.tsv missing or empty — per-call waits UNVERIFIED)"
  fi
fi
```

Example receipt:

```text
⏱ workflow v0.27 tier=small | 2026-06-11 14:02:11 → 2026-06-11 14:19:48 | TOTAL 17m 37s
  agent:tdd-red          14:02:40 → 14:05:12  2m 32s
  agent:tdd-green        14:05:20 → 14:11:03  5m 43s
  agent:cops             14:12:30 → 14:15:01  2m 31s
  codex:gate2            14:15:05 → 14:17:44  2m 39s
  WAIT agent=10m 46s | codex=2m 39s | all-blocking=13m 25s | orchestrator-own=4m 12s
```

Output (final line): `ORCHESTRATION COMPLETE (workflow v0.27, tier=$TIER)`

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
| External reviewer (Codex MCP / agy bridge MCP) NEEDS_WORK 3× | if reviewer active | STOP: REVIEW LOOP EXCEEDED |
| External reviewer no reply within 5-min cap (`MCP_TOOL_TIMEOUT`) | if reviewer active | Treat UNREACHABLE: print skip line, NO retry, downgrade + proceed (`--abort-on-missing-mcp` ⇒ STOP). Not a NEEDS_WORK iteration |
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
| Slow test suite (Unity/.NET), risky migration | `--tier=full -g` | Codex already on; add the Antigravity perspective |
| One-shot exploration, can't define quick test | refactor task to define one, or run free-form | `/wf` requires a quick test |

## Legacy generations

Older generations (`wf1`–`wf12`, `wf14`, `wf15`, plus `boris1-h`, `boris2`, `ddr`, `ddr2`) live in `legacy/` at the repo root — archived for evolutionary context only, not auto-loaded by Claude Code as commands.

---

## User's Task

$ARGUMENTS
