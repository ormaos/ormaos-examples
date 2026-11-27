"""The benchmark ``../../knows2`` for the harness: its tasks, its arms, its
task texts, the folders it built, and its grading. Nothing here is new: the
texts are those of knows2's runner, the answers those of its oracle, the
rules those of its ``rules.json``.
"""

import importlib.util
import json
import sys
from functools import cache
from pathlib import Path

NAME = "knows2"
FOLDER = Path(__file__).resolve().parents[2] / "knows2"
BUILD = FOLDER / ".build"


@cache
def runner():
    """knows2's ``run.py``, loaded as a module: it brings the task texts
    (``tasks.prompt``), the rules (``grade``) and the names."""
    if str(FOLDER) not in sys.path:
        sys.path.insert(0, str(FOLDER))
    spec = importlib.util.spec_from_file_location("knows2_run", FOLDER / "run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["knows2_run"] = module
    spec.loader.exec_module(module)
    return module


def tasks():
    return list(runner().tasks.NAMES)


def arms():
    return list(runner().k2.ARMS)


def text(task, arm):
    """The task text: the same for every agent."""
    return runner().tasks.prompt(task, arm)


def mount(task):
    return f"/srv/{task}"


def manifest():
    path = BUILD / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {"tasks": {}}


def not_built(names):
    """Why the batch cannot start, or None."""
    built = manifest()["tasks"]
    for name in names:
        if name not in built or not (BUILD / "answers" / f"{name}.json").exists():
            return f"{name} is not built: run `python3 build.py {name}` in {FOLDER}"
    return None


def python():
    """The Python the tasks were built with, as "3.14"."""
    return ".".join(manifest().get("python", "Python ?").split()[-1].split(".")[:2])


def folder(task, arm):
    """The folder an agent gets, as build.py left it."""
    return BUILD / "folders" / task / arm


def mounts(task, arm):
    """What is mounted read-only into the folder: the arm's .venv."""
    venv = manifest()["tasks"][task]["venvs"][arm]
    return [(venv, f"{mount(task)}/.venv", "ro")] if venv else []


def oracle(task):
    return BUILD / "answers" / f"{task}.json"


def grade(task, work, oracle_file):
    """The grade of the folder a run left. It gets the folder and the task,
    and nothing about who ran."""
    run = runner()
    answers = run.grade.read_answers(Path(work) / "answers.json")
    score, right = run.grade.grade(task, answers, json.loads(Path(oracle_file).read_text(encoding="utf-8")))
    return {"score": score, "right": right, "answers": answers,
            "answers_file": "missing or not JSON" if answers is None else "read"}


def tidy(work):
    """After grading: the trace is the same file in every run of the arm."""
    for trace in Path(work).glob("result*.json"):
        trace.unlink()
