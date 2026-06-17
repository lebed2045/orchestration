#!/bin/sh
# stamp-wf.sh — make workflow.md's banner self-truthful, then sync to the global copy.
#
# Source of truth = the **WF_VERSION:** line of workflow.md (found by pattern — YAML
# frontmatter may precede it, so never assume a fixed line number):
#   **WF_VERSION:** `vN` · **WF_COMMITTED:** `DD-mmm-YYYY` · ...
# This script:
#   1. rewrites WF_COMMITTED to today's date (DD-mmm-YYYY, lowercase month)
#   2. propagates vN (read from that line) into the verbatim run-banner,
#      the timing-receipt lines, and the ORCHESTRATION COMPLETE output line
#   3. copies the result to ~/.claude/commands/workflow.md so global == project
#
# Version (vN) stays a manual human decision (edit the WF_VERSION line). The DATE and the
# propagation of vN everywhere else are mechanical — that's what this automates.
set -e
cd "$(git rev-parse --show-toplevel)"
F=".claude/commands/workflow.md"
[ -f "$F" ] || { echo "stamp-wf: $F not found"; exit 1; }

TODAY=$(LC_ALL=C date +%d-%b-%Y | tr 'A-Z' 'a-z')   # LC_ALL=C: month abbreviation stays English regardless of locale
VER=$(grep -m1 '^\*\*WF_VERSION:\*\*' "$F" | grep -oE 'v[0-9]+(\.[0-9]+)?' | head -1)
[ -n "$VER" ] || { echo "stamp-wf: could not find a **WF_VERSION:** line in $F"; exit 1; }

# 1. WF_COMMITTED date  (match the date without touching the surrounding backticks)
sed -i '' -E "s/(WF_COMMITTED:[^0-9]*)[0-9]{2}-[a-z]{3}-[0-9]{4}/\1${TODAY}/" "$F"
# 2a. verbatim run-banner:  workflow vN (DD-mmm-YYYY)
sed -i '' -E "s/workflow v[0-9]+(\.[0-9]+)? \([0-9]{2}-[a-z]{3}-[0-9]{4}\)/workflow ${VER} (${TODAY})/" "$F"
# 2b. timing-receipt lines:  ⏱ workflow vN tier=
sed -i '' -E "s/workflow v[0-9]+(\.[0-9]+)? tier=/workflow ${VER} tier=/" "$F"
# 2c. ORCHESTRATION COMPLETE output line:  workflow vN, tier=
sed -i '' -E "s/workflow v[0-9]+(\.[0-9]+)?, tier=/workflow ${VER}, tier=/" "$F"

# 2d. propagate the dated run-banner to the sibling files that carry it verbatim, so
#     workflow.md / CLAUDE.md / README.md never desync. The pre-commit hook force-stages all
#     three (and refuses if any had unstaged edits, so this only ever stages the banner change).
for SIB in CLAUDE.md README.md; do
  [ -f "$SIB" ] && sed -i '' -E "s/workflow v[0-9]+(\.[0-9]+)? \([0-9]{2}-[a-z]{3}-[0-9]{4}\)/workflow ${VER} (${TODAY})/g" "$SIB"
done

# 3. sync to global
cp "$F" "$HOME/.claude/commands/workflow.md"
echo "stamp-wf: ${VER} @ ${TODAY} — repo + global synced"
