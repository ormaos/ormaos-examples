"""Have the questions of every task written by a model that is told nothing
of Ormaos, of a recording or of a trace.

    python3 writer.py                  # every task
    python3 writer.py rl-env ai-app    # some tasks
    python3 writer.py --folders        # only make the folders, run no model

For a task the execution is played once, as it is, in a copy of the program
mounted at ``/srv/<task>``. The writer's folder then gets only the source
files of the program (``.py``, ``.ipynb``), its README, and what the
execution printed (``stdout.txt``, ``stderr.txt``): no input, no output
file, no ``.venv``, no ``.ormaos``, no trace. Three READMEs and the notebook
speak of Ormaos; ``without_mentions`` takes those words out, and the build
of a folder stops if "ormaos" is still in any file of it.

``claude -p`` then runs in that folder inside bubblewrap, with the flags an
agent of the benchmark gets, and writes ``questions.json``. Kept in
``writer/<task>/``, as they are:

- ``folder/``: what the writer was given;
- ``prompt.txt``: the prompt;
- ``transcript.jsonl``: everything the command line printed;
- ``questions.json``: the file the writer left, byte for byte.
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import k2
from k2 import HERE, TASKS, benchlib, tasks

WRITER = HERE / "writer"
SOURCE = (".py", ".ipynb")
ASK = (
    "Write 8 factual questions about what happened inside {this} that the output alone does not answer, "
    "each with one unambiguous answer and its expected format. Write them to questions.json in this "
    'folder: a JSON list of 8 objects, each with the keys "id" ("q1" to "q8"), "question" and "format".'
)
HOLDS = ("This folder holds only the program's source files, its README, and what that execution "
         "printed: stdout.txt and stderr.txt.")
# The two tasks whose sentence in knows names something the writer's folder does not have.
WHAT = {
    "agent-change": "`python3 run.py` ran once at the first of the two commits of this program (that "
                    "execution is r1) and once at the second (r2).",
}
HOLDS_OF = {
    "agent-change": "This folder holds only the program's source files at each commit (commit-1/ and "
                    "commit-2/), its README, and what each execution printed: r1.stdout.txt, "
                    "r1.stderr.txt, r2.stdout.txt and r2.stderr.txt.",
}


def prompt(name):
    what = WHAT.get(name, TASKS[name]["what"])
    this = "these executions" if TASKS[name].get("labels") else "this execution"
    return f"{what} {HOLDS_OF.get(name, HOLDS)} {ASK.format(this=this)}"


def without_mentions(name, folder):
    """Take out of the README and of the notebook what speaks of Ormaos."""
    readme = folder / "README.md"
    text = readme.read_text(encoding="utf-8")
    if name in ("order-sync", "freight-quote"):
        # The section "Recording a run with Ormaos", to the next section or the end.
        text = re.sub(r"\n## Recording a run with Ormaos\n.*?(?=\n## |\Z)", "\n", text, flags=re.S)
        text = text.rstrip("\n") + "\n"
    if name == "notebook":
        text = re.sub(r"Four of its cells run their step inside `with ormaos\.record\(\):`, so each step "
                      r"of a session is recorded as it runs\. ", "", text)
        text = text.replace("pip install git+https://github.com/ormaos/ormaos-python\n", "")
        book = folder / "report.ipynb"
        document = json.loads(book.read_text(encoding="utf-8"))
        for cell in document["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            source = source.replace("import ormaos\n\n", "")
            # `with ormaos.record():` and its block: the block, not indented.
            source = re.sub(r"^with ormaos\.record\(\):\n((?:    .*\n?)+)",
                            lambda m: re.sub(r"^    ", "", m.group(1), flags=re.M), source, flags=re.M)
            cell["source"] = source.splitlines(keepends=True)
        book.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    readme.write_text(text, encoding="utf-8")


def make_folder(name, target):
    """Play the execution and fill `target` with what the writer gets."""
    envs = k2.venvs(name)
    with tempfile.TemporaryDirectory(prefix=f"knows2-writer-{name}-") as scratch:
        stage = k2.played(name, "none", Path(scratch) / "none", envs)
        program = stage.folder
        target.mkdir(parents=True)
        shutil.copy2(program / "README.md", target / "README.md")
        sources = sorted(p.name for p in program.iterdir() if p.suffix in SOURCE)
        labels = TASKS[name].get("labels")
        if labels:  # agent-change: the source at each commit
            for n, commit in enumerate(("HEAD~1", "HEAD"), 1):
                (target / f"commit-{n}").mkdir()
                for file in sources:
                    shown = k2.kb.run(["git", "-C", program, "show", f"{commit}:{file}"]).stdout
                    (target / f"commit-{n}" / file).write_text(shown, encoding="utf-8")
        else:
            for file in sources:
                shutil.copy2(program / file, target / file)
        if len(stage.outputs) != len(labels or [1]):
            raise SystemExit(f"{name}: {len(stage.outputs)} executions were kept")
        for label, (out, err) in zip(labels or [None], stage.outputs):
            front = f"{label}." if label else ""
            (target / f"{front}stdout.txt").write_text(out, encoding="utf-8")
            (target / f"{front}stderr.txt").write_text(err, encoding="utf-8")
    without_mentions(name, target)
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        text = path.read_text(encoding="utf-8")
        if "ormaos" in text.lower() or "ormaos" in path.name.lower():
            raise SystemExit(f"{name}: {path.relative_to(target)} speaks of Ormaos")
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"record|trace", line, re.I):
                print(f"  {name}/{path.relative_to(target)}:{number}: {line.strip()[:120]}")


def write(name, args):
    home = WRITER / name
    work = home / "work"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(home / "folder", work)
    text = prompt(name)
    (home / "prompt.txt").write_text(text + "\n", encoding="utf-8")
    command = benchlib.sandbox(work, benchlib.mount_of(name), network=True, claude=True)
    command += [
        args.claude, "-p", "--model", k2.MODEL, "--safe-mode", "--strict-mcp-config",
        "--tools", k2.TOOLS, "--allowedTools", k2.TOOLS, "--no-session-persistence",
        "--output-format", "stream-json", "--verbose", text,
    ]
    with open(home / "transcript.jsonl", "w", encoding="utf-8") as output:
        writer = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        try:
            writer.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(writer.pid, signal.SIGKILL)
            writer.wait()
            print(f"{name}: out of time")
    left = work / "questions.json"
    wrote = left.exists()
    if wrote:
        shutil.copyfile(left, home / "questions.json")
    others = sorted(str(p.relative_to(work)) for p in work.rglob("*")
                    if p.is_file() and not (home / "folder" / p.relative_to(work)).exists())
    shutil.rmtree(work)
    print(f"{name}: questions.json {'written' if wrote else 'NOT written'}; "
          f"files the writer added: {', '.join(others) or 'none'}", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tasks", nargs="*")
    parser.add_argument("--folders", action="store_true", help="only make the folders")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args(argv)
    names = args.tasks or k2.NAMES
    k2.BUILD.mkdir(exist_ok=True)
    k2.kb.bench_build.build_tools()
    for name in names:
        if (WRITER / name / "questions.json").exists():
            parser.error(f"{name} already has questions: they are written once")
        shutil.rmtree(WRITER / name, ignore_errors=True)
        make_folder(name, WRITER / name / "folder")
        print(f"{name}: folder made: {', '.join(sorted(str(p.relative_to(WRITER / name / 'folder')) for p in (WRITER / name / 'folder').rglob('*') if p.is_file()))}", flush=True)
    if args.folders:
        return 0
    args.claude = os.path.realpath(shutil.which("claude") or parser.error("claude is not installed"))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda name: write(name, args), names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
