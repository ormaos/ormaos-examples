"""What writer.py, build.py and run.py of knows2 share: the modules of
``../knows`` they reuse, the four arms, and the copy of a program in which
an execution is played.

The tasks, the sandbox, the environments, the grader, the runner and the
report are those of ``../knows``; this file only points them at this folder
and adds what knows2 has more: the ``ormaos-values`` arm, the standard
output and error of the execution kept apart, and an oracle copy for every
task, not only for the two jobs.
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNOWS = HERE.parent / "knows"
BENCH = HERE.parent
sys.path[:0] = [str(KNOWS), str(BENCH)]

import benchlib  # noqa: E402
import grade  # noqa: E402  (knows/grade.py)
import tasks  # noqa: E402  (knows/tasks.py)

kb = benchlib.load(KNOWS / "build.py", "knows_build")

BUILD = HERE / ".build"
kb.BUILD = BUILD  # the environments of knows2 are its own
ARMS = ("none", "raw", "ormaos", "ormaos-values")
TASKS, NAMES = tasks.TASKS, tasks.NAMES
MODEL = "claude-opus-5-5"
TOOLS = "Bash,Read,Grep,Glob,Edit,Write"
VALUES_FRONT = (".venv/bin/ormaos", "run", "--values", "--", ".venv/bin/python")
ORACLE_TRACE = "oracle-trace.json"


class Stage(kb.Stage):
    """One copy of a program and the sandbox its execution runs in, for the
    arms of knows and two more: ``ormaos-values`` and ``oracle``."""

    def __init__(self, name, arm, folder, venv):
        super().__init__(name, "ormaos" if arm == "ormaos-values" else arm, folder, venv)
        self.arm = arm
        self.readonly += ((HERE, "/opt/knows2"),)
        self.outputs = []  # (stdout, stderr) of each run an arm keeps
        if arm == "ormaos-values":
            self.bad_run = VALUES_FRONT
        elif arm == "oracle":
            self.bad_run = (self.python, "/opt/knows2/tracer.py", "--trace", ORACLE_TRACE)

    def run(self, argv, env=None, bad=False, timeout=900, recorder=True):
        """`bad` marks the execution the arms keep; every other run is plain.
        `recorder=False`: the program records or traces itself (the notebook)."""
        front = self.bad_run if (bad and (recorder or self.arm in ("none", "raw"))) else (self.python,)
        done = subprocess.run([*self.command(env), *front, *argv],
                              capture_output=True, text=True, check=False, timeout=timeout)
        if bad:
            self.printed += done.stdout + done.stderr
            self.outputs.append((done.stdout, done.stderr))
        return done

    def execute(self, argv, label=None, recorder=True):
        done = super().execute(argv, label=label, recorder=recorder)
        trace = self.folder / ORACLE_TRACE
        if label and self.arm == "oracle":
            trace.rename(self.folder / f"oracle-trace-{label}.json")
        return done


def play_notebook(stage):
    """The cells record themselves, so the session is not put under `ormaos
    run`. With --values a cell that is not of the notebook first makes
    `ormaos.record()` mean `ormaos.record(values=True)`; with --trace one
    turns the tracer on in the kernel."""
    more = {"ormaos-values": ["--values"], "oracle": ["--trace", ORACLE_TRACE]}.get(stage.arm, [])
    stage.execute(["/opt/knows2/session.py", *more], recorder=False)


TASKS["notebook"]["play"] = play_notebook


def venvs(name):
    """The environments of knows, built here; a library already installed for
    knows is linked, not downloaded again."""
    theirs, mine = KNOWS / ".build" / "venvs" / name, BUILD / "venvs" / name
    if (theirs / "base.built").exists() and not (mine / "base.built").exists():
        shutil.rmtree(mine, ignore_errors=True)
        mine.mkdir(parents=True)
        kb.run(["cp", "-al", theirs / "base", mine / "base"])
        shutil.copy2(theirs / "base.built", mine / "base.built")
    envs = kb.venvs(name)
    return {**envs, "ormaos-values": envs["ormaos"]}


def played(name, arm, folder, envs):
    """A fresh copy of the program in `folder`, with the execution played in it."""
    tasks.copy_program(name, folder)
    stage = Stage(name, arm, folder, envs[arm])
    TASKS[name]["play"](stage)
    return stage
