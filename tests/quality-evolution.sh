#!/usr/bin/env bash
# tests/quality-evolution.sh — quick test for longitudinal quality enforcement
# Spec: .claude/temp/spec.md (wf v24, 11-jun-2026); plan: .claude/temp/architecture.md "TDD test plan"
# Exit 0 only if ALL assertions pass. Prints one PASS:/FAIL: line per assertion.

set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

FAILURES=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAILURES=$((FAILURES + 1)); }

SIMP=.claude/agents/simplicity-cop.md
COHER=.claude/agents/coherence-cop.md
COVER=.claude/agents/coverage-cop.md
METRICS=.claude/agents/metrics-cop.md
WF=.claude/commands/workflow.md
GARDENER=.claude/commands/gardener.md
RATCHET=.claude/metrics/ratchet.tsv
DEBT=.claude/metrics/debt.tsv
QUALREF=.claude/reference/code-quality-metrics.md
TIMTEST=tests/timing-receipts.sh

# 1. simplicity-cop.md: folklore CC>10 REJECT removed
if grep -qF 'Cyclomatic complexity >10 per function? → REJECT' "$SIMP" 2>/dev/null; then
  fail "simplicity-cop.md still contains 'Cyclomatic complexity >10 per function? → REJECT'"
else
  pass "simplicity-cop.md no longer hard-REJECTs on cyclomatic complexity >10"
fi

# 2. simplicity-cop.md: folklore nesting>4 REJECT removed
if grep -qF 'Nesting depth >4? → REJECT' "$SIMP" 2>/dev/null; then
  fail "simplicity-cop.md still contains 'Nesting depth >4? → REJECT'"
else
  pass "simplicity-cop.md no longer hard-REJECTs on nesting depth >4"
fi

# 3. simplicity-cop.md: <50-lines file REJECT removed
if grep -qF 'New file <50 lines? → REJECT' "$SIMP" 2>/dev/null; then
  fail "simplicity-cop.md still contains 'New file <50 lines? → REJECT'"
else
  pass "simplicity-cop.md no longer hard-REJECTs on new file <50 lines"
fi

# 4. simplicity-cop.md: >3-new-files REJECT removed
if grep -qF 'PR adds >3 new files? → REJECT' "$SIMP" 2>/dev/null; then
  fail "simplicity-cop.md still contains 'PR adds >3 new files? → REJECT'"
else
  pass "simplicity-cop.md no longer hard-REJECTs on PR adds >3 new files"
fi

# 5. simplicity-cop.md: Thresholds table ('New files per feature') gone
if grep -qF 'New files per feature' "$SIMP" 2>/dev/null; then
  fail "simplicity-cop.md still contains 'New files per feature' (thresholds table)"
else
  pass "simplicity-cop.md thresholds table ('New files per feature') removed"
fi

# 6. simplicity-cop.md uses BASELINE_SHA
if grep -qF 'BASELINE_SHA' "$SIMP" 2>/dev/null; then
  pass "simplicity-cop.md uses BASELINE_SHA"
else
  fail "simplicity-cop.md missing BASELINE_SHA"
fi

# 7. simplicity-cop.md has AI-specific future-proofing check
if grep -qF 'future-proofing' "$SIMP" 2>/dev/null; then
  pass "simplicity-cop.md contains 'future-proofing' (AI-specific check)"
else
  fail "simplicity-cop.md missing 'future-proofing' (AI-specific check)"
fi

# 8. coverage-cop.md: <80% coverage quota removed
if grep -qF '<80%' "$COVER" 2>/dev/null; then
  fail "coverage-cop.md still contains '<80%' (coverage quota)"
else
  pass "coverage-cop.md coverage quota '<80%' removed"
fi

# 9. coverage-cop.md: edge-cases-per-function quota removed
if grep -qF 'Edge cases per function' "$COVER" 2>/dev/null; then
  fail "coverage-cop.md still contains 'Edge cases per function'"
else
  pass "coverage-cop.md 'Edge cases per function' quota removed"
fi

# 10. coverage-cop.md: hardcoded npm coverage command removed
if grep -qF 'npm test -- --coverage' "$COVER" 2>/dev/null; then
  fail "coverage-cop.md still contains 'npm test -- --coverage'"
else
  pass "coverage-cop.md hardcoded 'npm test -- --coverage' removed"
fi

# 11. coverage-cop.md uses QUICK_TEST_CMD
if grep -qF 'QUICK_TEST_CMD' "$COVER" 2>/dev/null; then
  pass "coverage-cop.md uses QUICK_TEST_CMD"
else
  fail "coverage-cop.md missing QUICK_TEST_CMD"
fi

# 12. coverage-cop.md uses BASELINE_SHA
if grep -qF 'BASELINE_SHA' "$COVER" 2>/dev/null; then
  pass "coverage-cop.md uses BASELINE_SHA"
else
  fail "coverage-cop.md missing BASELINE_SHA"
fi

# 13. coverage-cop.md has weakened-test check for it.skip
if grep -qF 'it.skip' "$COVER" 2>/dev/null; then
  pass "coverage-cop.md contains 'it.skip' (weakened-test check)"
else
  fail "coverage-cop.md missing 'it.skip' (weakened-test check)"
fi

# 14. coverage-cop.md has the key question 'fail against the old behavior'
if grep -qF 'fail against the old behavior' "$COVER" 2>/dev/null; then
  pass "coverage-cop.md contains 'fail against the old behavior'"
else
  fail "coverage-cop.md missing 'fail against the old behavior'"
fi

# 15. coverage-cop.md keeps the TDD-red check 'fails without the fix'
# keep-guard: passes at baseline by design
if grep -qF 'fails without the fix' "$COVER" 2>/dev/null; then
  pass "coverage-cop.md keeps 'fails without the fix' (TDD red regression guard)"
else
  fail "coverage-cop.md lost 'fails without the fix' (TDD red regression guard)"
fi

# 16. Adjudication guardrail in ALL FOUR cop files
for f in "$SIMP" "$COHER" "$COVER" "$METRICS"; do
  if grep -qF 'do not auto-compound into REJECT by count' "$f" 2>/dev/null; then
    pass "adjudication guardrail present in $f"
  else
    fail "adjudication guardrail missing in $f"
  fi
done

# 17. Role boundary line in ALL FOUR cop files
for f in "$SIMP" "$COHER" "$COVER" "$METRICS"; do
  if grep -qF 'Role boundary:' "$f" 2>/dev/null; then
    pass "role boundary line present in $f"
  else
    fail "role boundary line missing in $f"
  fi
done

# 18. metrics-cop.md reads the debt ledger
if grep -qF 'debt.tsv' "$METRICS" 2>/dev/null; then
  pass "metrics-cop.md references debt.tsv"
else
  fail "metrics-cop.md missing debt.tsv reference"
fi

# 19. metrics-cop.md has the 3-consecutive escalation rule
if grep -qF '3 consecutive' "$METRICS" 2>/dev/null; then
  pass "metrics-cop.md contains '3 consecutive' (debt escalation rule)"
else
  fail "metrics-cop.md missing '3 consecutive' (debt escalation rule)"
fi

# 20. workflow.md version line bumped to v0.27
VER_LINE='**WF_VERSION:** `v0.27`'
if grep -qF "$VER_LINE" "$WF" 2>/dev/null; then
  pass "workflow.md contains version line $VER_LINE"
else
  fail "workflow.md missing version line $VER_LINE"
fi

# 21. wf.md references both ledgers
if grep -qF 'ratchet.tsv' "$WF" 2>/dev/null && grep -qF 'debt.tsv' "$WF" 2>/dev/null; then
  pass "wf.md references both ratchet.tsv and debt.tsv"
else
  fail "wf.md missing ratchet.tsv and/or debt.tsv reference"
fi

# 22. workflow.md receipt name versioned to v0.27 on BOTH paths (success + UNVERIFIED)
WF_VER_LINES=$(grep -Fc '⏱ workflow v0.27' "$WF" 2>/dev/null); WF_VER_LINES=${WF_VER_LINES:-0}
if [ "$WF_VER_LINES" -ge 2 ]; then
  pass "workflow.md has v0.27 receipt on both success and UNVERIFIED paths ($WF_VER_LINES lines)"
else
  fail "workflow.md '⏱ workflow v0.27' lines: $WF_VER_LINES (need >=2: success + UNVERIFIED)"
fi

# 23. Banner sync: literal 'workflow v0.27 (13-jun-2026)' in workflow.md, CLAUDE.md, README.md
BANNER='workflow v0.27 (13-jun-2026)'
for f in "$WF" CLAUDE.md README.md; do
  if grep -Fq "$BANNER" "$f" 2>/dev/null; then
    pass "banner '$BANNER' present in $f"
  else
    fail "banner '$BANNER' missing in $f"
  fi
done

# 24. ratchet.tsv exists with >=1 non-comment row of exactly 5 tab-separated fields
RATCHET_ROWS=$(grep -v '^#' "$RATCHET" 2>/dev/null | awk -F'\t' 'NF==5' | wc -l | tr -d ' ')
if [ -f "$RATCHET" ] && [ "$RATCHET_ROWS" -ge 1 ]; then
  pass "ratchet.tsv exists with $RATCHET_ROWS row(s) of 5 tab-separated fields"
else
  fail "ratchet.tsv missing or has no non-comment row with exactly 5 tab-separated fields"
fi

# 25. debt.tsv exists (header comment ok)
if [ -f "$DEBT" ]; then
  pass "debt.tsv exists"
else
  fail "debt.tsv missing"
fi

# 26. gardener.md exists and references debt.tsv
if [ -f "$GARDENER" ] && grep -qF 'debt.tsv' "$GARDENER" 2>/dev/null; then
  pass "gardener.md exists and references debt.tsv"
else
  fail "gardener.md missing or lacks debt.tsv reference"
fi

# 27. CLAUDE.md documents /gardener
if grep -qF '/gardener' CLAUDE.md 2>/dev/null; then
  pass "CLAUDE.md contains /gardener"
else
  fail "CLAUDE.md missing /gardener"
fi

# 28. code-quality-metrics.md documents longitudinal enforcement + waivers
if grep -qF 'Longitudinal' "$QUALREF" 2>/dev/null && grep -qF 'waiver' "$QUALREF" 2>/dev/null; then
  pass "code-quality-metrics.md contains 'Longitudinal' and 'waiver'"
else
  fail "code-quality-metrics.md missing 'Longitudinal' and/or 'waiver'"
fi

# 29. tests/timing-receipts.sh banner synced to v24 (old v23 literal gone)
if grep -qF 'wf v23 (11-jun-2026)' "$TIMTEST" 2>/dev/null; then
  fail "tests/timing-receipts.sh still contains 'wf v23 (11-jun-2026)' (not synced to v24)"
else
  pass "tests/timing-receipts.sh no longer contains 'wf v23 (11-jun-2026)'"
fi

# 30. gardener.md open-items awk: waiver must RESET the streak, never permanently exempt the file.
# Documented contract (gardener.md prose, metrics-cop.md, code-quality-metrics.md): "waiver resets the
# streak" — so a warn → waiver → warn history MUST reopen the item. Extracting and executing the awk
# from the fenced block against a fixture is brittle (sed boundaries break on doc edits), so we assert
# the contract textually instead: no permanent 'waived[' exemption map, and the waiver branch resets
# the streak like the recovered branch does.
if grep -qF 'waived[' "$GARDENER" 2>/dev/null; then
  fail "gardener.md awk still has a permanent 'waived[' exemption (waiver must reset the streak, not exempt the file forever)"
elif grep -F '/^waiver:/' "$GARDENER" 2>/dev/null | grep -qF 'streak[$2]=0'; then
  pass "gardener.md awk resets the streak on waiver rows (no permanent exemption)"
else
  fail "gardener.md awk waiver branch does not reset the streak (missing streak[\$2]=0 on /^waiver:/ rows)"
fi

# 31. Guardrail identity: the adjudication-guardrail paragraph must be byte-identical in all 4 cop files
GUARD_VARIANTS=$(grep -h 'do not auto-compound into REJECT by count' "$SIMP" "$COHER" "$COVER" "$METRICS" 2>/dev/null | sort -u | wc -l | tr -d ' ')
if [ "$GUARD_VARIANTS" = "1" ]; then
  pass "adjudication guardrail is byte-identical across all 4 cop files"
else
  fail "adjudication guardrail differs across cop files ($GUARD_VARIANTS unique variants; need exactly 1)"
fi

# 32. wf.md Phase 9 ratchet block guards the commit when ASSIST_TRAILER is unset (v21 rule: never guess it)
if grep -qF 'ASSIST_TRAILER unset' "$WF" 2>/dev/null; then
  pass "wf.md Phase 9 guards the ratchet commit when ASSIST_TRAILER is unset"
else
  fail "wf.md Phase 9 missing the 'ASSIST_TRAILER unset' commit guard"
fi

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: ALL ASSERTIONS PASSED"
  exit 0
else
  echo "RESULT: $FAILURES assertion(s) FAILED"
  exit 1
fi
