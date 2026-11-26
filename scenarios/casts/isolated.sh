#!/bin/sh
# isolated.sh <folder> <command...>: run a command inside bubblewrap so that
# it sees the system (/usr and /etc, read-only), the claude program
# (read-only) and <folder> (read-write). The home directory and /tmp are
# empty apart from that. With CRED=1 the claude login file is there too,
# read-only. The network is not cut: the agent needs it to reach the model.
folder="$1"
shift
exec bwrap \
    --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib \
    --symlink usr/lib64 /lib64 --symlink usr/sbin /sbin \
    --ro-bind /etc /etc --ro-bind-try /run/systemd/resolve /run/systemd/resolve \
    --proc /proc --dev /dev --tmpfs /tmp --tmpfs /run/user --tmpfs /var \
    --tmpfs "$HOME" \
    --ro-bind "$HOME/.local/share/claude/versions" "$HOME/.local/share/claude/versions" \
    ${CRED:+--ro-bind "$HOME/.claude/.credentials.json" "$HOME/.claude/.credentials.json"} \
    --bind "$folder" "$folder" \
    --chdir "$folder" --unshare-pid --unshare-ipc --unshare-uts --die-with-parent \
    "$@"
