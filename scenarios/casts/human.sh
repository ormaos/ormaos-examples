#!/bin/bash
# The commands of human.cast, typed and run one after the other.
#
#   cd <a fresh copy of order-sync> && human.sh <address of the handler call>
#
# The address is the one `ormaos exceptions r1:e1` prints after "handled at"
# (r1:c130 on Python 3.14; it is not the same on every Python version).
handler="${1:?usage: human.sh <address of the handler call, for example r1:c130>}"

run() {
    printf '\033[1;32m$\033[0m '
    local i
    for ((i = 0; i < ${#1}; i++)); do
        printf '\033[1m%s\033[0m' "${1:i:1}"
        sleep 0.03
    done
    printf '\n'
    sleep 0.4
    eval "$1"
    sleep 2
}

run 'python3 -m venv .venv && . .venv/bin/activate'
run 'pip install git+https://github.com/ormaos/ormaos-python'
run './reset.sh'
run 'ormaos run -- python job.py'
run 'ormaos exceptions r1:e1'
run "ormaos tree $handler --depth 1 --limit 4"
run "ormaos io $handler"
