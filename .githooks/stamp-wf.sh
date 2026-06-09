#!/bin/sh
# stamp-wf.sh — make wf.md's banner self-truthful, then sync to the global copy.
#
# Source of truth = line 3 of wf.md:
#   **WF_VERSION:** `vN` · **WF_COMMITTED:** `DD-mmm-YYYY` · ...
# This script:
#   1. rewrites WF_COMMITTED to today's date (DD-mmm-YYYY, lowercase month)
#   2. propagates vN (read from line 3) into the verbatim run-banner (line ~5)
#      and the ORCHESTRATION COMPLETE output line (line ~513)
#   3. copies the result to ~/.claude/commands/wf.md so global == project
#
# Version (vN) stays a manual human decision (edit line 3). The DATE and the
# propagation of vN everywhere else are mechanical — that's what this automates.
set -e
cd "$(git rev-parse --show-toplevel)"
F=".claude/commands/wf.md"
[ -f "$F" ] || { echo "stamp-wf: $F not found"; exit 1; }

TODAY=$(date +%d-%b-%Y | tr 'A-Z' 'a-z')
VER=$(sed -n '3p' "$F" | grep -oE 'v[0-9]+' | head -1)
[ -n "$VER" ] || { echo "stamp-wf: could not read WF_VERSION from line 3"; exit 1; }

# 1. WF_COMMITTED date  (match the date without touching the surrounding backticks)
sed -i '' -E "s/(WF_COMMITTED:[^0-9]*)[0-9]{2}-[a-z]{3}-[0-9]{4}/\1${TODAY}/" "$F"
# 2a. verbatim run-banner:  wf vN (DD-mmm-YYYY)
sed -i '' -E "s/wf v[0-9]+ \([0-9]{2}-[a-z]{3}-[0-9]{4}\)/wf ${VER} (${TODAY})/" "$F"
# 2b. ORCHESTRATION COMPLETE output line:  wf vN, tier=
sed -i '' -E "s/wf v[0-9]+, tier=/wf ${VER}, tier=/" "$F"

# 3. sync to global
cp "$F" "$HOME/.claude/commands/wf.md"
echo "stamp-wf: ${VER} @ ${TODAY} — repo + global synced"
