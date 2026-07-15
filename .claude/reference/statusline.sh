#!/bin/bash
# Codex-style statusline:
#   Opus-4.8-high · …/projects/my-repo · master 3~ · Context 26%/200k
#
# Wire it up with a statusLine key in settings.json:
#   "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" }
#
# Segments, ' · ' separated:
#   model-effort    (one token, one color; effort omitted when unsupported)
#   cwd             (tilde-abbreviated; prefix-truncated to fit $COLUMNS)
#   branch + dirty  (dirty count hidden when the tree is clean)
#   context         (pct shade climbs with usage)
#
# The cwd is the only elastic segment: everything else is short and load-bearing,
# so the path gives up width first. It degrades last-2-segments → last-1 → chars,
# always keeping the tail (the specific dir) and eating the prefix.
#
# Updated: 15-jul-2026

set -f

input=$(cat)

if [ -z "$input" ]; then
    printf "Claude"
    exit 0
fi

dim='\033[2m'
bold='\033[1m'
reset='\033[0m'

# Colors sampled pixel-exact from the codex screenshot (539x80, bg #393939):
# path #ABDFA7, branch #8FB3EF, context #F2B590, separators #8F8F8F.
codex_path='\033[38;2;171;223;167m'    # #ABDFA7 — codex greens the path
codex_branch='\033[38;2;143;179;239m'  # #8FB3EF — and blues the branch

# Model keeps a per-family hue so Opus/Fable/Sonnet stay tellable apart at a
# glance, but the whole "Opus-4.8-high" token is a single color, codex-style.
blue='\033[38;2;0;153;255m'

# Context ramp: ONE orange family (hue pinned near codex's 22.7deg) with
# salience climbing via saturation, so the band reads as "how much trouble am I
# in" without changing color identity. The top band cannot also win on luminance
# — red is inherently darker than peach — so it takes bold instead of a brighter
# hue. Contrast vs #393939: 4.39 / 5.55 / 6.48 / 5.42 (+bold).
ctx_safe='\033[38;2;199;149;117m'    # #C79575  <15%    muted, recedes
ctx_onset='\033[38;2;226;167;131m'   # #E2A783  15-25%
ctx_base='\033[38;2;242;181;144m'    # #F2B590  25-50%  exactly codex's orange
ctx_hot='\033[38;2;255;150;112m'     # #FF9670  >=50%   vivid, rendered bold

sep="${dim} · ${reset}"
sep_w=3   # visible width of "$sep" — colors are zero-width

# Single jq pass — the script runs on every render, so avoid 6 forks.
eval "$(echo "$input" | jq -r '
    @sh "model_name=\(.model.display_name // "Claude")",
    @sh "cwd=\(.workspace.current_dir // "")",
    @sh "size=\(.context_window.context_window_size // 200000)",
    @sh "input_tokens=\(.context_window.current_usage.input_tokens // 0)",
    @sh "cache_create=\(.context_window.current_usage.cache_creation_input_tokens // 0)",
    @sh "cache_read=\(.context_window.current_usage.cache_read_input_tokens // 0)",
    @sh "effort_level=\(.effort.level // "")"
')"

# ---- model-effort -----------------------------------------------------------
# Per-family model color: Fable vs Opus distinguishable at a glance
model_lower=$(printf '%s' "$model_name" | LC_ALL=C tr '[:upper:]' '[:lower:]')
case "$model_lower" in
    *fable*)  model_color='\033[38;2;200;120;255m' ;;  # violet — current flagship
    *opus*)   model_color="$blue" ;;                    # unchanged — muscle memory
    *sonnet*) model_color='\033[38;2;0;200;190m' ;;     # teal
    *)        model_color="$blue" ;;
esac

# "Opus 4.8" + "high" -> "Opus-4.8-high", codex's single-token shape.
# effort.level: low|medium|high|xhigh|max (ultracode reports as xhigh).
# Absent when the current model does not support the effort parameter → omit it.
plain_model="${model_name// /-}"
[ -n "$effort_level" ] && plain_model="${plain_model}-${effort_level}"

# ---- cwd --------------------------------------------------------------------
[ -z "$cwd" ] && cwd=$(pwd)
# Keep the real path for git -C; $cwd below becomes a display string ("~/x"),
# and a literal ~ does not expand inside a variable.
raw_cwd="$cwd"
case "$cwd" in
    "$HOME")   cwd="~" ;;
    "$HOME"/*) cwd="~/${cwd#"$HOME"/}" ;;
esac

IFS='/' read -r -a _parts <<< "$cwd"
_segs=()
for _p in "${_parts[@]}"; do [ -n "$_p" ] && _segs+=("$_p"); done

# Last $1 path segments as "…/a/b"; the whole path when it has no more than $1.
dir_keep() {
    local keep=$1 n=${#_segs[@]} out="" i
    if [ "$n" -le "$keep" ]; then
        printf '%s' "$cwd"
        return
    fi
    for ((i = n - keep; i < n; i++)); do out="${out}/${_segs[$i]}"; done
    printf '…%s' "$out"
}

# ---- branch + dirty ---------------------------------------------------------
# -C "$raw_cwd" pins git to the dir shown in the segment above. Without it git
# reads the shell's cwd, which can differ from workspace.current_dir (/add-dir,
# or a host that spawns the script elsewhere) — branch would contradict the path.
#
# CACHED: `git status --short` costs ~555ms on the Unity repo over SMB (the
# untracked scan walking Library/), and this script runs on every render. A 2s
# TTL keeps the bar responsive; the count can lag a couple of seconds, which is
# fine for a cosmetic number. `-uno` would be 13x faster but stops counting
# untracked files — i.e. the new files you just wrote — so it is NOT used.
git_cache_dir="${TMPDIR:-/tmp}/claude-statusline"
git_cache_ttl=2

mtime_of() {
    stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0
}

branch_seg=""
plain_branch=""
if git -C "$raw_cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    cache_key=$(printf '%s' "$raw_cwd" | cksum | cut -d' ' -f1)
    cache_file="${git_cache_dir}/git-${cache_key}"

    cache_age=$(( $(date +%s) - $(mtime_of "$cache_file") ))

    if [ -s "$cache_file" ] && [ "$cache_age" -lt "$git_cache_ttl" ]; then
        IFS=$'\t' read -r branch dirty < "$cache_file"
    else
        branch=$(git -C "$raw_cwd" branch --show-current 2>/dev/null)
        [ -z "$branch" ] && branch="detached"
        dirty=$(git -C "$raw_cwd" status --short 2>/dev/null | wc -l | tr -d ' ')
        # Write via temp + mv so a concurrent render never reads a half-line.
        mkdir -p "$git_cache_dir" 2>/dev/null
        tmp="${cache_file}.$$"
        if printf '%s\t%s\n' "$branch" "$dirty" > "$tmp" 2>/dev/null; then
            mv -f "$tmp" "$cache_file" 2>/dev/null || rm -f "$tmp" 2>/dev/null
        fi
    fi

    # Dirty count shares the branch color — it is a fact *about* the branch.
    dirty_str=""
    plain_branch="$branch"
    if [ "$dirty" -gt 0 ] 2>/dev/null; then
        dirty_str=" ${dirty}~"
        plain_branch="${branch}${dirty_str}"
    fi

    branch_seg="${sep}${codex_branch}${branch}${dirty_str}${reset}"
fi

# ---- context ----------------------------------------------------------------
[ "$size" -eq 0 ] 2>/dev/null && size=200000
current=$((input_tokens + cache_create + cache_read))

pct=$((current * 100 / size))
[ "$pct" -gt 100 ] && pct=100

# Bands track context-rot degradation as % of the window, per research
# (.claude/reference/opus-4-8-1m-context-degradation-threshold.md):
#    <15% safe / 15-25% degradation onset /
#    25-50% degrading (compact/retrieve) / >=50% ceiling.
# Percent-based, so it behaves identically on a 200k or a 1M window.
if   [ "$pct" -ge 50 ]; then pct_color="${bold}${ctx_hot}"
elif [ "$pct" -ge 25 ]; then pct_color="$ctx_base"
elif [ "$pct" -ge 15 ]; then pct_color="$ctx_onset"
else pct_color="$ctx_safe"
fi

if [ "$size" -ge 1000000 ]; then
    size_fmt=$(awk "BEGIN {printf \"%.0fM\", $size / 1000000}")
elif [ "$size" -ge 1000 ]; then
    size_fmt=$(awk "BEGIN {printf \"%.0fk\", $size / 1000}")
else
    size_fmt="$size"
fi

# Label and window size sit at codex's base orange; only the number shades, so
# at 25-50% the whole segment is uniformly codex-colored.
ctx_seg="${sep}${ctx_base}Context ${reset}${pct_color}${pct}%${reset}${ctx_base}/${size_fmt}${reset}"
plain_ctx="Context ${pct}%/${size_fmt}"

# ---- fit the cwd to the terminal --------------------------------------------
# Claude Code captures stdout, so tput/stty cannot see the terminal — it exports
# COLUMNS instead (v2.1.153+). Unset/garbage → skip fitting, keep the last-2 form.
dir_str=$(dir_keep 2)

cols=${COLUMNS:-0}
case "$cols" in ''|*[!0-9]*) cols=0 ;; esac

dir_seg="${sep}${codex_path}${dir_str}${reset}"

if [ "$cols" -gt 0 ]; then
    # Everything that is not the path, plus the separator preceding the path.
    overhead=$(( ${#plain_model} + sep_w + ${#plain_ctx} + sep_w ))
    [ -n "$plain_branch" ] && overhead=$(( overhead + sep_w + ${#plain_branch} ))

    budget=$(( cols - overhead - 1 ))   # -1 margin so a full-width line cannot wrap

    if [ "$budget" -lt 5 ]; then
        # Under ~5 chars the path can only render as "…", which costs 4 columns
        # (separator included) to say nothing. Drop the segment instead.
        dir_seg=""
    elif [ "${#dir_str}" -gt "$budget" ]; then
        dir_str=$(dir_keep 1)                             # …/sim-vibecoding
        if [ "${#dir_str}" -gt "$budget" ]; then
            dir_str="…${dir_str: -$((budget - 1))}"       # …-vibecoding
        fi
        dir_seg="${sep}${codex_path}${dir_str}${reset}"
    fi
fi

printf "%b" "${model_color}${plain_model}${reset}${dir_seg}${branch_seg}${ctx_seg}"

exit 0
