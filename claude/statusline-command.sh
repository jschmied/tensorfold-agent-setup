#!/bin/bash
input=$(cat)

# Extract model, context usage, rate limits, and cwd from JSON
model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
five_hr=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_hr_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_day=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
seven_day_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
cwd=$(echo "$input" | jq -r '.cwd // empty')

# Snapshot the rate limits for Claude to read (atomic replace)
echo "$input" | jq -c '{at: now | floor, session: .session_id, rate_limits}' \
  > ~/.claude/usage-now.json.tmp 2>/dev/null && mv ~/.claude/usage-now.json.tmp ~/.claude/usage-now.json

# History for ~/.claude/usage-report.py: one line when a value changes, else at most every 10 min
if [ -n "$five_hr$seven_day" ]; then
  hist=~/.claude/usage-history.jsonl
  key="$five_hr $seven_day $five_hr_reset $seven_day_reset"
  last_key="" last_at=0
  [ -f ~/.claude/usage-last.txt ] && read -r last_at last_key < ~/.claude/usage-last.txt
  t=$(date +%s)
  if [ "$key" != "$last_key" ] || [ $((t - last_at)) -ge 600 ]; then
    printf '{"at":%s,"h5":%s,"h5_reset":%s,"d7":%s,"d7_reset":%s}\n' "$t" "${five_hr:-null}" \
      "${five_hr_reset:-null}" "${seven_day:-null}" "${seven_day_reset:-null}" >> "$hist"
    echo "$t $key" > ~/.claude/usage-last.txt
  fi
fi

# Format seconds-remaining as compact d/h/m (no seconds); empty if <= 0
format_countdown() {
  local secs="$1"
  [ -z "$secs" ] && return
  case "$secs" in ''|*[!0-9]*) return ;; esac
  [ "$secs" -le 0 ] && return
  local days=$((secs / 86400))
  local hours=$(((secs % 86400) / 3600))
  local mins=$(((secs % 3600) / 60))
  if [ "$days" -gt 0 ]; then
    printf '%dd%dh' "$days" "$hours"
  elif [ "$hours" -gt 0 ]; then
    printf '%dh%dm' "$hours" "$mins"
  else
    printf '%dm' "$mins"
  fi
}

now=$(date +%s)

# Git info — skip optional locks to avoid contention
branch=""
gitstatus=""
if [ -n "$cwd" ]; then
  branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    if git -C "$cwd" --no-optional-locks status --porcelain 2>/dev/null | grep -q .; then
      gitstatus="dirty"
    else
      gitstatus="clean"
    fi
  fi
fi

# ANSI colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
RESET='\033[0m'

out=""

# Model
if [ -n "$model" ]; then
  out="${CYAN}${model}${RESET}"
fi

# Context usage with traffic-light color
if [ -n "$used" ]; then
  pct=$(printf '%.0f' "$used")
  if [ "$pct" -ge 80 ]; then
    color="$RED"
  elif [ "$pct" -ge 50 ]; then
    color="$YELLOW"
  else
    color="$GREEN"
  fi
  [ -n "$out" ] && out="${out} | "
  out="${out}${color}ctx:${pct}%${RESET}"
fi

# Rate-limit windows (only present for Claude.ai subscribers after first API call)
for rl_label in "5h:$five_hr:$five_hr_reset" "7d:$seven_day:$seven_day_reset"; do
  rl_name="${rl_label%%:*}"
  rl_rest="${rl_label#*:}"
  rl_val="${rl_rest%%:*}"
  rl_reset="${rl_rest#*:}"
  if [ -n "$rl_val" ]; then
    rl_pct=$(printf '%.0f' "$rl_val")
    if [ "$rl_pct" -ge 80 ]; then
      rl_color="$RED"
    elif [ "$rl_pct" -ge 50 ]; then
      rl_color="$YELLOW"
    else
      rl_color="$GREEN"
    fi
    rl_remaining=""
    if [ -n "$rl_reset" ] && [ "$rl_reset" != "null" ]; then
      rl_remaining=$(format_countdown "$((rl_reset - now))")
    fi
    [ -n "$out" ] && out="${out} "
    if [ -n "$rl_remaining" ]; then
      out="${out}${rl_color}${rl_name}:${rl_pct}% (${rl_remaining})${RESET}"
    else
      out="${out}${rl_color}${rl_name}:${rl_pct}%${RESET}"
    fi
  fi
done

# Git branch
if [ -n "$branch" ]; then
  [ -n "$out" ] && out="${out} | "
  out="${out}${MAGENTA}${branch}${RESET}"
fi

# Git status
if [ -n "$gitstatus" ]; then
  [ -n "$out" ] && out="${out} "
  if [ "$gitstatus" = "clean" ]; then
    out="${out}${GREEN}(clean)${RESET}"
  else
    out="${out}${RED}(dirty)${RESET}"
  fi
fi

printf "%b\n" "$out"
