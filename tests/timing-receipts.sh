#!/usr/bin/env bash
# tests/timing-receipts.sh — quick test for one-line timing receipts
# Spec: .claude/temp/spec.md (wf v23, 11-jun-2026)
# Exit 0 only if ALL assertions pass. Prints one PASS:/FAIL: line per assertion.

set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

FAILURES=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAILURES=$((FAILURES + 1)); }

THINK=.claude/commands/think.md
REFLECT=.claude/commands/reflect.md
WF=.claude/commands/wf.md
R=.claude/commands/r.md
CODEX_WF=codex/.agents/skills/wf/SKILL.md
CODEX_RESEARCH=codex/.agents/skills/research/SKILL.md

# 1. think.md has the timing ledger path
if grep -Eq 'temp/think/.*started\.txt' "$THINK" 2>/dev/null; then
  pass "think.md contains timing ledger path (temp/think/.*started.txt)"
else
  fail "think.md missing timing ledger path (temp/think/.*started.txt)"
fi

# 2. think.md has the one-line receipt marker
if grep -q '⏱' "$THINK" 2>/dev/null; then
  pass "think.md contains receipt marker ⏱"
else
  fail "think.md missing receipt marker ⏱"
fi

# 3. reflect.md must stay timing-free (case-insensitive)
if grep -Eiq 'wall time|timing ledger|started\.txt|⏱' "$REFLECT" 2>/dev/null; then
  fail "reflect.md contains timing references (must be timing-free)"
else
  pass "reflect.md is timing-free"
fi

# 4. Repo-wide (tracked files, excluding tests/): WF TIMING RECEIPT box removed
WF_BOX_HITS=$(git grep -l 'WF TIMING RECEIPT' -- ':!tests/' 2>/dev/null)
if [ -z "$WF_BOX_HITS" ]; then
  pass "no tracked file contains 'WF TIMING RECEIPT' (outside tests/)"
else
  fail "'WF TIMING RECEIPT' still present in: $(echo "$WF_BOX_HITS" | tr '\n' ' ')"
fi

# 5. Repo-wide (tracked files, excluding tests/): RESEARCH TIMING RECEIPT box removed
RESEARCH_BOX_HITS=$(git grep -l 'RESEARCH TIMING RECEIPT' -- ':!tests/' 2>/dev/null)
if [ -z "$RESEARCH_BOX_HITS" ]; then
  pass "no tracked file contains 'RESEARCH TIMING RECEIPT' (outside tests/)"
else
  fail "'RESEARCH TIMING RECEIPT' still present in: $(echo "$RESEARCH_BOX_HITS" | tr '\n' ' ')"
fi

# 6. ⏱ present in wf.md, r.md, and both Codex SKILL.md files
for f in "$WF" "$R" "$CODEX_WF" "$CODEX_RESEARCH"; do
  if grep -q '⏱' "$f" 2>/dev/null; then
    pass "⏱ present in $f"
  else
    fail "⏱ missing in $f"
  fi
done

# 7. CLAUDE.md EXECUTION_BLOCK has a TIMING: row
if grep -q 'TIMING:' CLAUDE.md 2>/dev/null; then
  pass "CLAUDE.md has TIMING: row"
else
  fail "CLAUDE.md missing TIMING: row"
fi

# 8. Banner sync: literal 'wf v24 (11-jun-2026)' in wf.md, CLAUDE.md, README.md
BANNER='wf v24 (11-jun-2026)'
for f in "$WF" CLAUDE.md README.md; do
  if grep -Fq "$BANNER" "$f" 2>/dev/null; then
    pass "banner '$BANNER' present in $f"
  else
    fail "banner '$BANNER' missing in $f"
  fi
done

# 9. wf.md receipt name is versioned on BOTH paths (success + UNVERIFIED)
WF_V24_LINES=$(grep -c '⏱ wf v24' "$WF" 2>/dev/null); WF_V24_LINES=${WF_V24_LINES:-0}
if [ "$WF_V24_LINES" -ge 2 ]; then
  pass "wf.md has versioned receipt on both success and UNVERIFIED paths ($WF_V24_LINES lines)"
else
  fail "wf.md versioned receipt lines: $WF_V24_LINES (need >=2: success + UNVERIFIED)"
fi

# 10. research receipts carry the mode (graceful when unset) in r.md and Codex research skill
for f in "$R" "$CODEX_RESEARCH"; do
  if grep -Fq 'MODE:+' "$f" 2>/dev/null; then
    pass "research receipt carries mode via \${MODE:+ (...)} in $f"
  else
    fail "research receipt missing mode interpolation in $f"
  fi
done

# 11. UNVERIFIED fallback literal pinned in ALL 5 receipt surfaces (coverage-cop gap 1)
UNVERIFIED='TOTAL UNVERIFIED (start stamp not found)'
for f in "$WF" "$R" "$THINK" "$CODEX_WF" "$CODEX_RESEARCH"; do
  if grep -Fq "$UNVERIFIED" "$f" 2>/dev/null; then
    pass "UNVERIFIED fallback present in $f"
  else
    fail "UNVERIFIED fallback missing in $f"
  fi
done

# 12. Full end-timestamp format (Codex plan finding #3 fix) — >=2 per receipt surface
FULLTS="date '+%Y-%m-%d %H:%M:%S'"
for f in "$WF" "$R" "$THINK" "$CODEX_WF" "$CODEX_RESEARCH"; do
  N=$(grep -Fc "$FULLTS" "$f" 2>/dev/null); N=${N:-0}
  if [ "$N" -ge 2 ]; then
    pass "full timestamp format x$N in $f"
  else
    fail "full timestamp format only x$N in $f (need >=2: ledger write + receipt EH)"
  fi
done

# 13. think.md uses the exact 2-line ledger write (epoch + human)
if grep -Fq "{ date +%s; date '+%Y-%m-%d %H:%M:%S'; }" "$THINK" 2>/dev/null; then
  pass "think.md has the 2-line ledger write (epoch + human)"
else
  fail "think.md missing the 2-line ledger write pattern"
fi

# 14. Never-estimate prose survives in all 6 surfaces
for f in "$WF" "$R" "$THINK" "$CODEX_WF" "$CODEX_RESEARCH" CLAUDE.md; do
  if grep -Eiq 'never estimat|not estimat' "$f" 2>/dev/null; then
    pass "never-estimate prose present in $f"
  else
    fail "never-estimate prose missing in $f"
  fi
done

# 15. CLAUDE.md old STARTED:/ENDED: EXECUTION_BLOCK rows stay gone
if grep -Eq '^│ (STARTED|ENDED):' CLAUDE.md 2>/dev/null; then
  fail "CLAUDE.md still has old STARTED:/ENDED: rows"
else
  pass "CLAUDE.md old STARTED:/ENDED: rows absent"
fi

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: ALL ASSERTIONS PASSED"
  exit 0
else
  echo "RESULT: $FAILURES assertion(s) FAILED"
  exit 1
fi
