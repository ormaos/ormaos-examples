#!/usr/bin/env python3
"""Write the benchmark pages, served at ormaos.com/benchmarks/, into docs/benchmarks/.

    python3 site/benchmarks/build.py                       # write docs/benchmarks/
    python3 site/benchmarks/build.py --check               # exit 1 if docs/benchmarks/ is not a fresh build
    python3 site/benchmarks/build.py --overhead ../ormaos-python   # take bench/RESULTS.md again first

Every number on the pages is read from a results file by this script:

- agent-bench/knows2/results/<run>/ and agent-bench/knows/results/<run>/:
  results.jsonl, build.json, report.md, oracle/, streams/ and the
  questions.json each agent got in work/;
- agent-bench/results/<run>/: results.jsonl, build.json, report.md;
- site/benchmarks/overhead/RESULTS.md: a copy of bench/RESULTS.md of
  ormaos-python, with the commit it was taken from in source.json.

The statistics are computed with the functions the runners use (the
bootstrap of agent-bench/knows/run.py, the Wilson interval of
agent-bench/benchlib.py), and every row of a summary table is checked
against the same row of the run's own report.md: the build stops if they
differ. The prompts of knows2 are the text its run.py gives each agent.

The commits named on the pages are those that added each results file, so
the build needs the full git history.

Each page is written as HTML (index.html) and as Markdown at the sibling
path (docs/benchmarks.md, docs/benchmarks/knows2.md, ...), and llms.txt
lists them. The charts are inline SVG, with no script; each is
followed by a table of its numbers. The style is that of docs/index.html.
Standard library only.
"""

import argparse
import difflib
import filecmp
import html
import importlib.util
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BENCH = REPO / "agent-bench"
DOCS = REPO / "docs"
OUT = DOCS / "benchmarks"
OVERHEAD = HERE / "overhead"

# Where each benchmark keeps its results folders: every folder there whose
# results.jsonl is committed is read, oldest first. The first one is the run
# that the benchmark's own page describes; every folder counts on the
# situation pages and the overview.
KNOWS2 = BENCH / "knows2" / "results"
KNOWS = BENCH / "knows" / "results"
FIX = BENCH / "results"

SITE = "https://ormaos.com"
EXAMPLES = "https://github.com/ormaos/ormaos-examples"
ORMAOS = "https://github.com/ormaos/ormaos-python"
SENTENCE = ("Ormaos records and shows what happened inside your Python execution — "
            "the runtime context for your agent and for you.")

ARMS4 = ("none", "raw", "ormaos", "ormaos-values")
SLOT = {"none": 1, "raw": 2, "ormaos": 3, "ormaos-values": 4}

# Each program of knows2: the heading of its section on the knows2 page, its
# kind, its source, what it does (written by hand, without numbers), what the
# knows2 page adds about its execution, and one line for the overview.
KINDS = {
    "web-backend": dict(
        heading="For web backends", kind="web backend", source="use-cases/web-backend",
        does="A FastAPI service over a SQLite database of customers, products and orders, with one route that "
             "lists a customer's orders, each with its total.",
        line="a FastAPI route that lists a customer's orders with their totals"),
    "data-pipeline": dict(
        heading="For data pipelines", kind="data pipeline", source="use-cases/data-pipeline",
        does="A monthly report made with pandas from two exports: it drops the orders without an amount and "
             "repeated order numbers, joins each order to its customer and sums the amounts by region.",
        line="a pandas report that joins two exports and sums them by region"),
    "notebook": dict(
        heading="For notebooks", kind="notebook", source="use-cases/notebook",
        does="A Jupyter notebook that reads the sales of the week, leaves out single sales above a limit, adds "
             "tax and sums the week; its cells ran in the order of their saved execution counts.",
        line="a Jupyter notebook that sums a week of sales, with tax"),
    "ml-training": dict(
        heading="For ML training", kind="ML training", source="use-cases/ml-training",
        does="A PyTorch model trained on CPU that predicts how long a delivery takes, on data made from a seed; "
             "each batch is standardized, and a batch whose loss is not finite is left out.",
        line="a PyTorch training run that leaves out batches whose loss is not finite"),
    "rl-env": dict(
        heading="For RL environments", kind="RL environment", source="use-cases/rl-env",
        does="A grid world in pure Python, where a courier walks from a depot to a customer, and a loop that "
             "runs episodes of it with a seeded policy.",
        line="episodes of a grid world, a courier walking to a customer"),
    "ai-app": dict(
        heading="For AI apps", kind="AI app", source="use-cases/ai-app",
        does="An app that sends each support ticket to a model API, a local stand-in with a small and a large "
             "model, and keeps a one-sentence summary of each ticket.",
        line="support tickets summarized through a model API with a small and a large model"),
    "agent-change": dict(
        heading="For changes made by an agent", kind="change made by an agent", source="use-cases/agent-change",
        does="A small billing tool in a git repository that writes invoices and refunds, run at each of two "
             "commits: before and after a change that a coding agent made.",
        line="a billing tool run before and after a change an agent made"),
    "order-sync": dict(
        heading="For scheduled jobs: order-sync", kind="scheduled job", source="order-sync",
        does="A scheduled job that applies the new orders of a sales system to a warehouse inventory.",
        night="The execution is a night on which it printed its OK line and some orders did not reach the "
              "inventory.",
        line="a night run of a job that applies orders to an inventory"),
    "freight-quote": dict(
        heading="For scheduled jobs: freight-quote", kind="scheduled job", source="freight-quote",
        does="A scheduled job that asks a carrier's rate API for the freight of tomorrow's shipments and writes "
             "one quote per shipment.",
        night="The execution is a night on which some calls were refused.",
        line="a night run of a job that quotes freight from a carrier's API"),
}


def _n(count, one, many=None):
    return f"{count} {one if count == 1 else (many or one + 's')}"


def _ids(values):
    """Names as code spans; a run of names that differ only in a growing
    number is written as its first and last."""
    values = [str(v) for v in values]
    parts = [re.fullmatch(r"(.*?)(\d+)", v) for v in values]
    if len(values) > 3 and all(parts) and len({p.group(1) for p in parts}) == 1:
        numbers = [int(p.group(2)) for p in parts]
        if numbers == list(range(numbers[0], numbers[0] + len(numbers))):
            return f"{code(values[0])} to {code(values[-1])}"
    return joined(code(v) for v in values)


# What happened in each execution of knows2, in two or three sentences that
# describe and do not judge. Every number is the oracle's answer to one of
# the task's questions (o: question id -> answer, from oracle/<task>.json).
HAPPENED = {
    "web-backend": lambda o, says: [
        f"During the one request that `main.py` made, the route answered with the customer {code(o['q1'])} and "
        f"orders whose `total_cents` add up to {o['q4']}; the largest is order {o['q5'][0]}, with {o['q5'][1]}.",
        f"Handling it ran {o['q7']} SQL statements and called `price_of` {o['q6']} times; `discount_for` "
        f"returned {o['q2'][0]}, " + ("from" if o["q2"][1] else "not from") + " its `except KeyError` branch.",
        f"Before the request, `store.create()` inserted {o['q8']} rows into `order_items`."],
    "data-pipeline": lambda o, says: [
        f"`load_orders` read {o['q1']} rows; `drop_unpriced` removed {o['q2']} without an amount, and "
        "`drop_repeats` " + ("ran." if o["q3"] else "did not run."),
        f"Of the {o['q4']} rows passed to `join_customers`, {o['q6']} had a `customer_id` that is not in "
        f"`customers.csv`, and the joined frame had {o['q5']} rows.",
        f"The amounts of `report.csv` add up to {o['q8']}; its first row is {code(o['q7'][0])}, {o['q7'][1]}."],
    "notebook": lambda o, says: [
        f"`load(\"sales.csv\")` returned {o['q1']} rows, and the third cell the kernel ran was {code(o['q2'])}.",
        f"`drop_key_accounts` compared prices that were {o['q3']} and left {o['q4']} rows; {o['q5']} of the rows "
        "it took out had a price within the limit before tax.",
        f"At the end `week` held {o['q6']:.2f}, over rows with {o['q8']} items in all."],
    "ml-training": lambda o, says: [
        f"{_n(o['q1'], 'batch', 'batches')} produced an optimizer update and {o['q2']} were left out because "
        f"their loss was not finite: positions {', '.join(str(i) for i in o['q3'])}.",
        f"In each batch left out, the `{o['q4']}` column had the one value {o['q7']}; {o['q8']} batches had "
        "both values of it."],
    "rl-env": lambda o, says: [
        f"{_n(o['q1'], 'episode')} ended with the courier at the customer, and episode {o['q5']} at the step "
        f"limit; `_arrival_bonus` was called {_n(o['q2'], 'time')}.",
        f"Over {o['q4']} calls of `env.step()`, {o['q3']} moves were blocked by a wall or the edge of the grid, "
        f"and the highest return of an episode was {o['q8']}."],
    "ai-app": lambda o, says: [
        f"{_n(o['q2'], 'ticket')} got a summary from `small-1`, and {_n(len(o['q5']), 'ticket')} "
        f"({joined(str(t) for t in o['q5'])}) from `large-1`.",
        f"The model server answered {o['q3']} of the {o['q4']} POST requests with HTTP 503, and `summaries.json` "
        f"was {o['q8']} bytes."],
    "agent-change": lambda o, says: [
        f"From the run at the first commit (r1) to the run at the second (r2), the `total_cents` of "
        f"`invoices.csv` went from {o['q3']} to {o['q4']} in all, and {_n(o['q5'], 'order')} changed total.",
        f"In r2, `tiers.json` was opened {_n(o['q2'], 'time')}, `discount_percent` returned 10 in "
        f"{_n(o['q6'], 'call')}, and `line_price` dropped cents in an inexact division in {_n(o['q7'], 'call')}."],
    "order-sync": lambda o, says: [
        f"The job parsed {o['q1']} orders from the sales API: {o['q2']} were applied, {o['q3']} had been applied "
        f"by an earlier run, and {o['q4']} were skipped after an exception "
        f"({joined(code(c) for c in sorted(set(o['q6'].values())))}): {_ids(o['q5'])}.",
        f"It took {o['q7']} items out of stock, inserted {_n(o['q8'][0], 'back-order row')} for "
        f"{_n(o['q8'][1], 'item')}, and printed {code(says)}."],
    "freight-quote": lambda o, says: [
        f"The run wrote {o['q1']} quotes: {o['q2']} from the carrier stand-in's answer and {o['q3']} from the "
        f"contract rate card, after the stand-in refused {o['q4']} requests with HTTP 429; the first quote from "
        f"the rate card is {code(o['q5'])}.",
        f"`calls_used_today` went up by {o['q7']}, the quotes add up to {o['q8']} cents, and the job printed "
        f"{code(says)}."],
}


# ---------------------------------------------------------------- helpers


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def runners():
    """knows2/run.py, which brings knows/run.py (`base`), agent-bench/run.py
    (`base.bench_run`), knows/tasks.py (`tasks`) and benchlib.py."""
    sys.path[:0] = [str(BENCH / "knows2")]
    return load(BENCH / "knows2" / "run.py", "knows2_run")


def git(*args):
    done = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=False)
    if done.returncode:
        raise SystemExit(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout.strip()


def added_in(path):
    """The commit that added a file of this repository."""
    if git("rev-parse", "--is-shallow-repository") == "true":
        raise SystemExit("this clone is shallow: the build needs the full history (git fetch --unshallow)")
    full = git("log", "--diff-filter=A", "--format=%H", "-1", "--", str(path.relative_to(REPO)))
    if not full:
        raise SystemExit(f"no commit adds {path.relative_to(REPO)}: the build needs the full history "
                         "(git fetch --unshallow)")
    return full


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def results_folders(results):
    """The results folders under `results` whose results.jsonl is committed,
    oldest first (their names are dates)."""
    listed = git("ls-files", "--", f"{rel(results)}/*/results.jsonl")
    folders = sorted({(REPO / line).parent for line in listed.splitlines()
                      if (REPO / line).parent.parent == results})
    if not folders:
        raise SystemExit(f"no committed results.jsonl under {rel(results)}/")
    return folders


def agent_of(record):
    """The agent of a run: command line, model and effort, e.g.
    "claude-code / claude-opus-5-5". A record that names its agent is taken
    as it is; one written by the claude command line (it has the "claude"
    version) is claude-code."""
    given = record.get("agent")
    if isinstance(given, str) and given:
        return given
    if isinstance(given, dict):
        record = {**record, **given}
    cli = record.get("cli") or ("claude-code" if record.get("claude") else "unknown")
    parts = [cli, record.get("model") or "unknown model"]
    if record.get("effort"):
        parts.append(str(record["effort"]))
    return " / ".join(parts)


def committed_on(commit):
    return git("log", "-1", "--format=%cs", commit)


def rel(path):
    return path.relative_to(REPO).as_posix()


def blob(commit, path):
    return f"{EXAMPLES}/blob/{commit}/{rel(path)}"


def tree(commit, path):
    return f"{EXAMPLES}/tree/{commit}/{rel(path)}"


def esc(text):
    return html.escape(str(text), quote=True)


def dumped(value):
    return json.dumps(value, ensure_ascii=False)


def report_rows(report, first_header):
    """The rows of the table of report.md whose header starts with
    `first_header`, as lists of cells."""
    lines = report.splitlines()
    for at, line in enumerate(lines):
        if line.startswith(f"| {first_header} |"):
            rows = []
            for row in lines[at + 2:]:
                if not row.startswith("|"):
                    break
                rows.append([cell.strip() for cell in row.strip("|").split("|")])
            return rows
    raise SystemExit(f"report.md has no table that starts with {first_header!r}")


def same_as_report(ours, report, first_header, where):
    theirs = report_rows(report, first_header)
    if ours != theirs:
        raise SystemExit(f"{where}: the table differs from report.md\n  built:  {ours}\n  report: {theirs}")


def section_lines(report, title):
    """The bullet lines of a '## title' section of report.md."""
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", report, re.S | re.M)
    if not match:
        raise SystemExit(f"report.md has no section {title!r}")
    return [line[2:] for line in match.group(1).splitlines() if line.startswith("- ")]


def overlapping(intervals):
    """The pairs of names whose intervals overlap."""
    names = list(intervals)
    return [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
            if intervals[a][0] <= intervals[b][1] and intervals[b][0] <= intervals[a][1]]


def overlap_sentence(pairs, arms):
    if not pairs:
        return "No two of the 95% intervals overlap."
    if len(pairs) == len(arms) * (len(arms) - 1) // 2:
        return f"The 95% intervals of all {len(arms)} arms overlap one another."
    return "These 95% intervals overlap: " + "; ".join(f"`{a}` and `{b}`" for a, b in pairs) + "."


def md_url(path):
    """The address of a page's Markdown: /benchmarks.md for /benchmarks/,
    /benchmarks/knows2.md for /benchmarks/knows2/."""
    return "/benchmarks.md" if not path else f"/benchmarks/{path.rstrip('/')}.md"


def date_of(folder):
    name = folder.name
    return f"{name[0:4]}-{name[4:6]}-{name[6:8]}"


def joined(items, last="and"):
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {last} " + items[-1]


# ---------------------------------------------------------------- inline text

# The text of a page is written once, with Markdown's inline marks: `code`,
# [text](url) and **bold**. The HTML is made from it.
INLINE = re.compile(r"(`+)(.+?)\1|\[([^\]]+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*")


def inline(text):
    out, at = [], 0
    for match in INLINE.finditer(text):
        out.append(esc(text[at:match.start()]))
        if match.group(1):
            out.append(f"<code>{esc(match.group(2).strip())}</code>")
        elif match.group(3) is not None:
            out.append(f'<a href="{esc(match.group(4))}">{inline(match.group(3))}</a>')
        else:
            out.append(f"<b>{inline(match.group(5))}</b>")
        at = match.end()
    out.append(esc(text[at:]))
    return "".join(out)


def code(text):
    """A code span of any text, in the inline marks."""
    text = str(text)
    ticks = "`" * (max((len(m) for m in re.findall(r"`+", text)), default=0) + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{ticks}{pad}{text}{pad}{ticks}"


def md_link(url, page_path):
    """A link of the page as it is in Markdown: absolute."""
    return SITE + url if url.startswith("/") else url


def to_markdown_inline(text):
    return INLINE.sub(lambda m: m.group(0) if not m.group(3) else f"[{m.group(3)}]({md_link(m.group(4), '')})",
                      text)


# ---------------------------------------------------------------- blocks
#
# A page is a list of blocks; each is rendered as HTML and as Markdown.


class Block:
    def html(self):
        raise NotImplementedError

    def md(self):
        raise NotImplementedError


class P(Block):
    def __init__(self, text, cls=None):
        self.text, self.cls = text, cls

    def html(self):
        cls = f' class="{self.cls}"' if self.cls else ""
        return f"<p{cls}>{inline(self.text)}</p>"

    def md(self):
        text = to_markdown_inline(self.text)
        return f"*{text}*" if self.cls in ("caption", "kicker") else text


class H(Block):
    def __init__(self, level, text, anchor=None):
        self.level, self.text, self.anchor = level, text, anchor

    def html(self):
        anchor = f' id="{self.anchor}"' if self.anchor else ""
        return f"<h{self.level}{anchor}>{inline(self.text)}</h{self.level}>"

    def md(self):
        return "#" * self.level + " " + to_markdown_inline(self.text)


class UL(Block):
    def __init__(self, items, cls="rows"):
        self.items, self.cls = items, cls

    def html(self):
        items = "\n".join(f"  <li>{inline(item)}</li>" for item in self.items)
        return f'<ul class="{self.cls}">\n{items}\n</ul>'

    def md(self):
        return "\n".join(f"- {to_markdown_inline(item)}" for item in self.items)


class Table(Block):
    """`rows` are lists of cells in the inline marks. `numbers`: the columns
    after the first are numbers, aligned right."""

    def __init__(self, headers, rows, numbers=True, cls=None, caption=None):
        self.headers, self.rows, self.numbers, self.caption = headers, rows, numbers, caption
        self.cls = cls or ("results" if numbers else "plain")

    def html(self):
        head = "".join(f'<th scope="col">{inline(h)}</th>' for h in self.headers)
        body = "\n".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in self.rows)
        caption = f"<caption class=\"visually-hidden\">{inline(self.caption)}</caption>" if self.caption else ""
        return (f'<div class="table-wrap">\n<table class="{self.cls}">{caption}\n<thead><tr>{head}</tr></thead>\n'
                f"<tbody>\n{body}\n</tbody>\n</table>\n</div>")

    def md(self):
        def cell(text):
            return to_markdown_inline(text).replace("|", "\\|").replace("\n", " ")
        lines = ["| " + " | ".join(cell(h) for h in self.headers) + " |",
                 "|" + "|".join("---" if i == 0 or not self.numbers else "---:" for i in range(len(self.headers)))
                 + "|"]
        lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in self.rows]
        return "\n".join(lines)


class Pre(Block):
    """Text quoted as it is, in a panel with a label."""

    def __init__(self, label, text):
        self.label, self.text = label, text

    def html(self):
        bar = (f'<figcaption class="code-bar"><span class="code-label">{inline(self.label)}</span></figcaption>\n'
               if self.label else "")
        return (f'<figure class="code wrap verbatim">\n{bar}<pre tabindex="0"><code>{esc(self.text)}</code></pre>'
                "\n</figure>")

    def md(self):
        return (f"{to_markdown_inline(self.label)}:\n\n" if self.label else "") + fenced(self.text)


def fenced(text):
    """A Markdown code block that holds any text."""
    fence = "`" * max(3, max((len(m) for m in re.findall(r"`+", text)), default=0) + 1)
    return f"{fence}text\n{text}\n{fence}"


class Commands(Block):
    def __init__(self, lines):
        self.lines = lines

    def html(self):
        lines = "\n".join(f'<span class="cmd">{esc(line)}</span>' for line in self.lines)
        return ('<figure class="code sh">\n<figcaption class="code-bar"><span class="code-label">Shell</span>'
                f'</figcaption>\n<pre tabindex="0"><code>{lines}</code></pre>\n</figure>')

    def md(self):
        return "```bash\n" + "\n".join(self.lines) + "\n```"


class Facts(Block):
    """Big values over small labels: (value, label)."""

    def __init__(self, items, cls=""):
        self.items, self.cls = items, cls

    def html(self):
        items = "\n".join(f"  <div><dt>{inline(label)}</dt><dd>{inline(value)}</dd></div>"
                          for value, label in self.items)
        return f'<dl class="facts bench {self.cls}">\n{items}\n</dl>'.replace(" \">", "\">")

    def md(self):
        return "\n".join(f"- **{to_markdown_inline(value)}**: {to_markdown_inline(label)}"
                         for value, label in self.items)


class Cards(Block):
    """(kicker, title, blocks, link text, url)."""

    def __init__(self, cards, grid=False):
        self.cards, self.grid = cards, grid

    def html(self):
        out = ['<ul class="cards grid">' if self.grid else '<ul class="cards">']
        for kicker, title, blocks, more, url in self.cards:
            inner = "\n".join(b.html() for b in blocks)
            out.append(f'<li class="card">\n<p class="kicker">{inline(kicker)}</p>\n<h3>{inline(title)}</h3>\n'
                       f'{inner}\n<p class="more"><a href="{esc(url)}">{inline(more)}</a></p>\n</li>')
        out.append("</ul>")
        return "\n".join(out)

    def md(self):
        out = []
        for kicker, title, blocks, more, url in self.cards:
            out.append(f"### {to_markdown_inline(title)}\n\n*{to_markdown_inline(kicker)}*\n\n"
                       + "\n\n".join(b.md() for b in blocks) + f"\n\n[{more}]({md_link(url, '')})")
        return "\n\n".join(out)


class Pair(Block):
    """Two blocks side by side on a wide screen, one under the other on a
    narrow one."""

    def __init__(self, blocks):
        self.blocks = blocks

    def html(self):
        return '<div class="pair">\n' + "\n".join(f"<div>\n{b.html()}\n</div>" for b in self.blocks) + "\n</div>"

    def md(self):
        return "\n\n".join(b.md() for b in self.blocks)


class Toc(Block):
    def __init__(self, items):
        self.items = items

    def html(self):
        items = "\n".join(f'  <li><a href="#{a}">{inline(t)}</a></li>' for a, t in self.items)
        return f'<nav class="toc" aria-label="On this page">\n<h2>On this page</h2>\n<ol>\n{items}\n</ol>\n</nav>'

    def md(self):
        return ""


class Chart(Block):
    """An inline SVG chart, then the table of its numbers. `svg` is the SVG,
    or a function (id suffix, width) that draws it: drawn at `width`, or,
    without one, twice: WIDE for a wide screen and W for a narrow one, of
    which the style shows one."""

    def __init__(self, svg, title, desc, table, width=None):
        self.svg, self.title, self.desc, self.table, self.width = svg, title, desc, table, width

    def html(self):
        if isinstance(self.svg, str):
            body = self.svg
        elif self.width:
            body = self.svg("", self.width)
        else:
            body = (f'<div class="wide-only">\n{self.svg("", WIDE)}\n</div>\n'
                    f'<div class="narrow-only">\n{self.svg("-n", W)}\n</div>')
        return f'<figure class="chart">\n{body}\n</figure>\n{self.table.html()}'

    def md(self):
        return f"**{self.title}.** {self.desc}\n\n{self.table.md()}"


class Details(Block):
    def __init__(self, summary, blocks):
        self.summary, self.blocks = summary, blocks

    def html(self):
        inner = "\n".join(b.html() for b in self.blocks)
        return f'<details class="text">\n<summary>{inline(self.summary)}</summary>\n{inner}\n</details>'

    def md(self):
        return f"**{to_markdown_inline(self.summary)}**\n\n" + "\n\n".join(b.md() for b in self.blocks)


class Section:
    def __init__(self, anchor, title, blocks, kicker=None, first=False, level=2):
        self.anchor, self.title, self.blocks = anchor, title, blocks
        self.kicker, self.first, self.level = kicker, first, level


# ---------------------------------------------------------------- charts

W = 600       # a chart in the text column, and every chart on a narrow screen
WIDE = 1060   # a chart across the wide column of a wide screen
FONT = 13


def nice_ticks(high, count=4):
    raw = high / count
    step = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        if raw <= factor * step:
            step *= factor
            break
    top = step * math.ceil(high / step)
    ticks, value = [], 0.0
    while value <= top + step / 1000:
        ticks.append(value)
        value += step
    return ticks


def svg_open(cid, title, desc, height, width=W):
    return [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{cid}-t {cid}-d" '
            f'xmlns="http://www.w3.org/2000/svg">',
            f'<title id="{cid}-t">{esc(title)}</title>', f'<desc id="{cid}-d">{esc(desc)}</desc>']


def fmt(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def interval_chart(cid, title, desc, rows, ticks, tick_label, left=130, right=190, width=W):
    """rows: (label, slot, value, low, high, text, tooltip); the x axis runs
    from ticks[0] to ticks[-1]."""
    lo, hi = ticks[0], ticks[-1]
    plot = width - left - right
    row_h, top = 40, 12
    height = top + row_h * len(rows) + 34

    def x(v):
        return left + plot * (v - lo) / (hi - lo)

    out = svg_open(cid, title, desc, height, width)
    bottom = top + row_h * len(rows)
    for t in ticks:
        out.append(f'<line class="grid" x1="{fmt(x(t))}" y1="{top}" x2="{fmt(x(t))}" y2="{bottom}"/>')
        out.append(f'<text x="{fmt(x(t))}" y="{bottom + 20}" text-anchor="middle">{esc(tick_label(t))}</text>')
    for i, (label, slot, value, low, high, text, tip) in enumerate(rows):
        y = top + row_h * i + row_h / 2
        out.append(f"<g><title>{esc(tip)}</title>")
        out.append(f'<text class="label" x="{left - 14}" y="{fmt(y + 4.5)}" text-anchor="end">{esc(label)}</text>')
        out.append(f'<line class="s{slot} whisker" x1="{fmt(x(low))}" y1="{fmt(y)}" x2="{fmt(x(high))}" '
                   f'y2="{fmt(y)}"/>')
        for end in (low, high):
            out.append(f'<line class="s{slot} whisker" x1="{fmt(x(end))}" y1="{fmt(y - 6)}" x2="{fmt(x(end))}" '
                       f'y2="{fmt(y + 6)}"/>')
        out.append(f'<circle class="s{slot} dot" cx="{fmt(x(value))}" cy="{fmt(y)}" r="6"/>')
        out.append(f'<text class="value" x="{width - right + 14}" y="{fmt(y + 4.5)}">{esc(text)}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


def stacked_chart(cid, title, desc, rows, parts, left=130, right=150, width=W):
    """rows: (label, [count per part]); parts: (name, class)."""
    plot = width - left - right
    row_h, top = 40, 40
    height = top + row_h * len(rows) + 8
    total = max(sum(counts) for _, counts in rows)
    out = svg_open(cid, title, desc, height, width)
    lx = left
    for name, cls in parts:
        out.append(f'<rect class="{cls}" x="{lx}" y="10" width="12" height="12" rx="2"/>')
        out.append(f'<text x="{lx + 18}" y="20.5">{esc(name)}</text>')
        lx += 18 + 8 * len(name) + 28
    for i, (label, counts) in enumerate(rows):
        y = top + row_h * i + (row_h - 20) / 2
        out.append(f'<text class="label" x="{left - 14}" y="{fmt(y + 14.5)}" text-anchor="end">{esc(label)}</text>')
        at = left
        for (name, cls), count in zip(parts, counts):
            width = plot * count / total
            if count:
                shown = max(width - 2, 1.5)
                out.append(f'<rect class="{cls}" x="{fmt(at)}" y="{fmt(y)}" width="{fmt(shown)}" height="20" rx="2">'
                           f"<title>{esc(label)}: {count} {esc(name)} of {sum(counts)}</title></rect>")
            at += width
        text = " / ".join(str(c) for c in counts)
        out.append(f'<text class="value" x="{fmt(left + plot + 12)}" y="{fmt(y + 14.5)}">{esc(text)}</text>')
    out.append("</svg>")
    return "\n".join(out)


RAMP = ["#e6effb", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95"]


def heatmap(cid, title, desc, row_labels, col_labels, cells, left=110, cell_w=88, cell_h=30):
    """cells[r][c]: (share from 0 to 1, text, tooltip)."""
    top = 34
    width_needed = left + cell_w * len(col_labels)
    height = top + cell_h * len(row_labels) + 6
    out = [f'<svg viewBox="0 0 {width_needed} {height}" role="img" aria-labelledby="{cid}-t {cid}-d" '
           f'xmlns="http://www.w3.org/2000/svg" class="fit" style="max-width:{width_needed}px">',
           f'<title id="{cid}-t">{esc(title)}</title>', f'<desc id="{cid}-d">{esc(desc)}</desc>']
    for c, name in enumerate(col_labels):
        out.append(f'<text class="label" x="{left + cell_w * c + cell_w / 2}" y="22" text-anchor="middle">'
                   f"{esc(name)}</text>")
    for r, name in enumerate(row_labels):
        y = top + cell_h * r
        out.append(f'<text class="label" x="{left - 12}" y="{y + cell_h / 2 + 4.5}" text-anchor="end">'
                   f"{esc(name)}</text>")
        for c, (share, text, tip) in enumerate(cells[r]):
            step = round(share * (len(RAMP) - 1))
            ink = "#ffffff" if step >= 7 else "#0b0b0b"
            x = left + cell_w * c
            out.append(f'<g><title>{esc(tip)}</title><rect x="{x + 1}" y="{y + 1}" width="{cell_w - 2}" '
                       f'height="{cell_h - 2}" rx="2" fill="{RAMP[step]}"/>'
                       f'<text x="{x + cell_w / 2}" y="{y + cell_h / 2 + 4.5}" text-anchor="middle" '
                       f'style="fill:{ink}">{esc(text)}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


def bar_chart(cid, title, desc, rows, value_text, left=130, right=120, width=W):
    """rows: (label, slot, value, tooltip)."""
    plot = width - left - right
    row_h, top = 34, 12
    ticks = nice_ticks(max(v for _, _, v, _ in rows))
    hi = ticks[-1]
    bottom = top + row_h * len(rows)
    height = bottom + 34
    out = svg_open(cid, title, desc, height, width)
    for t in ticks:
        x = left + plot * t / hi
        out.append(f'<line class="grid" x1="{fmt(x)}" y1="{top}" x2="{fmt(x)}" y2="{bottom}"/>')
        out.append(f'<text x="{fmt(x)}" y="{bottom + 20}" text-anchor="middle">{esc(value_text(t, True))}</text>')
    for i, (label, slot, value, tip) in enumerate(rows):
        y = top + row_h * i + (row_h - 18) / 2
        width = plot * value / hi
        out.append(f"<g><title>{esc(tip)}</title>")
        out.append(f'<text class="label" x="{left - 14}" y="{fmt(y + 13.5)}" text-anchor="end">{esc(label)}</text>')
        out.append(f'<rect class="s{slot}" x="{left}" y="{fmt(y)}" width="{fmt(width)}" height="18" rx="2"/>')
        out.append(f'<text class="value" x="{fmt(left + width + 10)}" y="{fmt(y + 13.5)}">'
                   f"{esc(value_text(value, False))}</text></g>")
    out.append("</svg>")
    return "\n".join(out)


def log_dots(cid, title, desc, rows, series, ticks, tick_label, left=130, right=30, width=W):
    """rows: (label, {key: value}); series: (key, name, slot); ticks on a log
    scale from ticks[0] to ticks[-1]."""
    plot = width - left - right
    row_h, top = 34, 40
    lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])
    bottom = top + row_h * len(rows)
    height = bottom + 34

    def x(v):
        return left + plot * (math.log10(v) - lo) / (hi - lo)

    out = svg_open(cid, title, desc, height, width)
    lx = left
    for key, name, slot in series:
        out.append(f'<circle class="s{slot} dot" cx="{lx + 6}" cy="16" r="6"/>')
        out.append(f'<text x="{lx + 18}" y="20.5">{esc(name)}</text>')
        lx += 18 + 8 * len(name) + 28
    for t in ticks:
        out.append(f'<line class="grid" x1="{fmt(x(t))}" y1="{top}" x2="{fmt(x(t))}" y2="{bottom}"/>')
        out.append(f'<text x="{fmt(x(t))}" y="{bottom + 20}" text-anchor="middle">{esc(tick_label(t))}</text>')
    offsets = {1: [0], 2: [-5, 5], 3: [-8, 0, 8]}[len(series)]
    for i, (label, values) in enumerate(rows):
        y = top + row_h * i + row_h / 2
        out.append(f'<text class="label" x="{left - 14}" y="{fmt(y + 4.5)}" text-anchor="end">{esc(label)}</text>')
        for (key, name, slot), dy in zip(series, offsets):
            if values.get(key) is None:
                continue
            out.append(f'<circle class="s{slot} dot" cx="{fmt(x(values[key]))}" cy="{fmt(y + dy)}" r="5">'
                       f"<title>{esc(label)}, {esc(name)}: {esc(values[key + ':text'])}</title></circle>")
    out.append("</svg>")
    return "\n".join(out)


def size_text(n):
    for unit, size in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if n >= size:
            return f"{n / size:.1f} {unit}" if n / size < 100 else f"{n / size:.0f} {unit}"
    return f"{n} B"


# ---------------------------------------------------------------- page frame


class Frame:
    """What every page takes from docs/index.html: the style, the header,
    the theme scripts and the footer."""

    def __init__(self):
        text = (DOCS / "index.html").read_text(encoding="utf-8")
        self.style = re.search(r"<style>\n(.*?)</style>", text, re.S).group(1)
        self.head_script = re.search(r"(<script>\n  \(function \(\) \{\n    // Light is the default.*?</script>)",
                                     text, re.S).group(1)
        header = re.search(r'(<header class="site-header">.*?</header>)', text, re.S).group(1)
        self.header_script = re.search(r"</header>\n(<script>.*?</script>)", text, re.S).group(1)
        self.footer = re.search(r"(<footer>.*?</footer>)", text, re.S).group(1)
        demo = '<a href="./" aria-current="page">Demo</a>'
        bench = '<a href="/benchmarks/">Benchmarks</a>'
        if demo not in header or bench not in header:
            raise SystemExit("docs/index.html: the header has no Demo link marked as the current page, or no "
                             "Benchmarks link")
        self.header = (header.replace(demo, f'<a href="{SITE}/demo/">Demo</a>')
                       .replace(bench, '<a href="/benchmarks/"{current}>Benchmarks</a>'))

    def page(self, path, title, description, sections, current=False):
        out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{esc(title)}</title>", f'<meta name="description" content="{esc(description)}">',
               '<meta name="color-scheme" content="light">', '<meta name="theme-color" content="#ffffff">',
               '<link rel="icon" href="/benchmarks/favicon.svg" type="image/svg+xml">',
               f'<link rel="alternate" type="text/markdown" href="{md_url(path)}">', "", self.head_script, "",
               '<link rel="stylesheet" href="/benchmarks/style.css">', "</head>", '<body class="long bench">', "",
               self.header.replace("{current}", ' aria-current="page"' if current else ""), self.header_script,
               "", "<main>", ""]
        for s in sections:
            band = "band first" if s.first else "band"
            out.append(f'<section class="{band}" id="{s.anchor}" aria-labelledby="{s.anchor}-title">')
            if s.kicker:
                out.append(f'<p class="kicker">{inline(s.kicker)}</p>')
            tag = "h1" if s.first else f"h{s.level}"
            out.append(f'<{tag} id="{s.anchor}-title">{inline(s.title)}</{tag}>')
            out += [b.html() for b in s.blocks]
            out += ["</section>", ""]
        out += ["</main>", "", self.footer, "", "</body>", "</html>", ""]
        return "\n".join(out)

    @staticmethod
    def markdown(sections):
        out = []
        for s in sections:
            out.append(("# " if s.first else "#" * s.level + " ") + to_markdown_inline(s.title))
            if s.kicker:
                out.append(f"*{to_markdown_inline(s.kicker)}*")
            out += [b.md() for b in s.blocks if b.md()]
        return "\n\n".join(out) + "\n"


EXTRA_CSS = """
/* The benchmark pages: what docs/index.html does not have. Written by
   site/benchmarks/build.py. */
:root {
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --series-3: #1baf7a;
  --series-4: #eda100;
  --neutral: #a8a7a1;
}

:root[data-theme="dark"] {
  --series-1: #3987e5;
  --series-2: #d95926;
  --series-3: #199e70;
  --series-4: #c98500;
  --neutral: #6b6a66;
}

.chart {
  margin: 28px auto 4px;
  overflow-x: auto;
}

.chart svg {
  display: block;
  width: 100%;
  min-width: 30rem;
  height: auto;
}

.chart text {
  fill: var(--text-dim);
  font-family: inherit;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.chart text.label,
.chart text.value {
  fill: var(--text);
}

.chart .grid {
  stroke: var(--line);
  stroke-width: 1;
}

.chart .whisker {
  fill: none;
  stroke-width: 2;
}

.chart .dot {
  stroke: var(--bg);
  stroke-width: 2;
}

.chart rect.s1, .chart circle.s1 { fill: var(--series-1); }
.chart rect.s2, .chart circle.s2 { fill: var(--series-2); }
.chart rect.s3, .chart circle.s3 { fill: var(--series-3); }
.chart rect.s4, .chart circle.s4 { fill: var(--series-4); }
.chart line.s1 { stroke: var(--series-1); }
.chart line.s2 { stroke: var(--series-2); }
.chart line.s3 { stroke: var(--series-3); }
.chart line.s4 { stroke: var(--series-4); }
.chart rect.neutral { fill: var(--neutral); }

table.plain td,
table.answers td {
  overflow-wrap: anywhere;
}

table.answers {
  table-layout: fixed;
}

table.answers th:first-child,
table.answers td:first-child {
  width: 8.5rem;
}

table.answers td code {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.verbatim pre {
  max-height: 36rem;
  overflow-y: auto;
  font-size: 13px;
}

main .band > .facts.bench {
  gap: 16px 40px;
  margin: 24px auto 8px;
}

main .band > details.text {
  margin: 20px auto 0;
}

main .band > p.sentence {
  margin-top: 16px;
}

/* From 64rem the benchmark pages use a wider column, 1100 px: charts,
   tables and cards take all of it, text stays near 70 characters a line.
   Each wide chart is drawn twice; the style shows the one that fits. */
.narrow-only { display: none; }

@media (max-width: 63.99rem) {
  .wide-only { display: none; }
  .narrow-only { display: block; }
}

@media (min-width: 64rem) {
  .bench main .band {
    max-width: 68.75rem;
    margin-inline: auto;
  }

  .bench main .band > * {
    max-width: none;
    margin-inline: 0;
  }

  .bench main .band > :is(p, h1, h2, h3, ul.rows, nav.toc, details, figure.code) {
    max-width: 70ch;
    margin-inline: 0;
  }

  .bench .chart svg {
    min-width: 0;
  }
}

.bench main .band > p.headline {
  margin-top: 32px;
  font-size: 20px;
  line-height: 1.5;
  letter-spacing: -0.01em;
}

.pair {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px 48px;
}

@media (min-width: 64rem) {
  .pair { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

.pair .table-wrap,
.card .table-wrap {
  margin-top: 12px;
}

main .band > .facts.three {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 24px 40px;
  margin-top: 40px;
}

@media (min-width: 48rem) {
  main .band > .facts.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

.facts.three dt a {
  text-decoration: underline;
}

.cards.grid {
  border-top: 0;
}

.cards.grid .card {
  border-top: 1px solid var(--line);
  border-bottom: 0;
  padding-bottom: 24px;
}

@media (min-width: 64rem) {
  .cards.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 48px;
  }
}

.card .chart {
  margin-top: 12px;
}

/* A grid of cells fits the column; the other charts keep a readable font
   and scroll sideways on a narrow screen. */
.chart svg.fit {
  min-width: 0;
}

@media (max-width: 30rem) {
  table.answers th:first-child,
  table.answers td:first-child { width: 7rem; }
  table.answers th,
  table.answers td { padding-right: 10px; }
}

.facts.bench dd {
  font-size: 22px;
}

.question {
  margin-top: 40px;
}

.question + p {
  color: var(--text-soft);
}

/* A situation's page: one column per arm, side by side from 64rem, wider
   than the text column; one under the other below it. */
.sbs {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 28px;
  margin: 24px 0 8px;
}

@media (min-width: 64rem) {
  .bench main .band > .sbs {
    grid-template-columns: repeat(var(--cols), minmax(0, 1fr));
    gap: 20px;
    width: min(calc(100vw - 48px), 100rem);
    max-width: none;
    margin-inline: calc(50% - min(50vw - 24px, 50rem));
  }
}

.arm-col {
  min-width: 0;
  border-top: 3px solid var(--line);
  padding-top: 10px;
}

.arm-col.a1 { border-top-color: var(--series-1); }
.arm-col.a2 { border-top-color: var(--series-2); }
.arm-col.a3 { border-top-color: var(--series-3); }
.arm-col.a4 { border-top-color: var(--series-4); }

.arm-col h4 {
  margin: 0 0 6px;
  font-size: 16px;
}

.arm-col p {
  margin: 2px 0;
  font-size: 13.5px;
  line-height: 1.45;
}

.arm-col p.meta {
  color: var(--text-soft);
}

.arm-col p.part {
  margin: 18px 0 6px;
  font-weight: 600;
  color: var(--text);
}

.arm-col ol.steps {
  margin: 0;
  padding-left: 1.6em;
}

.arm-col ol.steps li {
  margin: 0 0 10px;
  font-size: 12px;
}

.arm-col pre {
  margin: 0;
  padding: 6px 8px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 12px;
  line-height: 1.45;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel);
  max-height: 22rem;
  overflow-y: auto;
}

.arm-col pre.out {
  margin-top: 4px;
  border-style: dashed;
  color: var(--text-soft);
}

.arm-col p.note {
  font-size: 12px;
  color: var(--text-dim);
}

.arm-col figure.code {
  margin: 0;
  max-width: none;
}

.arm-col figure.code pre {
  max-height: 26rem;
}

.arm-col .table-wrap {
  margin: 0;
}

.arm-col table.mini {
  font-size: 13px;
}

.arm-col table.mini th,
.arm-col table.mini td {
  padding: 3px 10px 3px 0;
}

.arm-col table.mini td code {
  white-space: normal;
  overflow-wrap: anywhere;
}

table.questions td:nth-child(2) {
  min-width: 18rem;
}

table.runs td {
  white-space: nowrap;
}

/* The overview's situations: a name and a line, small bars per arm. */
p.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  font-size: 13px;
}

p.legend .key {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

i.sw {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

i.sw.s1 { background: var(--series-1); }
i.sw.s2 { background: var(--series-2); }
i.sw.s3 { background: var(--series-3); }
i.sw.s4 { background: var(--series-4); }

table.situations td {
  vertical-align: top;
}

table.situations td:first-child {
  min-width: 14rem;
}

table.situations .bench {
  margin-left: 6px;
  font-size: 12px;
  color: var(--text-dim);
}

table.situations .line {
  font-size: 13px;
  color: var(--text-soft);
}

table.situations td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

@media (max-width: 40rem) {
  table.situations thead { display: none; }

  table.situations,
  table.situations tbody {
    display: block;
    width: 100%;
  }

  table.situations tr {
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: end;
    column-gap: 16px;
    border-bottom: 1px solid var(--line);
    padding: 12px 0;
  }

  table.situations td {
    border: 0;
    padding: 0;
  }

  table.situations td:first-child {
    grid-column: 1 / -1;
    min-width: 0;
    padding-bottom: 8px;
  }

  table.situations td.num::before {
    display: block;
    content: "ormaos − none";
    color: var(--text-dim);
    font-size: 12px;
  }
}

svg.mini {
  display: block;
  overflow: visible;
}

svg.mini text {
  font-size: 12px;
  fill: var(--text);
  font-variant-numeric: tabular-nums;
}

svg.mini rect.track { fill: var(--line); }
svg.mini rect.s1 { fill: var(--series-1); }
svg.mini rect.s2 { fill: var(--series-2); }
svg.mini rect.s3 { fill: var(--series-3); }
svg.mini rect.s4 { fill: var(--series-4); }
"""


# ---------------------------------------------------------------- the knows runs


class KnowsRun:
    """One results folder of knows or knows2."""

    def __init__(self, folder, arms, h):
        self.folder, self.h = folder, h
        self.records = jsonl(folder / "results.jsonl")
        for r in self.records:
            r["_agent"], r["_run"] = agent_of(r), self
        self.agents = sorted({r["_agent"] for r in self.records})
        self.built = json.loads((folder / "build.json").read_text(encoding="utf-8"))
        self.report = (folder / "report.md").read_text(encoding="utf-8")
        self.arms = [a for a in arms if any(r["arm"] == a for r in self.records)]
        self.names = [n for n in h.tasks.NAMES if any(r["task"] == n for r in self.records)]
        self.runs = sorted({r["run"] for r in self.records})
        self.commit = added_in(folder / "results.jsonl")
        self.models = sorted({r["model"] for r in self.records})
        self.claude = sorted({r["claude"] for r in self.records})
        self.date = date_of(folder)

    def of(self, arm=None, name=None, run=None):
        return [r for r in self.records if arm in (None, r["arm"]) and name in (None, r["task"])
                and run in (None, r["run"])]

    def scores(self, arm, name=None):
        return [r["score"] for r in self.of(arm, name)]

    def mean(self, arm, name=None):
        return statistics.fmean(self.scores(arm, name))

    def interval(self, arm):
        return self.h.base.bootstrap(self.scores(arm))

    def median(self, arm, key):
        bench_run = self.h.base.bench_run
        values = [bench_run.tokens_of(r) if key == "tokens" else r[key] for r in self.of(arm)]
        return bench_run.median(values)

    def summary_rows(self):
        """The first table of the report, made again from results.jsonl."""
        number = self.h.base.number
        rows = []
        for arm in self.arms:
            low, high = self.interval(arm)
            records = self.of(arm)
            rows.append([arm, str(len(records)), f"{self.mean(arm):.2f}", f"{low:.2f} to {high:.2f}",
                         number(self.median(arm, "wall_seconds"), "{:.0f} s"),
                         number(self.median(arm, "tool_calls")), number(self.median(arm, "tokens")),
                         f"{sum(1 for r in records if r['ran_again'])}/{len(records)}",
                         str(sum(1 for r in records if r["timed_out"]))])
        same_as_report(rows, self.report, "Arm", rel(self.folder))
        return rows

    def task_rows(self):
        rows = []
        for name in self.names:
            kept = len(self.of(name=name)[0]["right"])
            rows.append([name, str(kept)] + [f"{self.mean(arm, name):.2f}" for arm in self.arms])
        same_as_report(rows, self.report, "Task | Questions", rel(self.folder) + " per task")
        return rows

    def questions(self, name):
        first = self.of(name=name)[0]
        given = json.loads((self.folder / first["folder"] / "questions.json").read_text(encoding="utf-8"))
        given = given["questions"] if isinstance(given, dict) else given
        kept = first["right"]
        return [q for q in given if q["id"] in kept]

    def oracle(self, name):
        return json.loads((self.folder / "oracle" / f"{name}.json").read_text(encoding="utf-8"))

    @staticmethod
    def outcome(record, qid):
        given = record["answers"].get(qid) if isinstance(record["answers"], dict) else None
        return ("right" if record["right"][qid] else "null" if given is None else "wrong"), given

    def outcome_counts(self, arm):
        count = {"right": 0, "null": 0, "wrong": 0}
        for r in self.of(arm):
            for qid in r["right"]:
                count[self.outcome(r, qid)[0]] += 1
        return count

    def right_runs(self, name, qid, arm):
        return sum(1 for r in self.of(arm, name) if r["right"][qid])

    def full_marks(self):
        return [n for n in self.names if all(self.mean(a, n) == 1.0 for a in self.arms)]

    def last_text(self, record):
        """What the agent said last: its last text block in the stream."""
        last = None
        for line in (self.folder / record["stream"]).read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("type") == "assistant":
                for part in event["message"].get("content", []):
                    if part.get("type") == "text" and part["text"].strip():
                        last = part["text"]
        return last


def score_chart(cid, run, name, width=None, compact=False, left=130, right=190):
    rows = []
    for arm in run.arms:
        low, high = run.interval(arm)
        mean = run.mean(arm)
        rows.append((arm, SLOT[arm], mean, low, high, f"{mean:.2f} ({low:.2f} to {high:.2f})",
                     f"{arm}: mean score {mean:.2f}, 95% interval {low:.2f} to {high:.2f}, "
                     f"{len(run.of(arm))} runs"))
    title = f"Mean score per arm, {name}"
    desc = ("The mean score of the runs of each arm, with its 95% bootstrap interval. "
            + "; ".join(f"{r[0]} {r[5]}" for r in rows) + ".")
    def svg(suffix, w):
        return interval_chart(cid + suffix, title, desc, rows, [0, 0.25, 0.5, 0.75, 1.0], lambda t: f"{t:.2f}",
                              left=left, right=right, width=w)
    summary = run.summary_rows()
    if compact:
        table = Table(["Arm", "Runs", "Mean score", "95% interval"], [[code(r[0])] + r[1:4] for r in summary])
    else:
        table = Table(["Arm", "Runs", "Mean score", "95% interval", "Median wall time", "Median tool calls",
                       "Median tokens", "Ran the program again", "Timed out"], [[code(r[0])] + r[1:] for r in summary])
    return Chart(svg, title, desc, table, width)


def rnw_chart(cid, run, width=None, left=130, right=150):
    """Right, null and wrong answers per arm, stacked."""
    counts = {arm: run.outcome_counts(arm) for arm in run.arms}
    same_as_report([[a, str(sum(c.values())), str(c["right"]), str(c["null"]), str(c["wrong"])]
                    for a, c in counts.items()], run.report, "Arm | Answers", rel(run.folder) + " outcomes")
    title = "Right, null and wrong answers per arm"
    desc = ("Every answer of every run of each arm, stacked: right, null, wrong. "
            + "; ".join(f"{a}: {c['right']} right, {c['null']} null, {c['wrong']} wrong"
                        for a, c in counts.items()) + ".")

    def svg(suffix, w):
        return stacked_chart(cid + suffix, title, desc,
                             [(a, [c["right"], c["null"], c["wrong"]]) for a, c in counts.items()],
                             [("right", "s1"), ("null", "neutral"), ("wrong", "s2")], left=left, right=right, width=w)
    return Chart(svg, title, desc,
                 Table(["Arm", "Answers", "Right", "Null", "Wrong"],
                       [[code(a), str(sum(c.values())), str(c["right"]), str(c["null"]), str(c["wrong"])]
                        for a, c in counts.items()]), width)


def task_chart(cid, run, name):
    rows = run.task_rows()
    cells = [[(float(v), v, f"{row[0]}, {arm}: mean score {v} over {len(run.of(arm, row[0]))} runs")
              for arm, v in zip(run.arms, row[2:])] for row in rows]
    title = f"Mean score per task and arm, {name}"
    desc = ("The mean score of the runs of each task and arm, from 0 (no question right) to 1 (all right). "
            + " ".join(f"{row[0]}: " + ", ".join(f"{a} {v}" for a, v in zip(run.arms, row[2:])) + "."
                       for row in rows))
    svg = heatmap(cid, title, desc, [r[0] for r in rows], run.arms, cells)
    table = Table(["Task", "Questions"] + [code(a) for a in run.arms], rows)
    return Chart(svg, title, desc, table)


# ---------------------------------------------------------------- footer of every page


def about_run(anchor, folder, commit, ormaos_commit, models, claude, date, extra, commands, needs):
    short, ormaos_short = commit[:7], ormaos_commit[:7]
    files = [f"[`results.jsonl`]({blob(commit, folder / 'results.jsonl')}): one line per run",
             f"[`streams/`]({tree(commit, folder / 'streams')}): what every agent said and did",
             f"[`report.md`]({blob(commit, folder / 'report.md')}): the report the runner wrote"]
    items = [f"Results folder: [`{rel(folder)}`]({tree(commit, folder)})",
             f"ormaos-examples commit that added these results: [`{short}`]({EXAMPLES}/commit/{commit})",
             f"Ormaos commit: [`{ormaos_short}`]({ORMAOS}/commit/{ormaos_short})" + extra,
             "Model: " + joined(code(m) for m in models) + ", with the `claude` command line "
             + joined(claude),
             f"Date: {date}"]
    return Section(anchor, "This run", [
        UL(items),
        P("The results files, on GitHub:"),
        UL(files),
        P(f"To run it again: {needs}"),
        Commands(commands),
    ])


def clone_commands(commit, ormaos_commit, folder):
    return ["git clone https://github.com/ormaos/ormaos-python",
            f"git -C ormaos-python checkout {ormaos_commit[:7]}",
            "git clone https://github.com/ormaos/ormaos-examples",
            f"cd ormaos-examples && git checkout {commit[:7]} && cd {folder}"]


NEEDS = ("Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, git, the "
         "`claude` command line signed in, and a checkout of ormaos-python next to this repository. The run "
         "sends the folders it makes to the model's API.")


# ---------------------------------------------------------------- knows2


def knows2_page(run, h, frame):
    built = run.built
    model = joined(code(m) for m in run.models)
    n_tasks, n_arms, n_runs = len(run.names), len(run.arms), len(run.runs)
    dropped = {name: built["tasks"][name]["dropped"] for name in run.names if built["tasks"][name]["dropped"]}
    written = sum(built["tasks"][n]["questions"] + len(built["tasks"][n]["dropped"]) for n in run.names)
    kept = sum(built["tasks"][n]["questions"] for n in run.names)
    dropped_text = {}
    for line in run.report.splitlines():
        m = re.match(r"- ([\w-]+), (q\d+): (\".*?\") Reason:", line)
        if m:
            dropped_text[(m.group(1), m.group(2))] = m.group(3)
    readme = (BENCH / "knows2" / "README.md").read_text(encoding="utf-8")
    writer_prompt = re.search(r"^> (Write .*)$", readme, re.M).group(1)
    ended = [r for r in run.records if r["timed_out"] or r["error"] or r["answers_file"] != "read"]

    sections = [Section("top", "knows2: what an agent knows about an execution", [
        P(f"N = {len(run.records)} runs: {n_tasks} tasks x {n_arms} arms x {n_runs} runs, model {model}, "
          f"{run.date}. An agent gets the folder an execution left and questions about what happened in it, "
          "written by a model that was not told what Ormaos records; its answers are graded against an oracle "
          "that reads neither the trace nor the recording.", "lead"),
        P(SENTENCE, "sentence"),
        Facts([(f"{run.mean(a):.2f}", f"`{a}`, mean score, 95% interval "
                f"{run.interval(a)[0]:.2f} to {run.interval(a)[1]:.2f}") for a in run.arms]),
        Toc([("method", "Method"), ("results", "Results")]
            + [(n, KINDS[n]["heading"]) for n in run.names]
            + [("null-reasons", "What the agents said when they could not answer"), ("limits", "Limits"),
               ("this-run", "This run")]),
    ], first=True)]

    arm_rows = [
        ["`none`", "nothing", "nothing"],
        ["`raw`", "`result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of the "
                  "execution, default settings", "that the file is there and how to read it"],
        ["`ormaos`", "`.ormaos/`: the recording of `ormaos run`, default settings, and the `ormaos` command "
                     "line in `.venv/`", "that the recording is there, and to run `.venv/bin/ormaos guide` first"],
        ["`ormaos-values`", "`.ormaos/`: the recording of `ormaos run --values`, and the same command line",
         "the sentence of `ormaos`, with \"values included\""],
    ]
    example = "data-pipeline" if "data-pipeline" in run.names else run.names[0]
    sections.append(Section("method", "Method", [
        H(3, "The questions: a writer that was not told about Ormaos"),
        P(f"For each task, {model} wrote the questions once, in bubblewrap, in a folder that held only the "
          "source files of the program, its README, and what the execution printed (`stdout.txt`, "
          "`stderr.txt`). No input file, no file the execution wrote, no `.venv`, no `.ormaos`, no trace; "
          "nothing in the folder or in the prompt names Ormaos or says that the execution was recorded or "
          "traced. Where a README or the notebook spoke of Ormaos, those words were taken out for the writer. "
          "No question was edited, reworded or replaced. The prompt, after its first two sentences (what ran, "
          "what the folder holds):"),
        Pre("The writer's prompt", writer_prompt),
        P(f"The writers wrote {written} questions; {kept} are kept. An agent gets each question with the "
          "writer's words and the writer's format. The writer's folder, prompt, transcript and questions are in "
          f"[`agent-bench/knows2/writer/`]({tree(run.commit, BENCH / 'knows2' / 'writer')})."),
        H(3, "The oracle: one more execution, under sys.settrace"),
        P("The answers come from one more execution of the same program, independent of the arms, under "
          "`sys.settrace`, with wrappers around `open` and `sqlite3.connect`. "
          f"[`oracle.py`]({blob(run.commit, BENCH / 'knows2' / 'oracle.py')}) computes every answer from that "
          "trace and from the files that execution left. It never reads an Ormaos recording or a VizTracer "
          "trace."),
        H(3, "Rules written before any agent ran"),
        P(f"Each question has a rule in [`rules.json`]({blob(run.commit, BENCH / 'knows2' / 'rules.json')}), "
          "written, with the oracle, before any agent ran: numbers equal in value, names compared by their last "
          "dotted part, lists in order or as sets, a word out of a few without regard to capitals, a number "
          "rounded to the decimals its format names. An answer is right or wrong as a whole. The score of a run "
          "is the share of the task's kept questions it got right. Every answer is counted as **right** (by the "
          "rule of its question), **null** (the agent wrote null) or **wrong** (not null, and the rule marks it "
          "wrong)."),
        H(3, "The drop rule"),
        P("A question is dropped only when the oracle cannot give one unambiguous answer to it: not because an "
          "arm cannot answer it, not because it is hard, not because of what any agent answered. Dropped:"),
        UL([f"`{name}`, {qid}, {dropped_text.get((name, qid), '')}: {reason}"
            for name, qs in dropped.items() for qid, reason in qs.items()] or ["none"]),
        H(3, "The sandbox"),
        P("Each run copies the task's folder and mounts it at `/srv/<task>` inside bubblewrap, with nothing else "
          "of the machine but the system (`/usr` and `/etc`, read-only), the `claude` program and its login. "
          f"`claude -p --model {', '.join(run.models)} --safe-mode --strict-mcp-config` gets the prompt, with "
          "the tools Bash, Read, Grep, Glob, Edit and Write, and the runner's time limit. The network is not cut: the agent "
          "needs it to reach the model. The execution was played once per arm and once more for the oracle, in "
          "separate copies mounted at the same path, and the build stopped if the copies did not leave the same "
          "files."),
        H(3, "The first attempt counts"),
        P(f"Every slot (task, arm, run) was run once, and every run counts: nothing was run again and nothing "
          f"is left out. Runs that ended out of time, with an error, or without an `answers.json` that reads as "
          f"JSON: {len(ended)}."),
        H(3, "The arms"),
        Table(["Arm", "Added to the folder", "Added to the prompt"], arm_rows, numbers=False),
        H(3, "Each arm's prompt, verbatim"),
        P(f"The prompts of `{example}`. The first sentence and the files taken out are the task's own; each "
          "task's section below has its four prompts."),
    ] + [Pre(f"`{arm}`", h.prompt(example, arm)) for arm in run.arms]))

    # Results
    rnw = rnw_chart("rnw", run)
    wrong = [(r, qid, given) for r in run.records for qid in r["right"]
             for kind, given in [run.outcome(r, qid)] if kind == "wrong"]
    wrong_block = (Table(["Task", "Arm", "Run", "Question", "Answer", "Oracle"],
                         [[r["task"], code(r["arm"]), str(r["run"]), qid, code(dumped(given)),
                           code(dumped(run.oracle(r["task"])[qid]))] for r, qid, given in wrong], numbers=False)
                   if wrong else None)

    def tokens_text(v, tick):
        return f"{v / 1000:.0f}k" if tick else f"{v:,.0f}"

    tok_rows = [(a, SLOT[a], run.median(a, "tokens"), f"{a}: median {run.median(a, 'tokens'):,.0f} tokens")
                for a in run.arms]
    tok_title = "Median tokens per run, per arm"
    tok_desc = ("Input, output and cache tokens added up, as the claude command line reports them; the median "
                "over the runs of each arm. " + "; ".join(f"{a} {v:,.0f}" for a, _, v, _ in tok_rows) + ".")
    wall_rows = [(a, SLOT[a], run.median(a, "wall_seconds"),
                  f"{a}: median {run.median(a, 'wall_seconds'):.1f} s") for a in run.arms]
    wall_title = "Median wall time per run, per arm"
    wall_desc = ("From the start of the agent to its end, the median over the runs of each arm, in seconds. "
                 + "; ".join(f"{a} {v:.1f} s" for a, _, v, _ in wall_rows) + ".")
    cost = [r["cost_usd"] for r in run.records if r.get("cost_usd") is not None]
    cost_line = (f"Cost, as the claude command line reports it (`total_cost_usd`): ${sum(cost):.2f} for "
                 f"{len(cost)} runs; mean per run, " + ", ".join(
                     f"`{a}` ${statistics.fmean([r['cost_usd'] for r in run.of(a)]):.3f}" for a in run.arms) + ".")

    sizes = []
    for name in run.names:
        t = built["tasks"][name]
        values = {"raw": t["trace_bytes"], "ormaos": t["bytes_ormaos"], "ormaos-values": t["bytes_ormaos-values"]}
        for k in list(values):
            values[k + ":text"] = f"{values[k]:,} bytes"
        sizes.append((name, values))
    lo_exp = math.floor(math.log10(min(v["ormaos"] for _, v in sizes)))
    hi_exp = math.ceil(math.log10(max(v["raw"] for _, v in sizes)))
    size_title = "Size of the trace and of the recording, per task"
    size_desc = ("What the raw arm and the two Ormaos arms add to the folder, in bytes, on a log scale: the "
                 "VizTracer trace (`result.json`) and the `.ormaos/` folder. "
                 + "; ".join(f"{n}: raw {size_text(v['raw'])}, ormaos {size_text(v['ormaos'])}, ormaos-values "
                             f"{size_text(v['ormaos-values'])}" for n, v in sizes) + ".")
    size_chart = Chart(
        lambda sfx, w: log_dots("size" + sfx, size_title, size_desc, sizes,
                                [("raw", "raw", 2), ("ormaos", "ormaos", 3), ("ormaos-values", "ormaos-values", 4)],
                                [10 ** e for e in range(lo_exp, hi_exp + 1)],
                                lambda t: size_text(t).replace(".0", ""), width=w),
        size_title, size_desc,
        Table(["Task", "`raw` (bytes)", "`ormaos` (bytes)", "`ormaos-values` (bytes)"],
              [[n, f"{v['raw']:,}", f"{v['ormaos']:,}", f"{v['ormaos-values']:,}"] for n, v in sizes]))

    sections.append(Section("results", "Results", [
        P("The score of a run is the share of the task's questions its `answers.json` got right. The interval "
          f"is a 95% bootstrap interval of the mean over the runs of the arm ({h.base.RESAMPLES:,} resamples), "
          "computed with the runner's own function."),
        score_chart("score", run, "knows2"),
        rnw,
        P("Every wrong answer:" if wrong else "Every wrong answer: none."),
    ] + ([wrong_block] if wrong else []) + [
        task_chart("tasks", run, "knows2"),
        P("In " + f"{len(run.full_marks())} of {n_tasks} tasks every arm scored 1.00: "
          + joined(f"`{n}`" for n in run.full_marks()) + "."),
        Chart(lambda sfx, w: bar_chart("tokens" + sfx, tok_title, tok_desc, tok_rows, tokens_text, width=w),
              tok_title, tok_desc,
              Table(["Arm", "Median tokens"], [[code(a), f"{v:,.0f}"] for a, _, v, _ in tok_rows])),
        Chart(lambda sfx, w: bar_chart("wall" + sfx, wall_title, wall_desc, wall_rows,
                                       lambda v, tick: f"{v:.0f} s", width=w),
              wall_title, wall_desc,
              Table(["Arm", "Median wall time (s)"], [[code(a), f"{v:.1f}"] for a, _, v, _ in wall_rows])),
        P(cost_line),
        size_chart,
    ]))

    # One section per task
    for name in run.names:
        kind = KINDS[name]
        heading, source = kind["heading"], kind["source"]
        does = kind["does"] + (" " + kind["night"] if kind.get("night") else "")
        task = h.tasks.TASKS[name]
        removed = built["tasks"][name]["removed"]
        questions = run.questions(name)
        oracle = run.oracle(name)
        blocks = [
            P(does + f" Source: [`{source}`]({tree(run.commit, REPO / source)})."),
            P("The execution: " + task["what"] + (" Taken out of the folder afterwards: "
                                                   + joined(f"`{f}`" for f in removed) + "." if removed else "")),
            P("Mean score: " + ", ".join(f"`{a}` {run.mean(a, name):.2f}" for a in run.arms) + ". Run 1 of each "
              f"arm side by side, and every run: [the situation's page](/benchmarks/cases/knows2-{name}/)."),
        ]
        cells = [[(run.right_runs(name, q["id"], a) / len(run.of(a, name)),
                   f"{run.right_runs(name, q['id'], a)}/{len(run.of(a, name))}",
                   f"{q['id']}, {a}: {run.right_runs(name, q['id'], a)} of {len(run.of(a, name))} runs right")
                  for a in run.arms] for q in questions]
        hm_title = f"Runs right per question and arm, {name}"
        hm_desc = (f"For each question of {name}, how many of the runs of each arm got it right. "
                   + " ".join(f"{q['id']}: " + ", ".join(f"{a} {c[1]}" for a, c in zip(run.arms, row)) + "."
                              for q, row in zip(questions, cells)))
        blocks.append(Chart(heatmap(f"q-{name}", hm_title, hm_desc, [q["id"] for q in questions], run.arms, cells),
                            hm_title, hm_desc,
                            Table(["Question"] + [code(a) for a in run.arms],
                                  [[q["id"]] + [c[1] for c in row] for q, row in zip(questions, cells)])))
        for q in questions:
            blocks.append(H(3, f"{q['id']}. {q['question']}", f"{name}-{q['id']}"))
            blocks.append(P(f"Format: {q['format']}. The oracle: {code(dumped(oracle[q['id']]))}."))
            rows = []
            for arm in run.arms:
                row = [code(arm)]
                for r in sorted(run.of(arm, name), key=lambda r: r["run"]):
                    kind, given = run.outcome(r, q["id"])
                    row.append(kind if kind == "null" else f"{kind}: {code(dumped(given))}")
                rows.append(row)
            blocks.append(Table(["Arm"] + [f"Run {n}" for n in run.runs], rows, numbers=False, cls="answers"))
        blocks.append(Details(f"The four prompts of {name}",
                              [Pre(f"`{arm}`", h.prompt(name, arm)) for arm in run.arms]))
        sections.append(Section(name, heading, blocks))

    # Null reasons, run 1 of every arm
    said = []
    first_runs = [r for r in run.records if r["run"] == 1]
    with_null = 0
    for name in run.names:
        for arm in run.arms:
            r = next(x for x in first_runs if x["task"] == name and x["arm"] == arm)
            nulls = [q for q in r["right"] if run.outcome(r, q)[0] == "null"]
            if not nulls:
                continue
            with_null += 1
            said.append(H(3, f"{name}, `{arm}`, run 1: null for {', '.join(nulls)}"))
            said.append(Pre(f"The agent's last message, from [`{r['stream']}`]"
                            f"({blob(run.commit, run.folder / r['stream'])})", run.last_text(r)))
    sections.append(Section("null-reasons", "What the agents said when they could not answer", [
        P(f"Run 1 of every task and arm, always run 1: {len(first_runs)} runs, of which {with_null} wrote null "
          "for at least one question. For each of them, the last message the agent wrote, quoted from its "
          "stream as it is."),
    ] + said))

    sections.append(Section("limits", "Limits", [
        P("As the run's report lists them:"),
        UL(section_lines(run.report, "Limits")),
    ]))
    sections.append(about_run(
        "this-run", run.folder, run.commit, built["ormaos_commit"], run.models, run.claude, run.date,
        f"; VizTracer {built['viztracer']}; {built['python']}",
        clone_commands(run.commit, built["ormaos_commit"], "agent-bench/knows2")
        + ["python3 build.py", f"python3 run.py --runs {len(run.runs)} --replacements 0"], NEEDS))
    title = "knows2: what an agent knows about an execution"
    return title, sections


# ---------------------------------------------------------------- knows


def knows_page(run, new):
    built = run.built
    model = joined(code(m) for m in run.models)
    sections = [Section("top", "knows: the earlier run", [
        P(f"N = {len(run.records)} runs: {len(run.names)} tasks x {len(run.arms)} arms x {len(run.runs)} runs, "
          f"model {model}, {run.date}. The same {len(run.names)} executions as knows2, with questions written by the people "
          "who make Ormaos.", "lead"),
        P(SENTENCE, "sentence"),
        Toc([("why", "Why knows2 replaced it"), ("results", "Results"), ("limits", "Limits"),
             ("this-run", "This run")]),
    ], first=True)]
    sections.append(Section("why", "Why knows2 replaced it", [
        P("In knows, the programs, the executions and the questions were all written by the people who make "
          "Ormaos, and the questions ask about calls, exceptions, shapes and I/O: what Ormaos records. That "
          "choice of questions can favour the recording. [knows2](/benchmarks/knows2/) keeps the same executions "
          "and an oracle under `sys.settrace`, and has the questions written by a model that saw only the source, "
          "the README and the printed output of each program and was not told about Ormaos; it adds a fourth "
          "arm, a recording with values, counts every answer as right, null or wrong, and drops a question only "
          "when the oracle cannot answer it. The tasks and the oracle are described on its page."),
    ]))
    sections.append(Section("results", "Results", [
        P("The score of a run is the share of its questions that are right, by the rules of "
          f"[`rules.json`]({blob(run.commit, BENCH / 'knows' / 'rules.json')}), written before the run. The "
          "interval is a 95% bootstrap interval of the mean over the runs of the arm."),
        score_chart("score", run, "knows"),
        task_chart("tasks", run, "knows"),
    ]))
    sections.append(Section("limits", "Limits", [P("As the run's report lists them:"),
                                                 UL(section_lines(run.report, "Limits"))]))
    sections.append(about_run(
        "this-run", run.folder, run.commit, built["ormaos_commit"], run.models, run.claude, run.date,
        f"; VizTracer {built['viztracer']}; {built['python']}",
        clone_commands(run.commit, built["ormaos_commit"], "agent-bench/knows")
        + ["python3 build.py", f"python3 run.py --runs {len(run.runs)}"], NEEDS))
    return "knows: the earlier run", sections


# ---------------------------------------------------------------- fix


# Where each program of the fix benchmark behaves otherwise than its README
# says, in the words of the benchmark's README, without judging them.
DIFFERS = {
    "order-sync": "an exception that is caught and not shown",
    "freight-quote": "a fallback, with nothing printed, after HTTP calls that returned an error",
    "late-fees": "a branch taken because of a value in the environment",
    "statement-import": "a loop that stops before the end of its input",
    "fx-rates": "a retry that makes its call once",
    "price-import": "a subprocess whose exit code is not read",
    "points-grant": "an SQL statement that also writes other rows",
    "commission-run": "a value kept from one item to the next",
}

# What the data of each program showed the morning after, in one sentence.
# The items are those the scenario's own check of the data (`wrong`) found,
# as build.py wrote them into build.json.
FIX_MORNING = {
    "order-sync": lambda w: f"This morning the stock of {_n(len(w), 'SKU')} in `data/inventory.db` is not the "
                            f"warehouse's count in `data/count.csv`: {_ids(w)}.",
    "freight-quote": lambda w: f"This morning {_n(len(w), 'quote')} of last night are not what the carrier charged "
                               f"in `data/booked.csv`: {_ids(w)}.",
    "late-fees": lambda w: "This morning the billing database has no late fee dated "
                           + joined(re.sub(r"^no fee on ", "", x) for x in w) + ", the night of the run.",
    "statement-import": lambda w: "This morning " + joined(
        re.sub(r"^ledger (-?\d+), bank (-?\d+)$", r"the ledger adds up to \1 and the bank's closing balance of "
               r"yesterday is \2", x) for x in w) + ".",
    "fx-rates": lambda w: f"This morning {_n(len(w), 'currency', 'currencies')} still have the rate of the day "
                          f"before: {_ids(w)}.",
    "price-import": lambda w: f"This morning {_n(len(w), 'price')} in the catalog are not those of the supplier's "
                              f"list: {_ids(w)}.",
    "points-grant": lambda w: f"This morning the points of {_n(len(w), 'member')} are not the sum of their "
                              f"grants: {_ids(w)}.",
    "commission-run": lambda w: f"This morning the payouts of {_n(len(w), 'rep')} for yesterday are not what "
                                f"finance worked out: {_ids(w)}.",
}


class FixRun:
    def __init__(self, folder, h):
        self.folder, self.h = folder, h
        self.records = jsonl(folder / "results.jsonl")
        for r in self.records:
            r["_agent"], r["_run"] = agent_of(r), self
        self.agents = sorted({r["_agent"] for r in self.records})
        self.first = [r for r in self.records if r["attempt"] == 0]
        self.built = json.loads((folder / "build.json").read_text(encoding="utf-8"))
        self.report = (folder / "report.md").read_text(encoding="utf-8")
        self.arms = [a for a in ARMS4 if any(r["arm"] == a for r in self.first)]
        readme = (BENCH / "README.md").read_text(encoding="utf-8")
        table = re.search(r"\| Bug \| The job \| The kind of bug \|\n\|.*?\n((?:\|.*\n)+)", readme).group(1)
        self.cases = []
        for line in table.splitlines():
            name, job, _ = [c.strip() for c in line.strip("|").split("|")]
            name = name.strip("`")
            if name not in DIFFERS:
                raise SystemExit(f"agent-bench/README.md: {name} has no line in DIFFERS of build.py")
            self.cases.append((name, re.sub(r"\s*\(\[`[^`]*`\]\([^)]*\)\)", "", job), DIFFERS[name]))
        if {r["bug"] for r in self.first} != {c for c, _, _ in self.cases}:
            raise SystemExit("the cases of results.jsonl are not those of agent-bench/README.md")
        self.runs = sorted({r["run"] for r in self.first})
        self.commit = added_in(folder / "results.jsonl")
        self.models = sorted({r["model"] for r in self.records})
        self.claude = sorted({r["claude"] for r in self.records})
        self.date = date_of(folder)

    def of(self, arm=None, case=None):
        return [r for r in self.first if arm in (None, r["arm"]) and case in (None, r["bug"])]

    def fixed(self, arm, case=None):
        return sum(1 for r in self.of(arm, case) if r["fixed"])

    def summary_rows(self):
        bench_run, number = self.h.base.bench_run, self.h.base.number
        rows = []
        for arm in self.arms:
            records = self.of(arm)
            low, high = self.h.benchlib.wilson(self.fixed(arm), len(records))
            rows.append([arm, f"{self.fixed(arm)}/{len(records)}", f"{100 * low:.0f}% to {100 * high:.0f}%",
                         number(bench_run.median([r["wall_seconds"] for r in records]), "{:.0f} s"),
                         number(bench_run.median([r["tool_calls"] for r in records])),
                         number(bench_run.median([bench_run.tokens_of(r) for r in records])),
                         str(sum(1 for r in records if r["timed_out"]))])
        same_as_report(rows, self.report, "Arm", rel(self.folder))
        return rows


def fixed_chart(cid, run, width=None, compact=False, left=130, right=190):
    """The metric fixed per arm, with its Wilson interval."""
    rows = []
    for arm in run.arms:
        low, high = run.h.benchlib.wilson(run.fixed(arm), len(run.of(arm)))
        f, n = run.fixed(arm), len(run.of(arm))
        rows.append((arm, SLOT[arm], f / n, low, high, f"{f}/{n} ({100 * low:.0f}% to {100 * high:.0f}%)",
                     f"{arm}: fixed {f} of {n}, 95% Wilson interval {100 * low:.0f}% to {100 * high:.0f}%"))
    title = "The metric fixed, per arm"
    desc = ("The share of first attempts of each arm whose code passed the check, with its 95% Wilson score "
            "interval. " + "; ".join(f"{r[0]} {r[5]}" for r in rows) + ".")

    def svg(suffix, w):
        return interval_chart(cid + suffix, title, desc, rows, [0, 0.25, 0.5, 0.75, 1.0], lambda t: f"{100 * t:.0f}%",
                              left=left, right=right, width=w)
    summary = run.summary_rows()
    if compact:
        table = Table(["Arm", "Fixed", "95% interval"], [[code(r[0])] + r[1:3] for r in summary])
    else:
        table = Table(["Arm", "Fixed", "95% interval", "Median wall time", "Median tool calls", "Median tokens",
                       "Timed out"], [[code(r[0])] + r[1:] for r in summary])
    return Chart(svg, title, desc, table, width)


def fix_title(run):
    return f"fix: {len(run.cases)} programs that behaved otherwise than their README"


def fix_page(run):
    model = joined(code(m) for m in run.models)
    h = run.h
    intervals = {a: h.benchlib.wilson(run.fixed(a), len(run.of(a))) for a in run.arms}
    pairs = overlapping(intervals)
    sections = [Section("top", fix_title(run), [
        P(f"N = {len(run.first)} runs: {len(run.cases)} programs x {len(run.arms)} arms x {len(run.runs)} runs, "
          f"the first attempt of every slot, model {model}, {run.date}. A coding agent gets a scheduled program "
          "that behaved otherwise than its README on one night, the data that night left and a "
          "one-sentence symptom. A check it does not see then plays that night again on the code the agent left; "
          "`fixed` is the name of the metric that counts the runs whose code passed it.", "lead"),
        P(SENTENCE, "sentence"),
        Facts([(f"{run.fixed(a)}/{len(run.of(a))}", f"`{a}`, `fixed`, 95% interval "
                f"{100 * intervals[a][0]:.0f}% to {100 * intervals[a][1]:.0f}%") for a in run.arms]),
        Toc([("method", "Method"), ("results", "Results"), ("limits", "Limits"), ("this-run", "This run")]),
    ], first=True)]
    sections.append(Section("method", "Method", [
        H(3, "The programs"),
        P(f"{len(run.cases)} small scheduled Python programs, standard library only. Each runs from cron, prints "
          "its OK line and exits with code 0; on one night it behaved otherwise than its README, in "
          "a different place in each program, and that shows only in the data it left. Running it again today "
          "does not show it: that night's input is gone."),
        Table(["Program", "What it does, by its README", "Where it behaved otherwise than its README"],
              [[code(c), j, d] for c, j, d in run.cases], numbers=False),
        H(3, "The arms"),
        Table(["Arm", "Added to the folder", "Added to the prompt"], [
            ["`none`", "nothing", "nothing"],
            ["`raw`", "`result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of that "
                      "night's run, default settings", "that the file is there and how to read it"],
            ["`ormaos`", "`.ormaos/`: the Ormaos recording of that night's run, and `.venv/` with the `ormaos` "
                         "command line", "that the recording is there, and to run `.venv/bin/ormaos guide` first"],
        ], numbers=False),
        P("All arms have the same code, data and task text: the symptom, how cron runs the program, and \"Find "
          "the cause and fix it.\" The nights are played once per arm, in copies mounted at the same path, and "
          "the build stops if the copies do not leave the same data."),
        H(3, "The check"),
        P("For each program, `hidden/check.py`, not in the agent's folder, plays that night again on the code the "
          "agent left, and nights on which the program did what its README says. It passes when that night's "
          "data now comes out as the README describes and the other nights end as before, with exit code 0 and "
          "the program's last line as cron reads it. The metric `fixed` counts the runs whose code passed it."),
        H(3, "The sandbox"),
        P(f"The folder is mounted at `/srv/<program>` inside bubblewrap, with nothing else of the machine but the "
          f"system (`/usr` and `/etc`, read-only), the `claude` program and its login. `claude -p --model "
          f"{', '.join(run.models)} --safe-mode --strict-mcp-config` gets the task text, with the tools Bash, "
          "Read, Grep, Glob, Edit and Write, and the runner's time limit. The network is not cut: the agent needs "
          "it to reach the model."),
        H(3, "Scored by the first attempt of every slot"),
        P(f"What counts is the first attempt of every program, arm and run: all {len(run.first)} of them, as "
          "planned before the run. A run that used up its time counts with the code it left. An attempt in which "
          "the agent named a path outside its folder, or that ended with an error, was marked and run again; the "
          f"later attempts ({len(run.records) - len(run.first)}) are listed in the report and do not count. "
          f"First attempts that were marked: {sum(1 for r in run.first if r['read_outside'])}; they count like "
          "the others, since the sandbox has nothing of these programs outside the folder."),
    ]))

    chart = fixed_chart("fixed", run)
    per_case = Table(["Program"] + [code(a) for a in run.arms],
                     [[f"[{code(c)}](/benchmarks/cases/fix-{c}/)"] + [f"{run.fixed(a, c)}/{len(run.of(a, c))}"
                                                                     for a in run.arms]
                      for c, _, _ in run.cases])
    order = {c: i for i, (c, _, _) in enumerate(run.cases)}
    not_fixed = sorted((r for r in run.first if not r["fixed"]),
                       key=lambda r: (order[r["bug"]], run.arms.index(r["arm"]), r["run"]))
    sections.append(Section("results", "Results", [
        P("The interval is the 95% Wilson score interval, computed with the runner's own function. Tokens are "
          "input, output and cache tokens added up, as the claude command line reports them."),
        chart,
        P(overlap_sentence(pairs, run.arms)),
        H(3, "Per program"),
        per_case,
        H(3, "First attempts whose code did not pass the check"),
        P("With what the check said:"),
        UL([f"{code(r['bug'])}, `{r['arm']}`, run {r['run']}: {h.base.bench_run.reason(r)}" for r in not_fixed]
           or ["none"]),
        P("The report adds an analysis made after seeing the results, not planned before the run, which changes "
          "nothing in the tables: the folders these runs left were read by hand. See its section \"After the "
          f"run\" in [`report.md`]({blob(run.commit, run.folder / 'report.md')})."),
    ]))
    sections.append(Section("limits", "Limits", [UL([
        f"The {len(run.cases)} programs, and where each one behaved otherwise than its README, were written "
        "for this benchmark by the people who make Ormaos; they are not a sample of real programs.",
        "One model, one prompt per arm, one tracer with its default settings.",
        "The dates in the data are relative to the day `build.py` ran: build on the day of the run.",
    ])]))
    sections.append(about_run(
        "this-run", run.folder, run.commit, run.built["ormaos_commit"], run.models, run.claude, run.date,
        f"; VizTracer {run.built['viztracer']}; {run.built['python']}",
        clone_commands(run.commit, run.built["ormaos_commit"], "agent-bench")
        + ["python3 build.py", f"python3 run.py --runs {len(run.runs)}"], NEEDS))
    return fix_title(run), sections


# ---------------------------------------------------------------- overhead


class Overhead:
    def __init__(self):
        self.text = (OVERHEAD / "RESULTS.md").read_text(encoding="utf-8")
        self.source = json.loads((OVERHEAD / "source.json").read_text(encoding="utf-8"))
        body = self.text.split("\n## ", 1)[0]
        self.intro = [p for p in body.split("\n\n")[1:] if not p.startswith("- ")][0].strip()
        self.facts = dict(line[2:].split(": ", 1) for line in body.splitlines() if line.startswith("- "))
        self.runs = int(re.match(r"(\d+) runs", self.facts["N"]).group(1))
        self.workloads = []
        for part in self.text.split("\n## ")[1:]:
            title, rest = part.split("\n", 1)
            if title == "How to read it":
                self.reading = [line[2:] for line in rest.splitlines() if line.startswith("- ")]
                continue
            about = rest.strip().split("\n\n")[0]
            lines = [line for line in rest.splitlines() if line.startswith("|")]
            header = [c.strip() for c in lines[0].strip("|").split("|")]
            rows = [dict(zip(header, (c.strip() for c in line.strip("|").split("|")))) for line in lines[2:]]
            for row in rows:
                m = re.search(r"\(x([\d.]+)\)", row["Added to the median"])
                row["ratio"] = float(m.group(1)) if m else None
            notes = [line[2:] for line in rest.split("Listed as not collected", 1)[-1].splitlines()
                     if line.startswith("- ")] if "Listed as not collected" in rest else []
            self.workloads.append((title, about, header, rows, notes))

    def default(self, rows):
        return next(r for r in rows if "(the default)" in r["Capability set"])


def ratio_chart(cid, over, width=None, left=270):
    """The time of a recorded run, as a multiple of the run without Ormaos."""
    series = [(title, title.replace(" workload", ""), i + 1) for i, (title, *_rest) in enumerate(over.workloads)]
    sets = [r["Capability set"] for r in over.workloads[0][3] if r["ratio"]]
    rows = []
    for cap in sets:
        values = {}
        for title, _, _, wrows, _ in over.workloads:
            row = next(r for r in wrows if r["Capability set"] == cap)
            values[title] = row["ratio"]
            values[title + ":text"] = f"x{row['ratio']:.2f} ({row['Median (ms)']} ms)"
        rows.append((cap, values))
    top = 10 ** math.ceil(math.log10(max(v for _, vals in rows for k, v in vals.items() if ":" not in k)))
    ticks = [t for t in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if t <= top]
    title = "Time of a recorded run, as a multiple of the same run without Ormaos"
    desc = ("The median wall time of each capability set divided by the median without Ormaos, per workload, on "
            "a log scale. " + "; ".join(f"{cap}: " + ", ".join(f"{s[1]} {vals[s[0] + ':text']}" for s in series)
                                        for cap, vals in rows) + ".")
    label_of = {cap: cap.replace(" (the default)", ", the default") for cap in sets}
    return Chart(lambda sfx, w: log_dots(cid + sfx, title, desc, [(label_of[c], v) for c, v in rows], series,
                                         ticks, lambda t: f"x{t}", left=left, width=w),
                  title, desc,
                  Table(["Capability set"] + [f"{s[1]}" for s in series],
                        [[cap] + [f"x{vals[s[0]]:.2f}" for s in series] for cap, vals in rows]), width)


def overhead_page(over):
    commit = over.source["commit"]
    results_url = f"{ORMAOS}/blob/{commit}/{over.source['path']}"
    chart = ratio_chart("ratios", over)
    blocks = [chart]
    for title_w, about, header, wrows, notes in over.workloads:
        blocks.append(H(3, title_w))
        blocks.append(P(about))
        blocks.append(Table(header, [[r[h] for h in header] for r in wrows], numbers=False))
        if notes:
            blocks.append(P("Listed as not collected in these recordings:"))
            blocks.append(UL(notes))
    cpu, io = over.workloads[0], over.workloads[1]
    cpu_d, io_d = over.default(cpu[3]), over.default(io[3])
    sections = [Section("top", "overhead: what recording adds to the time of a run", [
        P(f"N = {over.facts['N']}. {over.intro}", "lead"),
        P(SENTENCE, "sentence"),
        Facts([(f"x{cpu_d['ratio']:.2f}", f"{cpu[0]}, the default capability set, median "
                f"{cpu_d['Median (ms)']} ms"),
               (f"x{io_d['ratio']:.2f}", f"{io[0]}, the default capability set, median {io_d['Median (ms)']} ms")]),
        Toc([("results", "Results"), ("machine", "The machine"), ("reading", "How to read it"),
             ("this-run", "This run")]),
    ], first=True)]
    sections.append(Section("results", "Results", blocks))
    sections.append(Section("machine", "The machine", [UL([f"{k}: {v}" for k, v in over.facts.items()])]))
    sections.append(Section("reading", "How to read it", [P("As the results file says:"), UL(over.reading)]))
    sections.append(Section("this-run", "This run", [
        UL([f"Results file: [`{over.source['path']}`]({results_url}) of ormaos-python, written by "
            f"[`bench/run.py`]({ORMAOS}/blob/{commit}/bench/run.py)",
            f"Ormaos commit: [`{commit[:7]}`]({ORMAOS}/commit/{commit}), version {over.facts['Ormaos']}",
            f"The copy these pages read: [`{rel(OVERHEAD / 'RESULTS.md')}`]({EXAMPLES}/blob/main/"
            f"{rel(OVERHEAD / 'RESULTS.md')}), taken by `site/benchmarks/build.py --overhead`",
            f"Date: {over.facts['When']}",
            "No agent and no model: this benchmark has no `results.jsonl` and no streams."]),
        P("To run it again: Linux or another POSIX system, Python 3.12 or newer, and "
          "[uv](https://docs.astral.sh/uv/)."),
        Commands(["git clone https://github.com/ormaos/ormaos-python && cd ormaos-python",
                  f"git checkout {commit[:7]}",
                  f"uv run python bench/run.py --runs {over.runs}"]),
    ]))
    return "overhead: what recording adds to the time of a run", sections


# ---------------------------------------------------------------- streams
#
# What an agent did, read from the stream the claude command line wrote:
# its tool calls in order, each with what the tool gave back.

# The verbs of the ormaos command line (src/ormaos/cli.py of ormaos-python).
# `ormaos --help` counts as the verb "help".
VERBS = ("run", "show", "tree", "exceptions", "path", "io", "logs", "diff", "list", "status", "guide")
_ASSIGN = re.compile(r"(?:^|[\s;&|(])(\w+)=[\"']?[\w./~-]*ormaos(?=[\s;\"')]|$)")
_WRITES_ANSWERS = re.compile(
    r">\s*[\"']?(?:\./)?answers\.json|tee\s+(?:-a\s+)?(?:\./)?answers\.json"
    r"|open\(\s*[\"'](?:\./)?answers\.json[\"']\s*,\s*[\"'][wa]|answers\.json[\"']?\)?\.write_text")
_STEPS = {}


class Step:
    def __init__(self, tool, given):
        self.tool, self.input, self.output, self.line = tool, given or {}, None, None

    @property
    def command(self):
        return self.input.get("command", "") if self.tool == "Bash" else ""


def read_steps(path):
    """(the folder the agent ran in, its tool calls in order)."""
    if path in _STEPS:
        return _STEPS[path]
    cwd, steps, by_id = "", [], {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        event = json.loads(line)
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            cwd = event.get("cwd") or ""
        elif kind == "assistant":
            for part in event["message"].get("content", []):
                if part.get("type") == "tool_use":
                    by_id[part["id"]] = Step(part.get("name", "?"), part.get("input"))
                    steps.append(by_id[part["id"]])
        elif kind == "user" and isinstance(event["message"].get("content"), list):
            for part in event["message"]["content"]:
                if part.get("type") == "tool_result" and part.get("tool_use_id") in by_id:
                    given = part.get("content")
                    text = given if isinstance(given, str) else "\n".join(
                        x.get("text", "") for x in given or [] if isinstance(x, dict))
                    step = by_id[part["tool_use_id"]]
                    step.output, step.line = text, number
    _STEPS[path] = cwd, steps
    return cwd, steps


def ormaos_calls(command):
    """The ormaos verbs a shell command runs, with where each is in it,
    also through a variable (`O=.venv/bin/ormaos; $O tree r1`)."""
    names = sorted(set(_ASSIGN.findall(command)))
    callee = r"(?:[\w./~-]*/)?ormaos" + "".join(rf"|\$\{{?{n}\}}?" for n in names)
    pattern = re.compile(rf"(?:^|(?<=[\s;&|(`]))(?:{callee})[ \t]+({'|'.join(VERBS)}|--help|-h)(?![\w-])")
    return [(m.start(), "help" if m.group(1) in ("--help", "-h") else m.group(1))
            for m in pattern.finditer(command)]


def writes_answers(step):
    """Where in the call answers.json is written, or None."""
    if step.tool in ("Write", "Edit"):
        return 0 if str(step.input.get("file_path", "")).endswith("answers.json") else None
    found = _WRITES_ANSWERS.search(step.command)
    return found.start() if found else None


def verbs_before_answers(steps):
    """The ormaos verbs run before the last write of answers.json, in the
    order they were first run."""
    last = max((i for i, s in enumerate(steps) if writes_answers(s) is not None), default=len(steps) - 1)
    seen = []
    for i, step in enumerate(steps[:last + 1]):
        cut = writes_answers(step) if i == last else None
        for at, verb in ormaos_calls(step.command):
            if (cut is None or at < cut) and verb not in seen:
                seen.append(verb)
    return seen


def shown_command(step, cwd):
    """A tool call as one line or a few, with paths relative to the folder."""
    def short(path):
        path = str(path or ".")
        return path[len(cwd) + 1:] if cwd and path.startswith(cwd + "/") else path
    given = step.input
    if step.tool == "Bash":
        return given.get("command", "")
    if step.tool == "Read":
        extra = "".join(f" {k} {given[k]}" for k in ("offset", "limit") if given.get(k))
        return f"Read {short(given.get('file_path'))}{extra}"
    if step.tool == "Grep":
        return f"Grep {given.get('pattern', '')!r} in {short(given.get('path'))}"
    if step.tool == "Glob":
        return f"Glob {given.get('pattern', '')}" + (f" in {short(given['path'])}" if given.get("path") else "")
    if step.tool in ("Write", "Edit"):
        return f"{step.tool} {short(given.get('file_path'))}"
    return f"{step.tool} {dumped(given)}"


def clipped(text, lines):
    rows = text.splitlines()
    if len(rows) <= lines:
        return text, 0
    return "\n".join(rows[:lines]), len(rows) - lines


def atoms(value):
    """The values an answer holds, as text, to find them in an output."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from atoms(k)
            yield from atoms(v)
    elif isinstance(value, list):
        for v in value:
            yield from atoms(v)
    elif value is not None and not isinstance(value, bool):
        text = str(value)
        yield text
        if "," in text:
            yield from (part.strip() for part in text.split(","))


# A line of questions.json or answers.json printed back: not a value read
# from the execution.
_ECHO = re.compile(r'^\s*"(q\d+|id|question|format)"\s*:')


def used_lines(output, answers, most=15):
    """The lines of an output that hold a value the agent wrote in
    answers.json (values of two characters or more), else its first lines.
    (lines, what they are)."""
    rows = output.splitlines()
    values = {a for v in (answers or {}).values() for a in atoms(v) if len(a) >= 2 and a.lower() not in ("yes", "no")}
    found = [row for row in rows if not _ECHO.match(row)
             and any(re.search(rf"(?<![\w.]){re.escape(v)}(?!\w)", row) for v in values)]
    if found:
        what = (f"the {_n(len(found), 'line')} of {len(rows)} that hold a value it wrote in answers.json"
                if len(found) <= most else f"the first {most} of the {len(found)} lines of {len(rows)} that hold "
                "a value it wrote in answers.json")
        return found[:most], what
    if len(rows) <= most:
        return rows, f"all {_n(len(rows), 'line')}"
    return rows[:most], f"the first {most} of {len(rows)} lines"


# ---------------------------------------------------------------- situations


class Situation:
    """One execution an agent was asked about (knows2) or one program it was
    asked to change (fix), with every run of every agent."""

    def __init__(self, bench, name, records, arms, page_url):
        self.bench, self.name, self.records, self.arms = bench, name, records, arms
        self.id = f"{bench}-{name}"
        self.path = f"cases/{self.id}/"
        self.url = f"/benchmarks/{self.path}"
        self.page_url = page_url
        self.agents = []
        for r in records:
            if r["_agent"] not in self.agents:
                self.agents.append(r["_agent"])

    def score(self, r):
        return float(r["fixed"]) if self.bench == "fix" else r["score"]

    def of(self, arm=None, agent=None):
        rows = [r for r in self.records if arm in (None, r["arm"]) and agent in (None, r["_agent"])]
        return sorted(rows, key=lambda r: (r["_run"].folder.name, r["run"]))

    def mean(self, arm):
        return statistics.fmean(self.score(r) for r in self.of(arm))

    def change(self):
        """The mean of ormaos minus the mean of none."""
        return self.mean("ormaos") - self.mean("none")

    def value_text(self, arm):
        if self.bench == "fix":
            return f"{sum(1 for r in self.of(arm) if r['fixed'])}/{len(self.of(arm))}"
        return f"{self.mean(arm):.2f}"

    def run_label(self, r):
        folders = {x["_run"].folder for x in self.of(agent=r["_agent"])}
        return str(r["run"]) if len(folders) == 1 else f"{r['_run'].date} · {r['run']}"

    def first_run(self, arm, agent):
        """Run 1 of the arm, in the agent's first results folder."""
        rows = self.of(arm, agent)
        return next((r for r in rows if r["run"] == 1 and r["_run"] is rows[0]["_run"]), rows[0])


def stream_url(r, line=None):
    run = r["_run"]
    return blob(run.commit, run.folder / r["stream"]) + (f"?plain=1#L{line}" if line else "")


def outcome_of(r, qid):
    return KnowsRun.outcome(r, qid)


class SideBySide(Block):
    """One column per arm: what one run of each arm did. `columns` are
    dicts: arm, head (lines in the inline marks), steps (command, output or
    None, what part of the output, url), then the end of the run."""

    def __init__(self, columns):
        self.columns = columns

    def html(self):
        out = [f'<div class="sbs" style="--cols:{len(self.columns)}">']
        for col in self.columns:
            out.append(f'<article class="arm-col a{SLOT[col["arm"]]}">')
            out.append(f'<h4><code>{esc(col["arm"])}</code></h4>')
            out.append("".join(f'<p class="meta">{inline(line)}</p>' for line in col["head"]))
            out.append(f'<p class="part">Commands, in order ({len(col["steps"])})</p><ol class="steps">')
            for command, output, what, url in col["steps"]:
                text, more = clipped(command, 12)
                item = f'<pre class="cmd-text">{esc(text)}</pre>'
                if more:
                    item += f'<p class="note">… {_n(more, "more line")} of this command</p>'
                if output is not None:
                    item += (f'<pre class="out">{esc(chr(10).join(output))}</pre>'
                             f'<p class="note">Output: {esc(what)}. <a href="{esc(url)}">Full output</a></p>')
                out.append(f"<li>{item}</li>")
            out.append("</ol>")
            for label, body in col["end"]:
                out.append(f'<p class="part">{inline(label)}</p>')
                out.append(body.html())
            out.append("</article>")
        out.append("</div>")
        return "\n".join(out)

    def md(self):
        out = []
        for col in self.columns:
            out.append(f"#### `{col['arm']}`\n\n" + "\n".join(f"- {to_markdown_inline(x)}" for x in col["head"]))
            lines = [f"Commands, in order ({len(col['steps'])}):", ""]
            for n, (command, output, what, url) in enumerate(col["steps"], 1):
                text, more = clipped(command, 12)
                lines.append(f"{n}. " + fenced(text).replace("\n", "\n   ")
                             + (f"\n\n   … {_n(more, 'more line')} of this command" if more else ""))
                if output is not None:
                    lines.append("\n   Output, " + what + f" ([full output]({url})):\n\n   "
                                 + fenced("\n".join(output)).replace("\n", "\n   "))
            out.append("\n".join(lines))
            for label, body in col["end"]:
                out.append(f"{to_markdown_inline(label)}\n\n{body.md()}")
        return "\n\n".join(out)


class Bars(Block):
    """The situations as rows: a link and a line, small bars per arm, and
    the change from none to ormaos."""

    def __init__(self, situations, arms):
        self.situations, self.arms = situations, arms

    def svg(self, sit):
        row, width, bar = 15, 200, 130
        arms = [a for a in self.arms if a in sit.arms]
        out = [f'<svg class="mini" viewBox="0 0 {width} {row * len(arms)}" width="{width}" '
               f'height="{row * len(arms)}" role="img" aria-label="'
               + esc(", ".join(f"{a} {sit.value_text(a)}" for a in arms)) + '">']
        for i, arm in enumerate(arms):
            y = i * row
            share = sit.mean(arm)
            out.append(f'<rect class="track" x="0" y="{y + 3}" width="{bar}" height="8" rx="1.5"/>')
            if share:
                out.append(f'<rect class="s{SLOT[arm]}" x="0" y="{y + 3}" width="{fmt(max(bar * share, 1.5))}" '
                           f'height="8" rx="1.5"><title>{esc(arm)}: {esc(sit.value_text(arm))}</title></rect>')
            out.append(f'<text x="{bar + 8}" y="{y + 11}">{esc(sit.value_text(arm))}</text>')
        out.append("</svg>")
        return "".join(out)

    def html(self):
        legend = "".join(f'<span class="key"><i class="sw s{SLOT[a]}"></i><code>{esc(a)}</code></span>'
                         for a in self.arms)
        out = [f'<p class="legend">{legend}</p>', '<div class="table-wrap">', '<table class="situations">',
               '<thead><tr><th scope="col">Situation</th><th scope="col">Per arm</th>'
               '<th scope="col" class="num"><code>ormaos</code>&nbsp;−&nbsp;<code>none</code></th></tr></thead>', "<tbody>"]
        for sit in self.situations:
            out.append(f'<tr><td><a href="{esc(sit.url)}"><b>{esc(sit.name)}</b></a> '
                       f'<span class="bench">{esc(sit.bench)}</span><br><span class="line">{inline(sit.line)}</span>'
                       f'</td><td>{self.svg(sit)}</td><td class="num">{sit.change():+.2f}</td></tr>')
        out += ["</tbody>", "</table>", "</div>"]
        return "\n".join(out)

    def md(self):
        head = "| Situation | " + " | ".join(f"`{a}`" for a in self.arms) + " | `ormaos` − `none` |"
        lines = [head, "|---|" + "---:|" * (len(self.arms) + 1)]
        for sit in self.situations:
            cells = [sit.value_text(a) if a in sit.arms else "" for a in self.arms]
            lines.append(f"| [{sit.name}]({SITE}{sit.url}) ({sit.bench}): {to_markdown_inline(sit.line)} | "
                         + " | ".join(cells) + f" | {sit.change():+.2f} |")
        return "\n".join(lines)


def runs_note(sit):
    agents = sit.agents
    return ("Agent: " + code(agents[0]) + "." if len(agents) == 1 else
            "Agents: " + joined(code(a) for a in agents) + ".")


def knows2_situations(runs, h):
    out = []
    names = [n for n in h.tasks.NAMES if any(n in run.names for run in runs)]
    for name in names:
        records = [r for run in runs for r in run.of(name=name)]
        arms = [a for a in ARMS4 if any(r["arm"] == a for r in records)]
        sit = Situation("knows2", name, records, arms, f"/benchmarks/knows2/#{name}")
        run = next(run for run in runs if name in run.names)
        sit.run, sit.kind = run, KINDS[name]
        sit.line = sit.kind["line"]
        sit.questions, sit.oracle = run.questions(name), run.oracle(name)
        task = h.tasks.TASKS[name]
        says = h.benchlib.scenario(name).SAYS if task.get("job") else None
        sit.source = REPO / sit.kind["source"]
        sit.happened = HAPPENED[name](sit.oracle, says)
        for r in records:
            if r["arm"].startswith("ormaos"):
                r["_verbs"] = verbs_before_answers(read_steps(r["_run"].folder / r["stream"])[1])
        out.append(sit)
    return out


def fix_situations(runs, h):
    out = []
    first = runs[0]
    for name, job, differs in first.cases:
        records = [r for run in runs for r in run.of(case=name)]
        arms = [a for a in ARMS4 if any(r["arm"] == a for r in records)]
        sit = Situation("fix", name, records, arms, "/benchmarks/fix/")
        sit.run, sit.job, sit.differs = first, job, differs
        sit.line = f"a scheduled job that {job}; where it behaved otherwise than its README: {differs}"
        story = h.benchlib.scenario(name)
        built = first.built["bugs"][name]
        exit_code = re.match(r"r\d+ exit (\d+)", built["recording"]).group(1)
        sit.happened = [f"That night cron ran `{story.RUNS_WITH}`; it printed {code(story.SAYS)} and exited with "
                        f"code {exit_code}.", FIX_MORNING[name](built["wrong"]),
                        f"Where it behaved otherwise than its README: {differs}."]
        sit.story = story
        any_run = sit.of()[0]
        sit.symptom = (first.folder / any_run["folder"] / "TASK.md").read_text(encoding="utf-8").strip()
        source = getattr(story, "SOURCE", None)
        sit.source = Path(source) if source else BENCH / "bugs" / name / "task"
        sit.skip = tuple(h.benchlib.NOT_CODE) + tuple(getattr(story, "NOT_COPIED", ()))
        out.append(sit)
    return out


def code_at(commit, folder, skip):
    """The files of a folder of this repository at a commit, without the
    names in `skip`: path -> text."""
    names = git("ls-tree", "-r", "--name-only", commit, "--", rel(folder)).splitlines()
    out = {}
    for name in names:
        inside = name[len(rel(folder)) + 1:]
        if inside.split("/")[0] in skip:
            continue
        out[inside] = git_bytes(f"{commit}:{name}")
    return out


def git_bytes(spec):
    done = subprocess.run(["git", "-C", str(REPO), "show", spec], capture_output=True, check=False)
    if done.returncode:
        raise SystemExit(f"git show {spec}: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def code_left(folder, skip):
    """The committed files of a work folder, without the names in `skip`."""
    out = {}
    for name in git("ls-files", "--", rel(folder)).splitlines():
        inside = name[len(rel(folder)) + 1:]
        if inside.split("/")[0] in skip:
            continue
        out[inside] = (REPO / name).read_bytes()
    return out


def diff_of(sit, r):
    """The agent's change: a unified diff of the code it left against the
    code it was given (task/, at the commit that added the results)."""
    before = code_at(r["_run"].commit, sit.source, sit.skip)
    after = code_left(r["_run"].folder / r["folder"], sit.skip)
    out = []
    for name in sorted(set(before) | set(after)):
        a, b = before.get(name), after.get(name)
        if a == b:
            continue
        try:
            a_text = a.decode("utf-8").splitlines(keepends=True) if a is not None else []
            b_text = b.decode("utf-8").splitlines(keepends=True) if b is not None else []
        except UnicodeDecodeError:
            out.append(f"Binary file {name} changed\n")
            continue
        out += difflib.unified_diff(a_text, b_text, f"task/{name}" if a is not None else "/dev/null",
                                    name if b is not None else "/dev/null")
    return "".join(line if line.endswith("\n") else line + "\n" for line in out).rstrip("\n")


def column(sit, r):
    """What one run did, for its column."""
    cwd, steps = read_steps(r["_run"].folder / r["stream"])
    answers = r.get("answers") if isinstance(r.get("answers"), dict) else {}
    shown = []
    for step in steps:
        output = what = None
        if ormaos_calls(step.command) and step.output is not None:
            output, what = used_lines(step.output, answers if sit.bench == "knows2" else {})
            if sit.bench == "fix":
                rows = step.output.splitlines()
                output = rows[:15]
                what = f"all {_n(len(rows), 'line')}" if len(rows) <= 15 else f"the first 15 of {len(rows)} lines"
        shown.append((shown_command(step, cwd), output, what, stream_url(r, step.line)))
    tokens = r["_run"].h.base.bench_run.tokens_of(r)
    head = [f"Run {sit.run_label(r)}, [stream]({stream_url(r)})",
            f"{_n(r['tool_calls'], 'tool call')}, {tokens:,} tokens, {r['wall_seconds']:.0f} s"
            + (", out of time" if r.get("timed_out") else "")]
    end = []
    if sit.bench == "knows2":
        counts = {"right": 0, "null": 0, "wrong": 0}
        rows, nulls = [], []
        for q in sit.questions:
            kind, given = outcome_of(r, q["id"])
            counts[kind] += 1
            rows.append([q["id"], kind, "" if kind == "null" else code(dumped(given))])
            if kind == "null":
                nulls.append(q["id"])
        head.insert(1, f"Score {r['score']:.2f}: {counts['right']} right, {counts['null']} null, "
                       f"{counts['wrong']} wrong")
        end.append(("Its answers", Table(["Question", "Graded", "Answer"], rows, numbers=False, cls="plain mini")))
        if nulls:
            said = r["_run"].last_text(r) or ""
            parts = [x for x in re.split(r"\n\s*\n", said) if any(re.search(rf"\b{q}\b", x) for q in nulls)]
            end.append((f"Its own words on {joined(nulls)}: the paragraphs of its last message that name "
                        + ("them" if len(nulls) > 1 else "it") if parts else
                        f"Its own words on {joined(nulls)}: its last message",
                        Pre("", "\n\n".join(parts) if parts else said)))
    else:
        head.insert(1, "Passed the check" if r["fixed"] else "Did not pass the check")
        diff = diff_of(sit, r)
        end.append(("Its change, against `task/`", Pre("", diff or "no change")))
        end.append(("What the check said", Pre("", "\n".join(r["check"]))))
    return {"arm": r["arm"], "head": head, "steps": shown, "end": end}


def every_run_table(sit):
    many = len(sit.agents) > 1
    knows = sit.bench == "knows2"
    headers = (["Agent"] if many else []) + ["Arm", "Run"] + (
        ["Score", "Right", "Null", "Wrong", "`ormaos` verbs before answers.json"] if knows else ["Check", "Last line"]
    ) + ["Tool calls", "Tokens", "Wall time", "Stream"]
    rows = []
    for agent in sit.agents:
        for arm in sit.arms:
            for r in sit.of(arm, agent):
                tokens = r["_run"].h.base.bench_run.tokens_of(r)
                if knows:
                    kinds = [outcome_of(r, q["id"])[0] for q in sit.questions]
                    middle = [f"{r['score']:.2f}", str(kinds.count("right")), str(kinds.count("null")),
                              str(kinds.count("wrong")), ", ".join(r.get("_verbs", [])) or "–"]
                else:
                    middle = ["passed" if r["fixed"] else "did not pass", code(r["check"][-1])]
                rows.append(([code(agent)] if many else []) + [code(arm), sit.run_label(r)] + middle
                            + [str(r["tool_calls"]), f"{tokens:,}", f"{r['wall_seconds']:.0f} s",
                               f"[stream]({stream_url(r)})"])
    return Table(headers, rows, numbers=False, cls="plain runs")


def verbs_by_question(sit):
    """For each question, the verbs the runs that answered it had run before
    answers.json, with how many of those runs ran each, and how many runs
    got it right, per Ormaos arm."""
    arms = [a for a in sit.arms if a.startswith("ormaos")]
    rows = []
    for q in sit.questions:
        row = [q["id"]]
        for arm in arms:
            runs = sit.of(arm)
            answered = [r for r in runs if outcome_of(r, q["id"])[0] != "null"]
            count = {}
            for r in answered:
                for verb in r["_verbs"]:
                    count[verb] = count.get(verb, 0) + 1
            row.append(", ".join(f"{v} {n}" for v, n in sorted(count.items(), key=lambda x: (-x[1], VERBS.index(x[0])
                                                                                          if x[0] in VERBS else 99)))
                       or "–")
            row.append(f"{len(answered)}/{len(runs)}")
            row.append(f"{sum(1 for r in runs if r['right'][q['id']])}/{len(runs)}")
        rows.append(row)
    headers = ["Question"] + [h for a in arms for h in (f"`{a}`: verbs (runs)", "answered", "right")]
    return Table(headers, rows, numbers=False, cls="plain")


VERBS_RULE = ("Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its "
              "last write of `answers.json`. A question counts for a verb when a run that ran the verb answered "
              "it (not null); a run that ran several verbs counts under each of them.")


def case_page(sit, h):
    first = Section("top", f"{sit.name}, in {sit.bench}", [
        P((f"A {sit.kind['kind']}. {sit.kind['does']}" if sit.bench == "knows2" else
           f"A scheduled job. By its README, it {sit.job}.")
          + f" Source: [`{rel(sit.source)}`]({tree(sit.run.commit, sit.source)}).", "lead"),
        P(SENTENCE, "sentence"),
        P(("Mean score over every run: " if sit.bench == "knows2" else "Passed the check, first attempts: ")
          + ", ".join(f"`{a}` {sit.value_text(a)}" for a in sit.arms)
          + f" ({_n(len(sit.of(sit.arms[0])), 'run')} per arm). " + runs_note(sit)),
        Toc([("happened", "What happened"), ("given", "What the agent was given"),
             ("side-by-side", "Run 1 of each arm, side by side")]
            + ([("answered", "What Ormaos data answered")] if sit.bench == "knows2" else [])
            + [("runs", "Every run"), ("files", "The results files")]),
    ], kicker=f"Situation · {sit.bench}", first=True)
    happened = [P(" ".join(sit.happened))]
    if sit.bench == "knows2":
        happened.append(P("The numbers are the oracle's answers to the questions below: "
                          f"[`oracle/{sit.name}.json`]({blob(sit.run.commit, sit.run.folder / 'oracle' / (sit.name + '.json'))})."))
        given = [P(f"The folder the execution left, with what the arm adds, and {_n(len(sit.questions), 'question')} "
                   "in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers "
                   "were not in the folder."),
                 Table(["Question", "Asked", "Format", "The oracle's answer"],
                       [[q["id"], q["question"], q["format"], code(dumped(sit.oracle[q["id"]]))] for q in sit.questions],
                       numbers=False, cls="plain questions"),
                 Details(f"The prompt of each arm, verbatim", [Pre(f"`{a}`", h.prompt(sit.name, a)) for a in sit.arms])]
    else:
        happened.append(P("The items are those the scenario's own check of the data found, in "
                          f"[`build.json`]({blob(sit.run.commit, sit.run.folder / 'build.json')})."))
        happened.append(Pre("The symptom, from `TASK.md` in the agent's folder", sit.symptom))
        given = [P("Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm "
                   "adds) and the task text, the same in every arm but for the arm's last sentence:")]
        given += [Pre(f"`{a}`", h.benchlib.prompt(sit.name, a)) for a in sit.arms]
    sbs = [P("Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool "
             "calls in order" + ("; under each `ormaos` command, the lines of its output that hold a value the "
                                 "agent wrote in `answers.json`, or its first 15 lines, with a link to the full "
                                 "output in the stream." if sit.bench == "knows2" else
                                 "; under each `ormaos` command, the first 15 lines of its output, with a link "
                                 "to the full output in the stream."))]
    for agent in sit.agents:
        if len(sit.agents) > 1:
            sbs.append(H(3, code(agent)))
        sbs.append(SideBySide([column(sit, sit.first_run(a, agent)) for a in sit.arms]))
    sections = [first, Section("happened", "What happened", happened),
                Section("given", "What the agent was given", given),
                Section("side-by-side", "Run 1 of each arm, side by side", sbs)]
    if sit.bench == "knows2":
        sections.append(Section("answered", "What Ormaos data answered", [P(VERBS_RULE), verbs_by_question(sit)]))
    sections.append(Section("runs", "Every run", [
        P(("Every run of every arm" if sit.bench == "knows2" else "The first attempt of every run of every arm")
          + (", of every agent." if len(sit.agents) > 1 else ".")), every_run_table(sit)]))
    folders = sorted({r["_run"].folder for r in sit.records})
    sections.append(Section("files", "The results files", [UL(
        [f"The benchmark: [{sit.bench}]({sit.page_url})"]
        + [f"Results folder: [`{rel(f)}`]({tree(next(r['_run'].commit for r in sit.records if r['_run'].folder == f), f)})"
           for f in folders])]))
    return f"{sit.name}, in {sit.bench}", sections


def verb_table(sits):
    """Over every knows2 situation: per verb and Ormaos arm, the runs that
    ran it, the answers they gave after it, and how many were right."""
    arms = [a for a in ARMS4 if a.startswith("ormaos") and any(a in s.arms for s in sits)]
    stats = {}
    for sit in sits:
        for arm in arms:
            for r in sit.of(arm):
                for verb in r.get("_verbs", []):
                    s = stats.setdefault(verb, {a: [0, 0, 0] for a in arms})[arm]
                    s[0] += 1
                    for q in sit.questions:
                        kind = outcome_of(r, q["id"])[0]
                        s[1] += kind != "null"
                        s[2] += kind == "right"
    order = sorted(stats, key=lambda v: (-sum(stats[v][a][1] for a in arms), v))
    headers = ["Verb"] + [h for a in arms for h in (f"`{a}`: runs", "answered after it", "right")]
    rows = [[f"`{v}`"] + [str(x) for a in arms for x in stats[v][a]] for v in order]
    runs = {a: sum(len(s.of(a)) for s in sits) for a in arms}
    return Table(headers, rows), runs


# ---------------------------------------------------------------- index


def index_page(k2s, k1s, fixes, over, sits):
    k2, k1, fix = k2s[0], k1s[0], fixes[0]
    cpu, io = over.workloads[0], over.workloads[1]
    agents = sorted({r["_agent"] for runs in (k2s, k1s, fixes) for run in runs for r in run.records})

    # The headline: knows2's answers, ormaos against none
    o, n = k2.outcome_counts("ormaos"), k2.outcome_counts("none")
    headline = (f"In knows2, with an Ormaos recording (`ormaos`) the agent answered {o['right']} of "
                f"{sum(o.values())} questions right, over its {len(k2.of('ormaos'))} runs; with only the folder "
                f"(`none`), {n['right']} of {sum(n.values())}. Null answers: {o['null']} and {n['null']}. "
                f"Wrong answers: {o['wrong']} and {n['wrong']}.")
    from_run = (f"From the knows2 results folder of {k2.date}, agent " + joined(code(a) for a in k2.agents) + ".")

    def short(title):
        return title.split(": ", 1)[1][:1].upper() + title.split(": ", 1)[1][1:]

    cards = [
        (f"knows2 · {k2.date} · {joined(k2.models)} · N = {len(k2.records)} runs, "
         f"{len(k2.of(k2.arms[0]))} per arm",
         "What an agent knows about an execution",
         [P(f"{len(k2.names)} executions, questions by a model that was not told what Ormaos records, graded "
            "against an oracle. Mean score per arm, from 0 to 1."),
          score_chart("c-knows2", k2, "knows2", width=500, compact=True, left=110, right=160)],
         "The method, every question and every answer", "/benchmarks/knows2/"),
        (f"knows · {k1.date} · {joined(k1.models)} · N = {len(k1.records)} runs, {len(k1.of(k1.arms[0]))} per arm",
         "The earlier run, questions by the makers of Ormaos",
         [P("The same executions, with questions written by the people who make Ormaos; replaced by knows2. "
            "Mean score per arm."),
          score_chart("c-knows", k1, "knows", width=500, compact=True, left=110, right=160)],
         "The run, and why knows2 replaced it", "/benchmarks/knows/"),
        (f"fix · {fix.date} · {joined(fix.models)} · N = {len(fix.first)} runs, {len(fix.of(fix.arms[0]))} per arm",
         short(fix_title(fix)),
         [P("A coding agent changes a program that behaved otherwise than its README on one night; "
            "a check it does not see runs that night again. The metric `fixed`, per arm."),
          fixed_chart("c-fix", fix, width=500, compact=True, left=110, right=160)],
         "The programs, the check and every run", "/benchmarks/fix/"),
        (f"overhead · {over.facts['When'].split(' ')[0]} · N = {over.runs} runs per row",
         "What recording adds to the time of a run",
         [P("The median time of a recorded run, as a multiple of the same run without Ormaos, per capability "
            "set and workload, on a log scale."),
          ratio_chart("c-overhead", over, width=500, left=250)],
         "Every capability set, and the machine", "/benchmarks/overhead/"),
    ]
    # Where Ormaos changed the result: every situation, by ormaos minus none
    ranked = sorted(sits, key=lambda x: (-x.change(), x.bench, x.name))
    k2_sits = [x for x in sits if x.bench == "knows2"]
    fix_sits = [x for x in sits if x.bench == "fix"]
    changed = [x for x in sits if x.change()]
    verbs, verb_runs = verb_table(k2_sits)

    # Not measured yet
    claude_models = {r["model"] for runs in (k2s, k1s, fixes) for run in runs for r in run.records
                     if r["_agent"].startswith("claude-code")}
    others = [x for x in ("Codex", "Gemini", "Grok") if not any(x.lower() in a.lower() for a in agents)]
    if len(claude_models) < 2:
        others.append("other Claude models")
    loc = [b["lines_of_code"] for run in fixes for b in run.built["bugs"].values()]
    none_fixed = sum(run.fixed("none") for run in fixes)
    none_runs = sum(len(run.of("none")) for run in fixes)
    public = committed_on(k2.commit)

    full = len(k2.full_marks())
    sections = [
        Section("top", "Benchmarks", [
            P("What Ormaos does, measured. Every number on these pages is read from a results file by a script, "
              "never typed by hand.", "lead"),
            P(SENTENCE, "sentence"),
            P(headline, "headline"),
            Pair([score_chart("o-score", k2, "knows2", width=540, compact=True, left=110, right=170),
                  rnw_chart("o-rnw", k2, width=540, left=110, right=120)]),
            P(from_run, "caption"),
        ], first=True),
        Section("situations", "Where Ormaos changed the result and where it did not", [
            P(f"All {len(sits)} situations: the {len(k2_sits)} executions of knows2, with the mean score of their "
              f"runs (0 to 1), and the {len(fix_sits)} programs of fix, with the first attempts that passed the "
              "check. Sorted by the mean of `ormaos` minus the mean of `none`, over every run of every agent; "
              f"in {len(changed)} of them the two differ. Each name links to the situation's page: what "
              "happened, what the agent was given, and run 1 of each arm side by side."),
            Bars(ranked, ARMS4),
        ]),
        Section("answered", "What Ormaos data answered", [
            P(VERBS_RULE + " Over the " + joined(f"{verb_runs[a]} runs of `{a}`" for a in verb_runs)
              + " in knows2; each situation's page has it per question."),
            verbs,
        ]),
        Section("benchmarks", "The benchmarks", [Cards(cards, grid=True)]),
        Section("not-measured", "Not measured yet", [UL([
            "Other agents and models: " + joined(others) + ". Every run on these pages is "
            + joined(code(a) for a in agents) + ".",
            "RL environments: knows2 has one small grid world (`rl-env`), as a program an agent asks about; no "
            "environment in which an agent is trained.",
            f"Large codebases: the programs of fix have {min(loc)} to {max(loc)} lines of code.",
            f"Harder repairs, where the agent alone fails: in fix, `none` passed the check in {none_fixed} of "
            f"{none_runs} first attempts.",
        ])]),
        Section("not-shown", "What these benchmarks do not show", [UL([
            "The programs and their executions were written for these benchmarks by the people who make Ormaos; "
            "they are not a sample of real programs.",
            f"One prompt per arm, one tracer with its default settings, and few runs: "
            f"{len(k2.of(k2.arms[0]))} per arm in knows2, {len(fix.of(fix.arms[0]))} in fix. Several 95% "
            "intervals overlap; each page says which.",
            f"In knows2 the question writer and the agents are the same model, and in {full} of "
            f"{len(k2.names)} tasks every arm scored 1.00.",
            f"The overhead was timed on {len(over.workloads)} workloads on one machine; another program has "
            "another cost.",
            "Whether what happened is what should have happened: the benchmarks ask what happened, and the "
            "reader decides.",
            f"The knows2 questions and the oracle's answers are public since {public}, the day they were "
            "committed: a later run must not let the agent reach the network, other than the model's API.",
        ])]),
        Section("files", "The pages as files", [UL([
            "Each page is also Markdown, at its address with `.md` in place of the last slash: "
            "[`/benchmarks.md`](/benchmarks.md), [`/benchmarks/knows2.md`](/benchmarks/knows2.md), "
            f"[`/benchmarks/{ranked[0].path.rstrip('/')}.md`]({md_url(ranked[0].path)}), and so on.",
            "[`/benchmarks/llms.txt`](/benchmarks/llms.txt) lists them for agents.",
            f"The pages are written by [`site/benchmarks/build.py`]({EXAMPLES}/blob/main/site/benchmarks/build.py) "
            "from the results files.",
        ])]),
    ]
    return "Benchmarks", sections


def other_folders(runs, bench):
    """When a benchmark has more than one results folder: the others, for
    the end of its page."""
    if len(runs) < 2:
        return []
    rows = []
    for run in runs[1:]:
        if bench == "fix":
            per_arm = ", ".join(f"`{a}` {run.fixed(a)}/{len(run.of(a))}" for a in run.arms)
            count = len(run.first)
        else:
            per_arm = ", ".join(f"`{a}` {run.mean(a):.2f}" for a in run.arms)
            count = len(run.records)
        rows.append([f"[`{rel(run.folder)}`]({tree(run.commit, run.folder)})", joined(code(a) for a in run.agents),
                     run.date, str(count), per_arm])
    return [Section("other-folders", "Other results folders", [
        P(f"This page describes the first results folder of {bench}, `{rel(runs[0].folder)}`. These are the "
          "others; every one counts on the situation pages and the overview."),
        Table(["Results folder", "Agent", "Date", "Runs", "Per arm"], rows, numbers=False),
    ])]


# ---------------------------------------------------------------- llms.txt


def llms_txt(pages):
    lines = ["# Ormaos benchmarks", "",
             f"> {SENTENCE} These pages measure what a coding agent knows about an execution and whether the "
             "code it changes passes a check, with nothing, a raw trace or an Ormaos recording, and what recording costs in time. Every number is "
             "read from a results file by site/benchmarks/build.py in ormaos-examples.", "",
             "Each page is plain Markdown at the address below; the HTML page is the same address with a slash "
             "in place of `.md`.", "", "## Pages", ""]
    for path, title, description, _ in pages:
        if not path.startswith("cases/"):
            lines.append(f"- [{title}]({SITE}{md_url(path)}): {description}")
    lines += ["", "## Situations", "", "One page per situation: what happened, what the agent was given, run 1 of "
              "each arm side by side, and every run.", ""]
    for path, title, _, _ in pages:
        if path.startswith("cases/"):
            lines.append(f"- [{title}]({SITE}{md_url(path)})")
    lines += ["", "## Results files", ""]
    for path, title, _, files in pages:
        for name, url in files:
            lines.append(f"- [{path.strip('/')} {name}]({url})")
    lines += ["", "## Optional", "",
              f"- [Demo]({SITE}/demo/): the demo page of Ormaos",
              f"- [ormaos-examples]({EXAMPLES}): the programs, the benchmarks and these pages",
              f"- [ormaos-python]({ORMAOS}): the recorder and the command line", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- build


def build(root):
    """Write root/benchmarks/ and root/benchmarks.md."""
    out = root / "benchmarks"
    h = runners()
    frame = Frame()
    k2s = [KnowsRun(folder, ARMS4, h) for folder in results_folders(KNOWS2)]
    k1s = [KnowsRun(folder, ARMS4, h) for folder in results_folders(KNOWS)]
    fixes = [FixRun(folder, h) for folder in results_folders(FIX)]
    k2, k1, fix = k2s[0], k1s[0], fixes[0]
    over = Overhead()
    sits = knows2_situations(k2s, h) + fix_situations(fixes, h)

    def result_files(run):
        return [("results.jsonl", blob(run.commit, run.folder / "results.jsonl")),
                ("streams", tree(run.commit, run.folder / "streams")),
                ("report.md", blob(run.commit, run.folder / "report.md"))]

    pages = []
    title, sections = index_page(k2s, k1s, fixes, over, sits)
    pages.append(("", title, "where Ormaos changed the result and where it did not, situation by situation, "
                  "what Ormaos data answered, one card per benchmark, and what is not measured yet", sections, []))
    title, sections = knows2_page(k2, h, frame)
    sections[-1:-1] = other_folders(k2s, "knows2")
    pages.append(("knows2/", title, "the method, the charts, every question with the oracle's answer and every "
                  "run's answer, and what the agents said when they could not answer", sections, result_files(k2)))
    title, sections = knows_page(k1, k2)
    sections[-1:-1] = other_folders(k1s, "knows")
    pages.append(("knows/", title, "the earlier run of the same executions, and why knows2 replaced it", sections,
                  result_files(k1)))
    title, sections = fix_page(fix)
    sections[-1:-1] = other_folders(fixes, "fix")
    pages.append(("fix/", title, f"{len(fix.cases)} programs, {len(fix.arms)} arms, the metric fixed, scored by the "
                  "first attempt of every slot", sections,
                  result_files(fix)))
    title, sections = overhead_page(over)
    pages.append(("overhead/", title, f"the time a recorded run takes, per capability set, on {len(over.workloads)} workloads",
                  sections, [("RESULTS.md", f"{ORMAOS}/blob/{over.source['commit']}/{over.source['path']}")]))
    for sit in sits:
        title, sections = case_page(sit, h)
        pages.append((sit.path, title, "what happened, what the agent was given, run 1 of each arm side by side, "
                      "and every run", sections, []))

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for path, title, description, sections, _ in pages:
        folder = out / path
        folder.mkdir(parents=True, exist_ok=True)
        page_title = f"{title} · Ormaos benchmarks" if path else "Ormaos benchmarks"
        (folder / "index.html").write_text(
            frame.page(path, page_title, f"{title}: {description}.", sections, current=not path), encoding="utf-8")
        (root / md_url(path).lstrip("/")).write_text(Frame.markdown(sections), encoding="utf-8")
    (out / "llms.txt").write_text(llms_txt([(p, t, d, f) for p, t, d, _, f in pages]), encoding="utf-8")
    (out / "style.css").write_text(frame.style + EXTRA_CSS, encoding="utf-8")
    shutil.copyfile(DOCS / "favicon.svg", out / "favicon.svg")


def take_overhead(checkout):
    """Copy bench/RESULTS.md of an ormaos-python checkout, with the commit
    that last changed it."""
    checkout = Path(checkout).resolve()
    path = "bench/RESULTS.md"
    run = lambda *a: subprocess.run(["git", "-C", str(checkout), *a], capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    if run("status", "--porcelain", "--", path):
        raise SystemExit(f"{checkout / path} has changes that are not committed")
    commit = run("log", "-1", "--format=%H", "--", path)
    OVERHEAD.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checkout / path, OVERHEAD / "RESULTS.md")
    (OVERHEAD / "source.json").write_text(json.dumps(
        {"repository": "ormaos/ormaos-python", "path": path, "commit": commit}, indent=2) + "\n", encoding="utf-8")


def differences(a, b):
    out = []
    files_a = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    files_b = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    for name in sorted(files_a | files_b):
        if name not in files_a or name not in files_b or not filecmp.cmp(a / name, b / name, shallow=False):
            out.append(str(name))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if docs/benchmarks/ is not a fresh build")
    parser.add_argument("--overhead", metavar="ORMAOS_PYTHON",
                        help="first copy bench/RESULTS.md of this ormaos-python checkout")
    args = parser.parse_args(argv)
    if args.overhead:
        take_overhead(args.overhead)
    if not args.check:
        build(DOCS)
        print(f"wrote {rel(OUT)}/ and {rel(DOCS / 'benchmarks.md')}")
        return 0
    with tempfile.TemporaryDirectory() as scratch:
        fresh = Path(scratch)
        build(fresh)
        changed = ["benchmarks/" + n for n in differences(fresh / "benchmarks", OUT)] if OUT.exists() \
            else ["benchmarks/"]
        if not (DOCS / "benchmarks.md").exists() or not filecmp.cmp(fresh / "benchmarks.md", DOCS / "benchmarks.md",
                                                                   shallow=False):
            changed.append("benchmarks.md")
    for name in changed:
        print(f"docs/{name}: not as a fresh build writes it")
    if changed:
        print("run: python3 site/benchmarks/build.py")
        return 1
    print("docs/benchmarks/ is a fresh build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
