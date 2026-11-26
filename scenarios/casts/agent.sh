#!/bin/bash
# One agent run on a morning-after folder, shown as it happens.
#
#   agent.sh <folder> without|with <file for the raw stream>
#
# <folder> was built by scenarios/morning_after.py ("with": with --record).
# The agent is `claude -p`, started inside isolated.sh with nothing but the
# prompt. Its raw stream is saved outside the folder, and render.py prints
# each step of it on the terminal.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
folder="$(cd "$1" && pwd)"
side="$2"
stream="$3"

prompt="Last night's order sync run said OK, but this morning some products have wrong stock. Find out why. The job runs with python3."
if [ "$side" = "with" ]; then
    prompt="Last night's order sync run said OK, but this morning some products have wrong stock. Find out why. The job runs with .venv/bin/python. Last night's run was recorded; the ormaos CLI is at .venv/bin/ormaos; run \".venv/bin/ormaos guide\" first."
fi

claude="$(readlink -f "$(command -v claude)")"
printf '\033[1;32m$\033[0m \033[1mcd %s\033[0m\n' "$folder"
printf '\033[1;32m$\033[0m \033[1mclaude -p --model claude-opus-5-5 "%s"\033[0m\n\n' "$prompt"

CRED=1 "$here/isolated.sh" "$folder" "$claude" -p --model claude-opus-5-5 \
    --safe-mode --strict-mcp-config \
    --tools Bash,Read,Grep,Glob --allowedTools Bash,Read,Grep,Glob \
    --no-session-persistence --output-format stream-json --verbose \
    "$prompt" </dev/null 2>&1 | tee "$stream" | python3 "$here/render.py"
sleep 3
