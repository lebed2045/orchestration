#!/usr/bin/env bash
# End-to-end test for scripts/link-globals.sh against a throwaway checkout and two
# throwaway homes (first machine seeds, second machine joins). Touches nothing real.
# BLIND SPOT: does not cover a checkout on a network mount going away mid-run.
set -eu

SRC="$(cd "$(dirname "$0")/.." && pwd -P)/scripts/link-globals.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
TREE="$T/tree"; H1="$T/home1"; H2="$T/home2"
fail() { echo "FAIL: $1" >&2; exit 1; }
run() { HOME="$1" bash "$TREE/scripts/link-globals.sh" "$2"; }

mkdir -p "$TREE/scripts" "$TREE/.claude/commands" "$TREE/codex/.agents/skills/wf" "$T/old/wf"
cp "$SRC" "$TREE/scripts/"
echo "repo workflow" > "$TREE/.claude/commands/workflow.md"
TREE="$(cd "$TREE" && pwd -P)"

for h in "$H1" "$H2"; do mkdir -p "$h/.claude/commands" "$h/.codex" "$h/.agents/skills"; done
echo "vm rules" > "$H1/.claude/CLAUDE.md";   echo "vm agents" > "$H1/.codex/AGENTS.md"
echo "host rules" > "$H2/.claude/CLAUDE.md"; echo "vm agents" > "$H2/.codex/AGENTS.md"
echo "stale copy" > "$H1/.claude/commands/workflow.md"
mkdir -p "$H1/.claude/reflections/archive" "$H2/.claude/reflections"
echo "vm incident" > "$H1/.claude/reflections/incidents.jsonl"; echo "old" > "$H1/.claude/reflections/archive/a.md"
echo "host incident" > "$H2/.claude/reflections/incidents.jsonl"
ln -s "$T/old/wf" "$H1/.agents/skills/wf"

# collect changes nothing on the machine
run "$H1" collect >/dev/null
[ -f "$H1/.claude/CLAUDE.md" ] && [ ! -L "$H1/.claude/CLAUDE.md" ] || fail "collect modified the machine"
ls "$TREE"/global/_incoming/*/.claude/CLAUDE.md >/dev/null 2>&1 || fail "collect saved nothing"

# first machine: seeds the private files, replaces copy + old link, keeps backups
out="$(run "$H1" link)"
[ "$(readlink "$H1/.claude/CLAUDE.md")" = "$TREE/global/AGENTS.md" ] || fail "CLAUDE.md not linked"
[ "$(readlink "$H1/.codex/AGENTS.md")" = "$TREE/global/AGENTS.md" ] || fail "both agents are not on one rules file"
[ "$(cat "$TREE/global/AGENTS.md")" = "vm rules" ] || fail "seed content wrong"
grep -rqx "vm agents" "$TREE/global/_incoming" || fail "the replaced AGENTS.md was not saved for merge"
[ "$(cat "$H1/.claude/commands/workflow.md")" = "repo workflow" ] || fail "command not linked to checkout"
[ "$(readlink "$H1/.agents/skills/wf")" = "$TREE/codex/.agents/skills/wf" ] || fail "old link not repointed"
[ "$(cat "$H1"/.agent-link-backups/*/.claude/commands/workflow.md)" = "stale copy" ] || fail "copy not backed up"
grep -q "old/wf" "$H1"/.agent-link-backups/*/replaced-links.txt || fail "old link target not recorded"
echo "$out" | grep -q "SKIPPED     ~/.claude/commands/wf.md" || fail "missing target was not skipped"
[ ! -e "$H1/.claude/commands/wf.md" ] && [ ! -L "$H1/.claude/commands/wf.md" ] || fail "dangling link created"

# the incident log moves into the shared log folder whole, stays writable through the link, and is backed up
LOG="$(echo "$TREE"/global/log/*-claude/reflections)"
[ -L "$H1/.claude/reflections" ] && [ "$(readlink "$H1/.claude/reflections")" = "$LOG" ] || fail "reflections not linked into the log"
[ "$(cat "$LOG/archive/a.md")" = "old" ] || fail "log folder not copied whole"
[ "$(cat "$H1"/.agent-link-backups/*/.claude/reflections/incidents.jsonl)" = "vm incident" ] || fail "reflections not backed up"
echo "new incident" >> "$H1/.claude/reflections/incidents.jsonl"
grep -qx "new incident" "$LOG/incidents.jsonl" || fail "a new incident did not land in the log"

# idempotent
run "$H1" link | grep -q "linked " && fail "second run re-linked"

# second machine: its differing file is saved for merge and backed up, never lost
run "$H2" link >/dev/null
[ "$(cat "$H2/.claude/CLAUDE.md")" = "vm rules" ] || fail "second machine not on shared file"
grep -rqx "host rules" "$TREE/global/_incoming" || fail "second machine's file not saved for merge"
[ "$(cat "$H2"/.agent-link-backups/*/.claude/CLAUDE.md)" = "host rules" ] || fail "second machine's file not backed up"

# two different incident logs are never merged or replaced silently
run "$H2" link | grep -q "CONFLICT    ~/.claude/reflections" || fail "differing log folders not reported"
[ ! -L "$H2/.claude/reflections" ] && [ "$(cat "$H2/.claude/reflections/incidents.jsonl")" = "host incident" ] || fail "second machine's log was touched"
grep -q "host incident" "$LOG/incidents.jsonl" && fail "second machine's log leaked into the first one's"

# a failed link never leaves the machine without its file or its previous link
H3="$T/home3"; mkdir -p "$H3/.claude" "$H3/.agents/skills" "$T/bin"
echo "third rules" > "$H3/.claude/CLAUDE.md"; ln -s "$T/old/wf" "$H3/.agents/skills/wf"
printf '#!/bin/sh\n[ "$2" = "$FAIL_ON" ] && exit 1\nexec /bin/ln "$@"\n' > "$T/bin/ln"; chmod +x "$T/bin/ln"
FAIL_ON="$TREE/global/AGENTS.md" PATH="$T/bin:$PATH" run "$H3" link >/dev/null 2>&1 && fail "failed ln was not reported"
[ ! -L "$H3/.claude/CLAUDE.md" ] && [ "$(cat "$H3/.claude/CLAUDE.md")" = "third rules" ] || fail "file not restored after failed ln"
FAIL_ON="$TREE/codex/.agents/skills/wf" PATH="$T/bin:$PATH" run "$H3" link >/dev/null 2>&1 && fail "failed ln was not reported"
[ "$(readlink "$H3/.agents/skills/wf")" = "$T/old/wf" ] || fail "previous link not restored after failed ln"

# an unreachable checkout is reported, not hidden
mv "$TREE/global" "$T/global.off"
run "$H1" status | grep -q "DANGLING    ~/.claude/CLAUDE.md" || fail "dangling link not reported"
run "$H1" link | grep -q "DANGLING    ~/.claude/CLAUDE.md" || fail "link reported a dangling link as ok"
run "$H1" status | grep -q "DANGLING    ~/.claude/reflections" || fail "dangling log folder not reported"

# a link to somewhere else that no longer resolves is called out too
rm -rf "$T/old/wf"
run "$H3" status | grep -q "DANGLING    ~/.agents/skills/wf -> " || fail "foreign dangling link not reported"

echo "PASS link-globals"
