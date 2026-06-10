#!/bin/bash
# Model | context % used (colored bar)

set -f

input=$(cat)

if [ -z "$input" ]; then
    printf "Claude"
    exit 0
fi

blue='\033[38;2;0;153;255m'
green='\033[38;2;0;160;0m'
orange='\033[38;2;255;176;85m'
yellow='\033[38;2;230;200;0m'
red='\033[38;2;255;85;85m'
grey='\033[38;2;140;140;140m'
dim='\033[2m'
reset='\033[0m'

model_name=$(echo "$input" | jq -r '.model.display_name // "Claude"')

# Per-family model color: Fable vs Opus distinguishable at a glance
model_lower=$(printf '%s' "$model_name" | LC_ALL=C tr '[:upper:]' '[:lower:]')
case "$model_lower" in
    *fable*)  model_color='\033[38;2;200;120;255m' ;;  # violet — current flagship
    *opus*)   model_color="$blue" ;;                    # unchanged — muscle memory
    *sonnet*) model_color='\033[38;2;0;200;190m' ;;     # teal
    *)        model_color="$blue" ;;
esac

size=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
[ "$size" -eq 0 ] 2>/dev/null && size=200000

input_tokens=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
current=$(( input_tokens + cache_create + cache_read ))

pct=$(( current * 100 / size ))
[ "$pct" -gt 100 ] && pct=100

# Color tracks context-rot degradation as % of the window, per research
# (.claude/research/opus-4-8-1m-context-degradation-threshold.md):
#   <15% green (safe) / 15-25% yellow (degradation onset) /
#   25-50% orange (degrading — compact/retrieve) / >=50% red (ceiling).
# Percent-based, so it behaves identically on a 200k or a 1M window.
if   [ "$pct" -ge 50 ]; then pct_color="$red"
elif [ "$pct" -ge 25 ]; then pct_color="$orange"
elif [ "$pct" -ge 15 ]; then pct_color="$yellow"
else pct_color="$green"
fi

if [ "$size" -ge 1000000 ]; then
    size_fmt=$(awk "BEGIN {printf \"%.0fM\", $size / 1000000}")
elif [ "$size" -ge 1000 ]; then
    size_fmt=$(awk "BEGIN {printf \"%.0fk\", $size / 1000}")
else
    size_fmt="$size"
fi

# Thinking + reasoning effort come from the statusline stdin JSON (live session
# values, incl. mid-session /effort changes) — NOT from settings.json, where
# alwaysThinkingEnabled is not a real key and always falls back to Off.
thinking_val=$(echo "$input" | jq -r '.thinking.enabled // false')
if [ "$thinking_val" = "true" ]; then
    think="${grey}On${reset}"
else
    think="${grey}Off${reset}"
fi

# effort.level: low|medium|high|xhigh|max (ultracode reports as xhigh).
# Absent when the current model does not support the effort parameter -> hide it.
effort_level=$(echo "$input" | jq -r '.effort.level // empty')
effort_str=""
if [ -n "$effort_level" ]; then
    case "$effort_level" in
        max|xhigh) effort_color="$red" ;;
        high)      effort_color="$orange" ;;
        medium)    effort_color="$yellow" ;;
        *)         effort_color="$green" ;;
    esac
    effort_str=" ${dim}effort:${reset}${effort_color}${effort_level}${reset}"
fi

branch=$(git branch --show-current 2>/dev/null || echo "detached")
dirty=$(git status --short 2>/dev/null | wc -l | tr -d ' ')

dirty_str=""
if [ "$dirty" -gt 0 ]; then
    dirty_str=" ${yellow}${dirty}~${reset}"
fi

printf "%b" "${model_color}${model_name}${reset} ${pct_color}${pct}%${reset}${dim}/${reset}${size_fmt}${effort_str} ${dim}think:${reset}${think} ${green}${branch}${reset}${dirty_str}"

exit 0
