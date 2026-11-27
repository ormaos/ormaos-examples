"""What the scenario.py of every use case shares.

A scenario does three things, in this order:

1. copies the program to a new folder and records one execution of it with
   Ormaos (``ormaos run``, or ``with ormaos.record():`` in a notebook);
2. runs the same program again, in a second copy, without Ormaos and under
   the tracer of this file (``sys.settrace``), and computes the answer of
   every question from that trace and from what the program itself counted;
3. writes ``questions.json``.

The answers never come from the Ormaos recording: step 2 does not read
``.ormaos/``. The programs are deterministic, so the two executions did the
same things.

The tracer part of this file runs alone::

    python common.py --trace out.json [--lines fn,fn] script.py [args...]

It writes, for the files of the current folder: every call (function, file,
line, the shape of each argument and of the result, the call it was made
from), every exception with the function that handled it, every SQL
statement a sqlite3 connection ran and every file opened, each with the
function of the program that caused it. Standard library only.
"""

import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWN = os.path.realpath(__file__)
SKIP = (".venv", ".ormaos", "__pycache__", ".git", ".ipynb_checkpoints")


# --------------------------------------------------------------------------
# The scenario side
# --------------------------------------------------------------------------


def arguments(doc):
    parser = argparse.ArgumentParser(
        description=doc, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", type=Path, help="a folder that does not exist yet")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when an answer is not the one in questions.json next to this script",
    )
    mode.add_argument(
        "--update",
        action="store_true",
        help="write questions.json and demo.txt next to this script",
    )
    args = parser.parse_args()
    args.target = args.target.resolve()
    if args.target.exists() and any(args.target.iterdir()):
        parser.error(f"{args.target} exists and is not empty")
    need("ormaos")
    return args


def need(*modules):
    """Stop with one line when the Python running the scenario lacks a library."""
    import importlib.util

    missing = [name for name in modules if importlib.util.find_spec(name) is None]
    if missing:
        sys.exit(
            f"this Python ({sys.executable}) has no {', '.join(missing)}: "
            "install ormaos and the requirements.txt of the use case into it"
        )


def copy_program(source, target, files):
    """Copy the files of the program, and nothing else, to `target`."""
    target.mkdir(parents=True, exist_ok=True)
    for name in files:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, target / name)


def environment():
    """The environment of every command: the folder of this Python first on
    PATH, so that `python` and `ormaos` are the ones of this environment."""
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env.pop("ORMAOS_DIR", None)
    env["PYTHONHASHSEED"] = "0"
    return env


def run(folder, *command, check=True, env=None):
    """Run a command in `folder`; give what it printed."""
    done = subprocess.run(
        [str(word) for word in command],
        cwd=folder,
        env=env or environment(),
        capture_output=True,
        text=True,
    )
    if check and done.returncode != 0:
        sys.exit(f"{' '.join(map(str, command))}: exit {done.returncode}\n{done.stderr}")
    return done


def record(folder, *command, options=()):
    """`ormaos run [options] -- command` in `folder`."""
    return run(folder, "ormaos", "run", *options, "--", *command)


def trace(source, files, script, *args, lines=(), before=None):
    """Run `script` in a fresh copy of the program, under the tracer, without
    Ormaos; give the trace. `before(folder)` prepares the copy first."""
    with tempfile.TemporaryDirectory(prefix="oracle-") as name:
        folder = Path(name).resolve() / "program"
        copy_program(source, folder, files)
        if before:
            before(folder)
        return trace_in(folder, script, *args, lines=lines)


def trace_in(folder, script, *args, lines=()):
    out = folder.parent / f"trace-{next(_numbers)}.json"
    command = [sys.executable, str(Path(__file__).resolve()), "--trace", out]
    if lines:
        command += ["--lines", ",".join(lines)]
    done = run(folder, *command, script, *args)
    found = json.loads(out.read_text())
    found["stdout"] = done.stdout
    return found


_numbers = itertools.count(1)


def address(folder, recording, function):
    """The address of the first call of `function`, as `ormaos tree` prints it."""
    out = run(folder, "ormaos", "tree", recording, "--function", function, "--limit", "1").stdout
    for line in out.splitlines():
        if line.startswith(f"{recording}:c"):
            return line.split()[0]
    sys.exit(f"no call of {function} in {recording}")


def calls(found, function):
    """The calls of one function, in order."""
    return [call for call in found["calls"] if call["fn"] == function]


def below(found, call, function):
    """True when `call` was made, directly or not, from a call of `function`."""
    by_id = {c["id"]: c for c in found["calls"]}
    parent = call["parent"]
    while parent is not None:
        if by_id[parent]["fn"] == function:
            return True
        parent = by_id[parent]["parent"]
    return False


def finish(args, here, use_case, recordings, questions, show):
    """Write questions.json in the target; with --update also next to the
    scenario, with what the command `show` printed (demo.txt); with --check
    compare the answers with the committed ones."""
    document = {
        "use_case": use_case,
        "recordings": recordings,
        "answers_from": (
            "an execution of the same program without Ormaos, under "
            "sys.settrace and the counters named in each question"
        ),
        "questions": questions,
    }
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    (args.target / "questions.json").write_text(text, encoding="utf-8")
    shown = run(args.target, *show, check=False)
    demo = "$ " + " ".join(show) + "\n" + shown.stdout + shown.stderr
    for item in questions:
        print(f"{item['id']}  {item['question']}\n    {json.dumps(item['answer'])}")
    print(f"\n{demo}")
    print(f"the program and its recording: {args.target}")
    committed = here / "questions.json"
    if args.update:
        committed.write_text(text, encoding="utf-8")
        (here / "demo.txt").write_text(demo, encoding="utf-8")
        print(f"written: {committed} and demo.txt")
    if args.check:
        old = json.loads(committed.read_text(encoding="utf-8"))["questions"]
        different = [
            new["id"]
            for new, was in itertools.zip_longest(questions, old, fillvalue={})
            if new.get("answer") != was.get("answer") or new.get("question") != was.get("question")
        ]
        if different:
            sys.exit(f"not the committed answer: {', '.join(different)}")
        print(f"{len(questions)} answers, the same as in {committed.name}")


# --------------------------------------------------------------------------
# The tracer side: runs in the process of the program
# --------------------------------------------------------------------------


class Tracer:
    def __init__(self, root, line_functions=(), is_program=None):
        self.root = str(root) + os.sep
        self.line_functions = set(line_functions)
        self.is_program = is_program or self._in_root
        self.calls = []
        self.exceptions = []
        self.sql = []
        self.opens = []
        self.ids = itertools.count(1)
        self.local = threading.local()
        self.files = {}

    def _in_root(self, filename):
        known = self.files.get(filename)
        if known is None:
            known = (
                filename.startswith(self.root)
                and os.path.realpath(filename) != OWN
                and not any(f"{os.sep}{part}{os.sep}" in filename for part in SKIP)
            )
            self.files[filename] = known
        return known

    def name(self, filename):
        return filename[len(self.root) :] if filename.startswith(self.root) else filename

    def state(self):
        local = self.local
        if not hasattr(local, "stack"):
            local.stack = []
            local.busy = False
            local.pending = {}
        return local

    # -- sys.settrace ------------------------------------------------------

    def global_trace(self, frame, event, arg):
        if event != "call" or not self.is_program(frame.f_code.co_filename):
            return None
        local = self.state()
        if local.busy:
            return None
        local.busy = True
        try:
            code = frame.f_code
            names = code.co_varnames[: code.co_argcount + code.co_kwonlyargcount]
            record = {
                "id": next(self.ids),
                "fn": code.co_qualname,
                "file": self.name(code.co_filename),
                "line": code.co_firstlineno,
                "parent": local.stack[-1]["id"] if local.stack else None,
                "args": {n: describe(frame.f_locals[n]) for n in names if n in frame.f_locals},
                "thread": threading.current_thread().name,
            }
            if code.co_name in self.line_functions:
                record["lines"] = []
            self.calls.append(record)
            local.stack.append(record)
        finally:
            local.busy = False
        return self.local_trace

    def local_trace(self, frame, event, arg):
        local = self.state()
        if local.busy:
            return self.local_trace
        local.busy = True
        try:
            record = local.stack[-1] if local.stack else None
            key = id(frame)
            if event == "line":
                if record is not None and "lines" in record:
                    record["lines"].append(frame.f_lineno)
                pending = local.pending.pop(key, None)
                if pending is not None:
                    pending["handled_in"] = frame.f_code.co_qualname
                    pending["handled_at_line"] = frame.f_lineno
            elif event == "exception":
                exc_type, exc, _ = arg
                seen = getattr(local, "seen", None)
                if seen is None:
                    seen = local.seen = {}
                item = seen.get(id(exc))
                if item is None or item["object"] is not exc:
                    item = {
                        "object": exc,
                        "record": {
                            "type": f"{exc_type.__module__}.{exc_type.__qualname__}",
                            "raised_in": frame.f_code.co_qualname,
                            "raised_at_line": frame.f_lineno,
                            "handled_in": None,
                            "handled_at_line": None,
                        },
                    }
                    seen[id(exc)] = item
                    self.exceptions.append(item["record"])
                local.pending[key] = item["record"]
            elif event == "return":
                local.pending.pop(key, None)
                if record is not None:
                    record["result"] = describe(arg)
                    local.stack.pop()
        finally:
            local.busy = False
        return self.local_trace

    # -- what the program did outside its own code -------------------------

    def caller(self):
        """The innermost function of the program on the stack of this thread."""
        frame = sys._getframe(2)
        while frame is not None:
            if self.is_program(frame.f_code.co_filename):
                return {
                    "fn": frame.f_code.co_qualname,
                    "file": self.name(frame.f_code.co_filename),
                    "line": frame.f_lineno,
                }
            frame = frame.f_back
        return {"fn": None, "file": None, "line": None}

    def install(self):
        import builtins
        import sqlite3

        tracer = self
        real_connect = sqlite3.connect
        real_open = builtins.open

        def connect(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            where = tracer.caller()
            tracer.sql.append({"sql": "(connect)", **where})

            def statement(text):
                tracer.sql.append({"sql": " ".join(text.split()), **tracer.caller()})

            connection.set_trace_callback(statement)
            return connection

        def opened(file, mode="r", *args, **kwargs):
            where = tracer.caller()
            if where["fn"] is not None and isinstance(file, (str, os.PathLike)):
                path = os.path.abspath(file)
                if tracer.is_program(path) or path.startswith(tracer.root):
                    tracer.opens.append({"path": tracer.name(path), "mode": mode, **where})
            return real_open(file, mode, *args, **kwargs)

        sqlite3.connect = connect
        builtins.open = opened
        threading.settrace(self.global_trace)
        sys.settrace(self.global_trace)

    def result(self):
        sys.settrace(None)
        threading.settrace(None)
        return {
            "calls": self.calls,
            "exceptions": self.exceptions,
            "sql": self.sql,
            "opens": self.opens,
        }


def kernel_tracer():
    """A tracer for a Jupyter kernel: the program is the code of the cells,
    which the kernel compiles under .../ipykernel_<pid>/<number>.py."""
    tracer = Tracer(Path.cwd().resolve(), is_program=_is_cell)
    tracer.install()
    return tracer


def _is_cell(filename):
    return "ipykernel_" in filename and "site-packages" not in filename


def describe(value):
    """The type of a value and what can be counted of it."""
    kind = type(value)
    module = kind.__module__ or ""
    if value is None or kind in (bool, int, str):
        return {"type": kind.__name__, "value": value}
    if kind is float:
        return {"type": "float", "value": value if value == value else "nan"}
    if kind in (list, tuple, set, frozenset, dict):
        return {"type": kind.__name__, "len": len(value)}
    if module.startswith("pandas") and kind.__name__ == "DataFrame":
        return {
            "type": "DataFrame",
            "rows": int(value.shape[0]),
            "columns": [str(c) for c in value.columns],
            "nulls": int(value.isna().sum().sum()),
        }
    if module.startswith("torch") and kind.__name__ in ("Tensor", "Parameter"):
        import torch

        return {
            "type": "Tensor",
            "shape": [int(n) for n in value.shape],
            "nan": int(torch.isnan(value).sum()) if value.is_floating_point() else 0,
        }
    return {"type": kind.__qualname__}


def trace_main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--lines", default="")
    parser.add_argument("script")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    import runpy

    root = Path.cwd().resolve()
    tracer = Tracer(root, [name for name in args.lines.split(",") if name])
    sys.argv = [args.script, *args.rest]
    sys.path.insert(0, str(root))
    tracer.install()
    code = 0
    try:
        runpy.run_path(str(root / args.script), run_name="__main__")
    except SystemExit as stop:
        code = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 1)
    finally:
        found = tracer.result()
        args.trace.write_text(json.dumps(found), encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(trace_main(sys.argv[1:]))
