#!/bin/bash
# The canary of a batch, run inside the agent's image, on the agents' network,
# with the environment and the home folder of a run.
#
#     harness-canary <url of the model host> <file expected in ~> [<file> ...]
#
# One line per check, "PASS ..." or "FAIL ..."; exit code 1 when any failed.
# The batch does not start unless every line says PASS.
probe=$1
shift
failed=0

blocked() {  # blocked <what> <curl arguments...>: the request must not get an answer
    what=$1
    shift
    said=$(curl -sS -m 15 -o /dev/null -w 'HTTP %{http_code}' "$@" 2>&1)
    code=$?
    if [ "$code" -ne 0 ]; then
        echo "PASS blocked: $what (curl exit $code: $(echo "$said" | head -1))"
    else
        echo "FAIL reached: $what ($said)"
        failed=1
    fi
}

reached() {  # reached <what> <curl arguments...>: any HTTP answer counts
    what=$1
    shift
    said=$(curl -sS -m 30 -o /dev/null -w 'HTTP %{http_code}' "$@" 2>&1)
    code=$?
    if [ "$code" -eq 0 ]; then
        echo "PASS reached: $what ($said)"
    else
        echo "FAIL blocked: $what (curl exit $code: $(echo "$said" | head -1))"
        failed=1
    fi
}

blocked "https://github.com through the proxy" https://github.com
blocked "https://raw.githubusercontent.com through the proxy" https://raw.githubusercontent.com
blocked "http://example.com through the proxy" -f http://example.com
blocked "https://github.com without the proxy" --noproxy '*' https://github.com
blocked "https://1.1.1.1 without the proxy" --noproxy '*' https://1.1.1.1
blocked "$probe without the proxy" --noproxy '*' "$probe"
if getent hosts github.com >/dev/null 2>&1; then
    echo "FAIL resolved: the name github.com, from inside"
    failed=1
else
    echo "PASS blocked: the name github.com does not resolve from inside"
fi
reached "$probe through the proxy" "$probe"

expected=$(printf '%s\n' "$@" | sort)
found=$(cd "$HOME" && find . -mindepth 1 ! -type d | sed 's|^\./||' | sort)
if [ "$found" = "$expected" ]; then
    echo "PASS home: ~ holds only $(echo $found)"
else
    echo "FAIL home: ~ holds $(echo $found), expected only $(echo $expected)"
    failed=1
fi
for file in "$@"; do
    if [ -w "$HOME/$file" ]; then
        echo "FAIL home: ~/$file can be written"
        failed=1
    fi
done
exit $failed
