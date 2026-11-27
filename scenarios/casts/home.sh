#!/bin/bash
# The commands of home.cast, typed and run one after the other.
#
#   cd <a fresh copy of order-sync, Ormaos installed in .venv, reset.sh run> && home.sh
. .venv/bin/activate
run() {
    printf '\033[1;32m$\033[0m '
    local i
    for ((i = 0; i < ${#1}; i++)); do
        printf '\033[1m%s\033[0m' "${1:i:1}"
        sleep 0.04
    done
    printf '\n'
    sleep 0.4
    eval "$1"
    sleep 2.5
}
sleep 0.6
run 'ormaos run -- python job.py'
run 'ormaos exceptions r1:e1'
sleep 2
