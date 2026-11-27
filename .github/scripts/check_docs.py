"""Check the demo page against the files of the real runs.

    python3 .github/scripts/check_docs.py docs

- the recordings exist, are asciinema v2 recordings, output only, and the
  text under each one is the whole recording;
- every block of commands that names a file of this repository has each of
  its lines in it;
- every row of the results table is a row of the table in the report it
  names, and every number of a paragraph that names a file is in that file;
- every block has a copy button;
- the only thing the page loads from another site is the pinned asciinema
  player, with an integrity hash;
- the public sentence is on the page, and no other em dash is.

Exit code 1 and one line per problem. Standard library only.
"""

import sys as _sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CAPTURES = None
PAGES = [Path(_sys.argv[1]).resolve() / "index.html"]

import html
import json
import re
import sys

PLAYER = "https://cdn.jsdelivr.net/npm/asciinema-player@"
SENTENCE = (
    "Ormaos records and shows what happened inside your Python execution — "
    "the runtime context for your agent and for you."
)
ELIDE = '<span class="elide">...</span>'
TAG = re.compile(r"<[^>]+>")
skipped = set()


def plain(fragment):
    return html.unescape(TAG.sub("", fragment))


def squeeze(text):
    return " ".join(text.split())


def cast_text(path):
    """What a recording printed, as plain text: the output events joined in
    order, colour codes dropped, a carriage return back to the start of the
    line and a backspace one column back, as on a terminal. Lines are not
    wrapped."""
    lines = path.read_text(encoding="utf-8").splitlines()
    raw = "".join(json.loads(line)[2] for line in lines[1:])
    raw = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", raw).replace("\r\n", "\n")
    out = []
    for line in raw.split("\n"):
        cells, at = [], 0
        for char in line:
            if char == "\r":
                at = 0
            elif char == "\b":
                at = max(0, at - 1)
            else:
                if at < len(cells):
                    cells[at] = char
                else:
                    cells.append(char)
                at += 1
        out.append("".join(cells).rstrip())
    return "\n".join(out).strip("\n") + "\n"


def source_path(name, page):
    """Where the file a block names is: a recording next to its page, a
    capture, or a file of this repository or of one checked out next to it."""
    if name.startswith("casts/"):
        return page.parent / name
    if name.startswith("captures/"):
        return CAPTURES / name[len("captures/") :]
    return (ROOT / name).resolve()


def source_text(name, page):
    path = source_path(name, page)
    if not path.is_file():
        skipped.add(name)
        return None
    if path.suffix == ".cast":
        return cast_text(path)
    return path.read_text(encoding="utf-8")


def in_order(wanted, lines):
    """None when `wanted` are lines of `lines`, in that order; else the first that is not."""
    at = 0
    for line in wanted:
        try:
            at = lines.index(line, at) + 1
        except ValueError:
            return line
    return None


def all_run(pages):
    """Every "$ ..." line of the captures and of the recordings of the pages."""
    ran = set()
    files = list(CAPTURES.glob("*.txt")) if CAPTURES else []
    for path in files:
        ran.update(path.read_text(encoding="utf-8").splitlines())
    for page in pages:
        for cast in (page.parent / "casts").glob("*.cast"):
            ran.update(cast_text(cast).splitlines())
    return ran


def check_page(page, ran, problems):
    name = str(page.relative_to(ROOT))
    text = page.read_text(encoding="utf-8")
    say = lambda what: problems.append(f"{name}: {what}")  # noqa: E731
    counts = {"blocks": 0, "rows": 0}

    # Code blocks.
    figures = re.findall(
        r"<figure class=\"code[^\"]*\"([^>]*)>.*?<pre[^>]*><code>(.*?)</code></pre>\s*</figure>",
        text,
        re.S,
    )
    if text.count("<pre") != len(figures):
        say("a <pre> is not inside a code block with a copy button")
    for attrs, body in figures:
        if "data-copy=" not in attrs:
            say("a code block has no data-copy")
        source = re.search(r'data-source="([^"]+)"', attrs)
        doc = re.search(r'data-doc="([^"]+)"', attrs)
        lines = [plain(line) for line in body.replace(ELIDE, "\x00").split("\n")]
        lines = [line for line in lines if line != "\x00"]
        if source:
            real = source_text(source.group(1), page)
            if real is None:
                continue
            counts["blocks"] += 1
            real = [line.rstrip() for line in real.splitlines()]
            if 'data-whole="1"' in attrs:
                if lines != real:
                    say(f"the block is not the whole text of {source.group(1)}")
            else:
                missing = in_order(lines, real)
                if missing is not None:
                    say(f"not a line of {source.group(1)}, or out of order: {missing!r}")
        elif doc:
            real = source_text(doc.group(1), page)
            if real is None:
                continue
            counts["blocks"] += 1
            real = real.replace('\\"', '"')
            for line in lines:
                if line not in real:
                    say(f"not in {doc.group(1)}: {line!r}")

    # Results tables.
    for source, table in re.findall(
        r'<table class="results" data-source="([^"]+)">(.*?)</table>', text, re.S
    ):
        real = source_text(source, page)
        if real is None:
            continue
        rows = [
            [squeeze(cell.replace("`", "")) for cell in line.strip().strip("|").split("|")]
            for line in real.splitlines()
            if line.startswith("|")
        ]
        for tr in re.findall(r"<tr>(.*?)</tr>", table.split("<tbody>")[1], re.S):
            cells = [squeeze(plain(td)) for td in re.findall(r"<td>(.*?)</td>", tr, re.S)]
            counts["rows"] += 1
            if not any(all(cell in row for cell in cells) for row in rows):
                say(f"no row of a table in {source} has all of {cells}")

    # Numbers in a paragraph that names a results file.
    for source, inner in re.findall(
        r'<(?:p|dl)\b[^>]*data-numbers="([^"]+)"[^>]*>(.*?)</(?:p|dl)>', text, re.S
    ):
        real = source_text(source, page)
        if real is None:
            continue
        for number in re.findall(r"\d[\d,./]*\d|\d", plain(inner)):
            if number not in real:
                say(f"the number {number} is not in {source}")

    # The verbs table.
    verbs_table = re.search(r'<table class="verbs">(.*?)</table>', text, re.S)
    if verbs_table:
        listed = re.findall(r"<tr><td><code>(\w+)</code>", verbs_table.group(1))
        help_text = source_text("captures/help.txt", page) or ""
        real = re.findall(r"^    (\w+)  ", help_text, re.M)
        if sorted(listed) != sorted(real):
            say(f"the verbs table has {listed}, `ormaos --help` has {real}")
    for example in re.findall(r'<span class="chip"[^>]*><code>(.*?)</code>', text):
        if "$ " + html.unescape(example) not in ran:
            say(f"the example was not run: {example}")
    if text.count('class="chip"') != text.count('class="chip" data-copy='):
        say("a chip has no data-copy")
    if "data-copy=" in text and ("[data-copy]" not in text or 'id="copy-status"' not in text):
        say("the copy script or its live region is missing")

    # Recordings.
    casts = re.findall(r'data-cast="([^"]+)"', text)
    for cast in casts:
        path = page.parent / cast
        if not path.is_file():
            say(f"{cast}: no such file")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        if header.get("version") != 2 or len(lines) < 2:
            say(f"{cast}: not an asciinema v2 recording")
        if header.get("width") not in (80, 100):
            say(f"{cast}: {header.get('width')} columns wide, not 80 or 100")
        for line in lines[1:]:
            time, kind, _ = json.loads(line)
            if kind != "o" or not isinstance(time, (int, float)):
                say(f"{cast}: an event that is not terminal output")
                break
        if f'data-source="{cast}"' not in text:
            say(f"{cast}: the session is not on the page as text")

    # Other sites.
    loaded = re.findall(r'<(?:script|link|img|iframe)\b[^>]*?(?:src|href)="([^"]+)"', text)
    player_files = 0
    for address in loaded:
        if "://" in address or address.startswith("//"):
            if address.startswith(PLAYER):
                player_files += 1
                if not re.match(re.escape(PLAYER) + r"\d+\.\d+\.\d+/", address):
                    say(f"the player version is not pinned: {address}")
            elif not re.match(r"https://ormaos\.com/", address):
                say(f"loads {address}")
    if text.count("integrity=") != player_files:
        say("a player file has no integrity hash")
    if casts and not player_files:
        say("recordings, but no player")

    # The public sentence, and no other em dash.
    visible = squeeze(plain(re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S)))
    if SENTENCE not in visible:
        say("the public sentence is not on the page")
    if visible.replace(SENTENCE, "").count("—"):
        say("an em dash outside the public sentence")

    print(
        f"{name}: {counts['blocks']} blocks checked against their source, "
        f"{counts['rows']} table rows, {len(casts)} recordings"
    )


def main():
    problems = []
    ran = all_run(PAGES)
    for page in PAGES:
        check_page(page, ran, problems)
    for name in sorted(skipped):
        print(f"not checked, the file is not here: {name}")
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
