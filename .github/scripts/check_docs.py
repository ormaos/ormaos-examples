"""Check the demo page: its recordings exist and are asciinema recordings,
and the only thing it loads from another site is the pinned asciinema player."""

import json
import re
import sys
from pathlib import Path

PLAYER = "https://cdn.jsdelivr.net/npm/asciinema-player@"


def main():
    docs = Path(sys.argv[1])
    page = (docs / "index.html").read_text(encoding="utf-8")
    problems = []

    casts = re.findall(r'data-cast="([^"]+)"', page)
    if not casts:
        problems.append("the page shows no recording")
    for name in casts:
        path = docs / name
        if not path.is_file():
            problems.append(f"{name}: no such file")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        if header.get("version") != 2 or len(lines) < 2:
            problems.append(f"{name}: not an asciinema v2 recording")
        for line in lines[1:]:
            time, kind, _ = json.loads(line)
            if kind != "o" or not isinstance(time, (int, float)):
                problems.append(f"{name}: an event that is not terminal output")
                break

    loaded = re.findall(
        r'<(?:script|link|img|iframe)\b[^>]*?(?:src|href)="([^"]+)"', page
    )
    for address in loaded:
        if "://" in address or address.startswith("//"):
            if not address.startswith(PLAYER):
                problems.append(f"loads {address}")
            elif not re.match(re.escape(PLAYER) + r"\d+\.\d+\.\d+/", address):
                problems.append(f"the player version is not pinned: {address}")
    if page.count("integrity=") != sum(a.startswith(PLAYER) for a in loaded):
        problems.append("a player file has no integrity hash")

    for problem in problems:
        print(problem)
    print(
        f"docs: {len(casts)} recordings, {len(loaded)} files loaded, {len(problems)} problems"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
