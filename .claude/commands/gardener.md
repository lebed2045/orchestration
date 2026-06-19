---
description: "Periodic entropy-removal workflow. Reads the longitudinal ledgers (ratchet.tsv trend, debt.tsv open items), sweeps the repo for duplication/dead code, and executes the top-K cleanups as small /wf-style tasks with separate commits."
argument-hint: "[--top=K] [--dry-run]"
---

# /gardener — Periodic Entropy Removal

**Updated:** `19-jun-2026`

Companion to `/wf`'s longitudinal gates. `/wf` *blocks* new entropy (ratchet + debt escalation); `/gardener` *removes* accumulated entropy on demand. Run it manually when the ledgers show drift, or on a schedule.

## Usage

```text
/gardener [--top=K] [--dry-run]
```

| Flag | Effect | Default |
|---|---|---|
| `--top=K` | Execute the K highest-ranked cleanup items | `K=3` |
| `--dry-run` | Print the ranked plan only — no edits, no commits | off |

## Phase 1: Read the ledgers

```bash
mkdir -p .claude/temp/gardener
{ date +%s; date '+%Y-%m-%d %H:%M:%S'; } > .claude/temp/gardener/started.txt   # timing ledger (wf pattern)
RATCHET=.claude/metrics/ratchet.tsv; DEBT=.claude/metrics/debt.tsv
echo "== ratchet trend (last 10 rows: run_id dup_pct suppressions prod_cycles files_over_warn) =="
grep -v '^#' "$RATCHET" 2>/dev/null | tail -10
echo "== debt open items (files with warned rows after their last waiver/recovered row) =="
grep -v '^#' "$DEBT" 2>/dev/null | awk -F'\t' '
  $3 ~ /^waiver:/   {streak[$2]=0; next}   # waiver RESETS the streak (never a permanent exemption) — a later warn reopens the item
  $3 ~ /^recovered:/{streak[$2]=0; next}
  {streak[$2]++; last[$2]=$3}
  END{for (f in streak) if (streak[f]>0) print f "\t" last[f] "\tstreak=" streak[f]}'
```

Open item = a file with warned rows after its last waiver/recovered row. Re-verify each is still over the warn threshold (300 SLOC; test/fixture ×1.5) at HEAD before ranking — debt rows are history, HEAD is truth.

## Phase 2: Repo-wide duplication sweep

```bash
if command -v jscpd >/dev/null; then
  jscpd --threshold 100 . 2>/dev/null | tail -15
else
  echo "DUP: unmeasured (jscpd not installed) — falling back to git-grep heuristic for obvious clone blocks"
  # Heuristic: identical non-trivial lines appearing in >1 tracked source file (candidate clones, judge before acting)
  git grep -h -E '.{40,}' -- '*.sh' '*.py' '*.ts' '*.js' '*.cs' 2>/dev/null | sort | uniq -c | sort -rn | awk '$1>1' | head -15
fi
```

Never invent a duplication number: jscpd absent → report `unmeasured` and use the heuristic only to *find candidates*, not to claim a percentage.

## Phase 3: Rank

Priority order (high → low):

1. **Escalated debt** — open debt items with a 3+ streak of non-decreasing SLOC (these are blocking `/wf` runs right now)
2. **Duplication clusters** — largest cloned blocks first (jscpd output or heuristic candidates)
3. **files_over_warn trend** — files driving a rising last column in ratchet.tsv

Print the ranked table: `rank | item | kind (debt|dup|trend) | proposed action (named extraction / dedup target)`. Each proposed action must be a single small extraction or dedup — one responsibility per item.

**If `--dry-run`: STOP here.** Print the ranked plan and exit — no edits, no commits.

## Phase 4: Execute top-K

For each of the top K items, run it as a separate small `/wf --tier=small` task (one extraction/dedup each, own commit):

- Debt item → "extract <named responsibility> from <file> into <target>" — goal: file drops below the warn threshold (the next `/wf` run appends the `recovered:` streak-breaker row automatically).
- Dup cluster → "deduplicate <block> shared by <files> into one definition".
- Each task gets its own commit with the standard `Assisted-by:` trailer; never batch multiple items into one commit (keeps batch size small — the DORA gate applies to the gardener too).
- An item that can't be safely extracted → record a waiver row in debt.tsv instead, with an honest reason: `printf '%s\t%s\twaiver:%s\n' "$(date -u +%Y%m%dT%H%M%SZ)" "<file>" "<reason>" >> .claude/metrics/debt.tsv`

Circuit breaker: an item's quick test fails 3× → skip it, report honestly, move to the next item. Never claim an item closed without its EXECUTION_BLOCK.

## Phase 5: Receipt

```bash
LEDGER=".claude/temp/gardener/started.txt"   # written at Phase 1 start
if [ ! -f "$LEDGER" ]; then echo "⏱ gardener | TOTAL UNVERIFIED (start stamp not found)"
else
  S=$(sed -n 1p "$LEDGER"); SH=$(sed -n 2p "$LEDGER"); E=$(date +%s); EH=$(date '+%Y-%m-%d %H:%M:%S'); T=$((E - S))
  echo "⏱ gardener | $SH → $EH | TOTAL $((T/60))m $((T%60))s"
fi
```

Final report: items closed (with commit SHAs), items waived (with reasons), items skipped, ledger rows appended (debt.tsv waivers/recoveries), then the `⏱ gardener` line. Totals are measured from the ledger, never estimated.

---

## User's Task

$ARGUMENTS
