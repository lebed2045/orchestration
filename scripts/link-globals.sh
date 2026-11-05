#!/usr/bin/env bash
# link-globals.sh — point this machine's global agent files at this checkout,
# so host and VM share one live tree. See global/README.md for the layout.
# Updated: 05-nov-2026
#
#   status   (default) show the state of every entry on this machine
#   collect  copy this machine's CLAUDE.md / AGENTS.md into global/_incoming/<host>-<time>/
#            for merging; changes nothing on this machine
#   link     back up whatever is there, then symlink every entry into this checkout;
#            a machine's reflections folder is first copied whole into global/inbox/ (unreviewed reflections)
#
# The checkout path is resolved from this script's own location, so the same
# script works on the host and in the VM even though the paths differ.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
HOST="$(hostname -s)"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"   # pid keeps two runs in one second apart
BACKUP="$HOME/.agent-link-backups/$STAMP"
INCOMING="$ROOT/global/_incoming/$HOST-$STAMP"
# each machine's incident log gets its own folder: global/inbox/vm-claude, global/inbox/host-codex, ...
if [ "$(sysctl -n kern.hv_vmm_present 2>/dev/null || echo 0)" = 1 ]; then MACHINE=vm; else MACHINE=host; fi

# <path under $HOME>|<path under this checkout>
# Entries under global/ are private (gitignored); a missing one is seeded from this machine.
# Claude Code and Codex load the same rules file. @MACHINE@ becomes vm or host.
# MCP configs point at ~/.agents/bin/agy-peer-mcp, so only these links know where the checkout is.
ENTRIES='
.claude/CLAUDE.md|global/AGENTS.md
.codex/AGENTS.md|global/AGENTS.md
.claude/reflections|global/inbox/@MACHINE@-claude/reflections
.codex/reflections|global/inbox/@MACHINE@-codex/reflections
.claude/commands/workflow.md|.claude/commands/workflow.md
.claude/commands/wf.md|.claude/commands/wf.md
.claude/commands/research.md|.claude/commands/research.md
.claude/commands/r.md|.claude/commands/r.md
.claude/commands/think.md|.claude/commands/think.md
.claude/commands/reflect.md|.claude/commands/reflect.md
.claude/commands/sweep.md|.claude/commands/sweep.md
.claude/commands/gardener.md|.claude/commands/gardener.md
.claude/commands/tl.md|.claude/commands/tl.md
.claude/agents/code-simplifier.md|.claude/agents/code-simplifier.md
.claude/agents/coherence-cop.md|.claude/agents/coherence-cop.md
.claude/agents/coverage-cop.md|.claude/agents/coverage-cop.md
.claude/agents/metrics-cop.md|.claude/agents/metrics-cop.md
.claude/agents/plan-reviewer.md|.claude/agents/plan-reviewer.md
.claude/agents/simplicity-cop.md|.claude/agents/simplicity-cop.md
.claude/agents/verify-app.md|.claude/agents/verify-app.md
.claude/skills/cc|.claude/skills/cc
.codex/skills/in-browser-verify|codex/.agents/skills/in-browser-verify
.agents/skills/reflect|codex/.agents/skills/reflect
.agents/skills/research|codex/.agents/skills/research
.agents/skills/think|codex/.agents/skills/think
.agents/skills/tldr|codex/.agents/skills/tldr
.agents/skills/wf|codex/.agents/skills/wf
.agents/bin/claude-peer|codex/bin/claude-peer
.agents/bin/codex-review-context|codex/bin/codex-review-context
.agents/bin/agy-peer-mcp|codex/bin/agy-peer-mcp
.local/bin/agy-ask|codex/bin/agy-peer-mcp
.claude/hooks/enforce_codex_mcp_policy.py|.claude/hooks/enforce_codex_mcp_policy.py
'

is_private() { case "$1" in global/*) return 0 ;; *) return 1 ;; esac; }

linked_here() { [ -L "$1" ] && [ "$(readlink "$1")" = "$2" ]; }

real_dir() { [ -d "$1" ] && [ ! -L "$1" ]; }

save_incoming() { # <home-relative path> <source file>
  mkdir -p "$INCOMING/$(dirname "$1")"
  if [ -e "$INCOMING/$1" ]; then echo "FAILED      ~/$1 (incoming path already exists)" >&2; exit 1; fi
  cp -p "$2" "$INCOMING/$1"
  echo "  saved for merge: ${INCOMING#"$ROOT"/}/$1"
}

status_one() {
  local src="$HOME/$1" dst="$ROOT/$2"
  if linked_here "$src" "$dst"; then
    if [ -e "$src" ]; then echo "linked      ~/$1"; else echo "DANGLING    ~/$1 (checkout unreachable?)"; fi
  elif [ -L "$src" ]; then
    if [ -e "$src" ]; then echo "other-link  ~/$1 -> $(readlink "$src")"; else echo "DANGLING    ~/$1 -> $(readlink "$src") (not this checkout)"; fi
  elif [ ! -e "$src" ]; then echo "absent      ~/$1"
  elif [ ! -e "$dst" ]; then echo "local-only  ~/$1 (not in checkout yet)"
  elif [ -f "$src" ] && cmp -s "$src" "$dst"; then echo "copy-same   ~/$1"
  else echo "copy-differs ~/$1"
  fi
}

collect_one() {
  local src="$HOME/$1" dst="$ROOT/$2"
  is_private "$2" || return 0
  if real_dir "$src"; then echo "folder      ~/$1 (link copies it into $2)"; return 0; fi
  if [ -L "$src" ] || [ ! -f "$src" ]; then echo "skip        ~/$1 (no local file)"; return 0; fi
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then echo "same        ~/$1"; return 0; fi
  echo "differs     ~/$1"
  save_incoming "$1" "$src"
}

restore_one() { # <home-relative path> <previous link target, or empty>
  local src="$HOME/$1"
  if [ -L "$src" ]; then rm "$src"; fi
  if [ -n "$2" ]; then ln -s "$2" "$src"
  elif [ -e "$BACKUP/$1" ]; then mv "$BACKUP/$1" "$src"
  fi
}

link_one() {
  local src="$HOME/$1" dst="$ROOT/$2"
  if linked_here "$src" "$dst"; then
    if [ -e "$src" ]; then echo "ok          ~/$1"; else echo "DANGLING    ~/$1 (checkout unreachable?)"; fi
    return 0
  fi
  local seeded=""
  if [ ! -e "$dst" ]; then
    if is_private "$2" && [ ! -L "$src" ] && { [ -f "$src" ] || [ -d "$src" ]; }; then
      mkdir -p "$(dirname "$dst")"
      cp -Rp "$src" "$dst"
      seeded=1
      echo "seeded      $2 from ~/$1"
    else
      echo "SKIPPED     ~/$1 ($2 is missing in the checkout)"; return 0
    fi
  fi
  # a private folder is a log: link only once the shared copy is proven identical
  if is_private "$2" && real_dir "$src" && ! diff -rq "$src" "$dst" >/dev/null; then
    if [ -n "$seeded" ]; then echo "FAILED      ~/$1 (copy into $2 is incomplete; this machine is unchanged)" >&2; exit 1; fi
    echo "CONFLICT    ~/$1 (differs from $2; merge by hand, nothing changed)"; return 0
  fi
  local old_link=""
  if [ -L "$src" ]; then
    old_link="$(readlink "$src")"
    mkdir -p "$BACKUP"
    echo "$1 -> $old_link" >> "$BACKUP/replaced-links.txt"
    rm "$src"
  elif [ -e "$src" ]; then
    if is_private "$2" && [ -f "$src" ] && ! cmp -s "$src" "$dst"; then save_incoming "$1" "$src"; fi
    mkdir -p "$BACKUP/$(dirname "$1")"
    if [ -e "$BACKUP/$1" ]; then echo "FAILED      ~/$1 (backup path already exists)" >&2; exit 1; fi
    mv "$src" "$BACKUP/$1"
  fi
  mkdir -p "$(dirname "$src")"
  # the link must exist AND resolve; otherwise put the previous state back
  if ! ln -s "$dst" "$src" || [ ! -e "$src" ]; then
    if restore_one "$1" "$old_link"; then echo "FAILED      ~/$1 (previous state restored)" >&2
    else echo "FAILED      ~/$1 — NOT restored; previous state is under $BACKUP" >&2; fi
    exit 1
  fi
  echo "linked      ~/$1"
}

cmd="${1:-status}"
case "$cmd" in status|collect|link) ;; *) echo "usage: $0 [status|collect|link]" >&2; exit 2 ;; esac

echo "checkout: $ROOT   machine: $HOST"
echo "$ENTRIES" | while IFS='|' read -r home_rel tree_rel; do
  [ -n "$home_rel" ] || continue
  "${cmd}_one" "$home_rel" "${tree_rel/@MACHINE@/$MACHINE}"
done
if [ "$cmd" = link ] && [ -d "$BACKUP" ]; then echo "previous files kept in: $BACKUP"; fi
