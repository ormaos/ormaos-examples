"""Record the billing tool before and after a change, and compute what
happened in each of the two executions.

    python scenario.py /tmp/agent-change

The folder becomes a git repository with two commits: the tool as it is in
this folder, then `change.patch`, a change a coding agent made when asked
for "10% off for gold customers and 5% for silver ones on invoices".
`python run.py` is recorded at each commit: `r1` before the change, `r2`
after it. Both print the same line.

Then the two versions run again in other copies, without Ormaos, under
`sys.settrace`; the answers in `questions.json` come from the calls seen
there, from a wrapper around `open`, and from `git rev-parse`.

Needs, in the Python that runs it: ormaos. Needs git.
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "billing.py", "run.py", "orders.json", "returns.json", "tiers.json"]
MESSAGE = "Give gold and silver customers their discount on invoices"
SHOW = ["ormaos", "diff", "r1", "r2"]
GIT = ["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com"]


def commit(folder, message):
    common.run(folder, *GIT, "add", "-A")
    common.run(folder, *GIT, "commit", "-q", "-m", message)
    return common.run(folder, "git", "rev-parse", "HEAD").stdout.strip()


def change(folder):
    shutil.copy2(HERE / "change.patch", folder.parent / "change.patch")
    common.run(folder, "git", "apply", folder.parent / "change.patch")


def repository(folder):
    common.run(folder, "git", "init", "-q", "-b", "main", ".")
    (folder / ".gitignore").write_text(".ormaos/\n__pycache__/\ninvoices.csv\nrefunds.csv\n")
    return commit(folder, "Add the billing tool")


def below_which(found, call):
    for name in ("refund_amount", "invoice_total"):
        if common.below(found, call, name):
            return name
    return None


def main():
    args = common.arguments(__doc__)
    if shutil.which("git") is None:
        sys.exit("git is not installed")
    target = args.target
    common.copy_program(HERE, target, FILES)
    commits = [repository(target)]
    common.record(target, "python", "run.py")
    change(target)
    commits.append(commit(target, MESSAGE))
    common.record(target, "python", "run.py")

    before = common.trace(HERE, FILES, "run.py")
    after = common.trace(HERE, FILES, "run.py", before=lambda folder: (repository(folder), change(folder)))
    names = lambda found: {c["fn"] for c in found["calls"]}  # noqa: E731
    count = lambda found, name: len(common.calls(found, name))  # noqa: E731
    discounts = {"invoice_total": 0, "refund_amount": 0}
    for call in common.calls(after, "discount_percent"):
        discounts[below_which(after, call)] += 1
    reads = lambda found: sum(  # noqa: E731
        1 for o in found["opens"] if o["path"] == "tiers.json" and "w" not in o["mode"]
    )
    written = lambda found: sorted({o["path"] for o in found["opens"] if "w" in o["mode"]})  # noqa: E731

    questions = [
        {
            "id": "q1",
            "question": "How many times did discount_percent run before the change (r1) and after it (r2)?",
            "answer": {"r1": count(before, "discount_percent"), "r2": count(after, "discount_percent")},
            "oracle": "sys.settrace, one pass per commit",
        },
        {
            "id": "q2",
            "question": "After the change (r2), how many calls of discount_percent were made below invoice_total and how many below refund_amount?",
            "answer": discounts,
            "oracle": "sys.settrace, the chain of calls above each call",
        },
        {
            "id": "q3",
            "question": "How many times did line_price run in r1 and in r2?",
            "answer": {"r1": count(before, "line_price"), "r2": count(after, "line_price")},
            "oracle": "sys.settrace, one pass per commit",
        },
        {
            "id": "q4",
            "question": "Which functions ran in r2 and did not run in r1?",
            "answer": sorted(names(after) - names(before)),
            "oracle": "sys.settrace, one pass per commit",
        },
        {
            "id": "q5",
            "question": "How many times was tiers.json opened for reading in r1 and in r2?",
            "answer": {"r1": reads(before), "r2": reads(after)},
            "oracle": "a wrapper around builtins.open",
        },
        {
            "id": "q6",
            "question": "Which files did each execution open for writing?",
            "answer": {"r1": written(before), "r2": written(after)},
            "oracle": "a wrapper around builtins.open",
        },
        {
            "id": "q7",
            "question": "Did r1 and r2 run the same git commit?",
            "answer": commits[0] == commits[1],
            "oracle": "git rev-parse HEAD before each recorded run",
        },
        {
            "id": "q8",
            "question": "Did the two executions print the same output?",
            "answer": before["stdout"] == after["stdout"],
            "oracle": "the standard output of the two passes",
        },
    ]
    common.finish(args, HERE, "agent-change", ["r1", "r2"], questions, SHOW)


if __name__ == "__main__":
    main()
