#!/bin/bash
# The commands of diff.cast, typed and run one after the other.
#
#   cd <a folder built by scenarios/two_nights.py --record> && diff.sh
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

run 'cat data/cron.log'
run '.venv/bin/ormaos list'
run '.venv/bin/ormaos diff r1 r2'
