"""Build, for every task, the folder an agent gets in each of the three arms.

    python3 build.py                 # every task
    python3 build.py rl-env ai-app   # some tasks

For a task the same execution is played in separate copies of the program,
each mounted at ``/srv/<task>``: as it was (``none``), under VizTracer with
its default settings (``raw``: ``result.json``), under Ormaos (``ormaos``:
``.ormaos/``), and for the two jobs once more under the tracer of
``use-cases/common.py``, which gives the answers. The copies must leave the
same files. Then the input the execution read is taken out, and
``questions.json`` is put in, without the answers.

Everything goes to ``.build/`` (not committed): ``folders/<task>/<arm>/``,
``venvs/<task>/`` (mounted read-only at ``.venv`` of the folder),
``answers/<task>.json`` and ``manifest.json``.

Needs bubblewrap, the network (pip), git, and a checkout of ormaos-python
next to this repository.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import grade
import tasks
from tasks import BENCH, HERE, TASKS, USE_CASES, benchlib

sys.path.insert(0, str(BENCH))
import build as bench_build  # noqa: E402  (the wheels and VizTracer of agent-bench)

BUILD = HERE / ".build"
WHEELS = benchlib.TOOLS / "wheels"
ARMS = benchlib.ARMS
TRACE_ATTEMPTS = 40
NOT_COMPARED = (".venv", ".ormaos", ".git", "__pycache__")
STUB = '''"""Stands in for Ormaos where the notebook runs without it: record() does nothing."""
import contextlib


def record(*args, **kwargs):
    return contextlib.nullcontext()
'''


def run(command, **kwargs):
    done = subprocess.run([str(c) for c in command], capture_output=True, text=True, check=False, **kwargs)
    if done.returncode != 0:
        raise SystemExit(f"failed: {' '.join(map(str, command))}\n{done.stdout}{done.stderr}")
    return done


class Stage(benchlib.World):
    """One copy of a program, and the sandbox its execution runs in."""

    def __init__(self, name, arm, folder, venv):
        task = TASKS[name]
        self.arm, self.venv, self.printed = arm, venv, ""
        self.python = ".venv/bin/python" if (task["install"] or arm == "ormaos") else "python3"
        readonly = [(USE_CASES, "/opt/use-cases"), (HERE, "/opt/knows")]
        if arm == "raw":
            front = (".venv/bin/viztracer",) if task["install"] else (f"{benchlib.VIZTRACER}/bin/viztracer",)
            readonly.append((benchlib.TOOLS / "viztracer", benchlib.VIZTRACER))
        elif arm == "ormaos":
            front = (".venv/bin/ormaos", "run", "--", ".venv/bin/python")
        elif arm == "oracle":
            front = (self.python, "/opt/use-cases/common.py", "--trace", "oracle-trace.json")
        else:
            front = (self.python,)
        super().__init__(name, folder, bad_run=front, readonly=readonly)

    def command(self, env=None):
        env = {"PYTHONHASHSEED": "0", **(env or {})}
        argv = benchlib.sandbox(self.folder, self.mount, readonly=self.readonly, env=env)
        if self.venv:
            argv += ["--ro-bind", str(self.venv), f"{self.mount}/.venv",
                     "--setenv", "PATH", f"{self.mount}/.venv/bin:/usr/local/bin:/usr/bin:/bin"]
        return argv

    def run(self, argv, env=None, bad=False, timeout=900, recorder=True):
        """`bad` marks the execution the arms keep; every other run is plain."""
        front = self.bad_run if (bad and (recorder or self.arm != "ormaos")) else (self.python,)
        done = subprocess.run([*self.command(env), *front, *argv],
                              capture_output=True, text=True, check=False, timeout=timeout)
        if bad:
            self.printed += done.stdout + done.stderr
        return done

    def execute(self, argv, label=None, recorder=True):
        done = self.run(argv, bad=True, recorder=recorder)
        if done.returncode != 0:
            raise SystemExit(f"{self.name}/{self.arm}: {' '.join(argv)}: exit {done.returncode}\n"
                             f"{done.stdout}{done.stderr}")
        if label and self.arm == "raw":
            (self.folder / "result.json").rename(self.folder / f"result-{label}.json")
        return done

    def sh(self, argv):
        return run([*self.command(), *argv])


def venvs(name):
    """The environments of a task, built at the path they are mounted at.
    {arm: folder or None}; the oracle of a job uses the plain one."""
    task = TASKS[name]
    root = BUILD / "venvs" / name
    mount = f"/srv/{name}/.venv"
    readonly = [(WHEELS, "/wheels"), (USE_CASES, "/opt/use-cases")]

    def inside(folder, command, network=False):
        return run([*benchlib.sandbox(folder, mount, readonly=readonly, network=network), *command])

    def site(folder):
        return next((folder / "lib").glob("python*/site-packages"))

    base = None
    if task["install"]:
        base = root / "base"
        if not (root / "base.built").exists():
            shutil.rmtree(base, ignore_errors=True)
            base.mkdir(parents=True)
            inside(base, ["python3", "-m", "venv", "."])
            inside(base, ["bin/pip", "install", "--quiet", *task["install"]], network=True)
            (root / "base.built").write_text(datetime.now().isoformat(timespec="seconds") + "\n")
        (site(base) / "ormaos.py").unlink(missing_ok=True)

    orm = root / "orm"
    shutil.rmtree(orm, ignore_errors=True)
    wheel = next(WHEELS.glob("ormaos-*.whl"))
    if base:
        run(["cp", "-al", base, orm])  # hard links: only what pip adds is new
        inside(orm, ["bin/pip", "install", "--quiet", "--no-index", f"/wheels/{wheel.name}"])
    else:
        orm.mkdir(parents=True)
        inside(orm, ["python3", "-m", "venv", "."])
        inside(orm, ["bin/pip", "install", "--quiet", "--no-index", f"/wheels/{wheel.name}"])
        inside(orm, ["bin/python", "-m", "pip", "uninstall", "--quiet", "-y", "pip"])

    viz = None
    if base:
        if name == "notebook":
            # The cells import ormaos; where Ormaos is not, record() does nothing.
            (site(base) / "ormaos.py").write_text(STUB, encoding="utf-8")
        viz = root / "viz"
        shutil.rmtree(viz, ignore_errors=True)
        run(["cp", "-al", base, viz])
        others = [f"/wheels/{w.name}" for w in WHEELS.glob("*.whl") if not w.name.startswith("ormaos")]
        inside(viz, ["bin/pip", "install", "--quiet", "--no-index", *others])
    return {"none": base, "raw": viz, "ormaos": orm, "oracle": base}


def traces_of(folder):
    return sorted(folder.glob("result*.json"))


def trace_is_whole(stage):
    """Every trace loads and has calls of this folder; VizTracer left no process out."""
    found = traces_of(stage.folder)
    if "invalid json" in stage.printed or not found:
        return False
    for path in found:
        try:
            events = json.loads(path.read_text(encoding="utf-8"))["traceEvents"]
        except (OSError, ValueError, KeyError):
            return False
        if not any(f"({stage.mount}/" in str(event.get("name", "")) for event in events):
            return False
    return True


def left(name, stage):
    """What the execution left, for comparing the copies."""
    if TASKS[name].get("job"):
        return stage.story.data_left(stage.folder)
    files = {}
    for path in sorted(stage.folder.rglob("*")):
        relative = path.relative_to(stage.folder)
        if (not path.is_file() or relative.parts[0] in NOT_COMPARED or path in traces_of(stage.folder)
                or path.name == "oracle-trace.json"):
            continue
        # A database or a checkpoint holds the same rows or weights in bytes that differ.
        binary = path.suffix in (".db", ".pt")
        files[str(relative)] = "binary" if binary else hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def check_committed(name, envs, scratch):
    """The answers committed in use-cases/ are the answers in this environment."""
    folder = scratch / "check"
    folder.mkdir()
    stage = Stage(name, "ormaos", folder, envs["ormaos"])
    stage.sh([".venv/bin/python", f"/opt/use-cases/{name}/scenario.py", "/tmp/check", "--check"])


def build_task(name, scratch):
    task = TASKS[name]
    envs = venvs(name)
    arms = [*ARMS, "oracle"] if task.get("job") else list(ARMS)
    stages, attempts = {}, 0
    for arm in arms:
        folder = scratch / arm
        while True:
            tasks.copy_program(name, folder)
            stages[arm] = Stage(name, arm, folder, envs[arm])
            task["play"](stages[arm])
            if arm != "raw":
                break
            # VizTracer sometimes writes a duration that is not a number and then
            # leaves that process out of the file: play the execution again.
            attempts += 1
            if trace_is_whole(stages[arm]):
                break
            if attempts == TRACE_ATTEMPTS:
                raise SystemExit(f"{name}: no whole trace in {TRACE_ATTEMPTS} attempts")
            shutil.rmtree(folder)
    same = left(name, stages["none"])
    for arm in arms[1:]:
        if left(name, stages[arm]) != same:
            raise SystemExit(f"{name}: the {arm} copy did not leave what the plain one left")

    if task.get("job"):
        found = json.loads((stages["oracle"].folder / "oracle-trace.json").read_text(encoding="utf-8"))
        questions = task["questions"](found)
    else:
        check_committed(name, envs, scratch)
        questions = tasks.committed_questions(name)
    rules = grade.RULES[name]
    if [q[0] for q in questions] != list(rules):
        raise SystemExit(f"{name}: rules.json does not have the ids of the questions")
    oracle = {qid: answer for qid, _, answer in questions}
    shown = {"questions": [{"id": qid, "question": text, "format": grade.say(rules[qid])}
                           for qid, text, _ in questions]}
    if grade.grade(name, oracle, oracle)[0] != 1.0 or grade.grade(name, {}, oracle)[0] != 0.0:
        raise SystemExit(f"{name}: the oracle's answers do not grade 1.0, or an empty file not 0")

    out = BUILD / "folders" / name
    shutil.rmtree(out, ignore_errors=True)
    facts = {"questions": len(questions), "removed": task["removed"], "trace_attempts": attempts}
    for arm in ARMS:
        folder = stages[arm].folder
        for cache in folder.rglob("__pycache__"):
            shutil.rmtree(cache)
        for file in task["removed"]:
            (folder / file).unlink()
        (folder / "questions.json").write_text(json.dumps(shown, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(folder, out / arm, symlinks=True)
    facts["files"] = sorted(p.name for p in (out / "none").iterdir())
    facts["trace_bytes"] = sum(p.stat().st_size for p in traces_of(out / "raw"))
    listed = Stage(name, "ormaos", out / "ormaos", envs["ormaos"]).sh([".venv/bin/ormaos", "list"]).stdout
    facts["recordings"] = listed.splitlines()[0]
    expected = len(task.get("labels", [])) or (4 if name == "notebook" else 1)
    if not listed.startswith(f"{expected} recording"):
        raise SystemExit(f"{name}: expected {expected} recordings:\n{listed}")
    (BUILD / "answers").mkdir(exist_ok=True)
    (BUILD / "answers" / f"{name}.json").write_text(json.dumps(oracle, indent=2) + "\n", encoding="utf-8")
    # What an agent gets at .venv: the program's environment, and in the ormaos
    # arm the one that also has the ormaos command line. VizTracer is in neither.
    agents = {"none": envs["none"], "raw": envs["none"], "ormaos": envs["ormaos"]}
    return facts, {arm: (str(agents[arm]) if agents[arm] else None) for arm in ARMS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tasks", nargs="*", help="the tasks to build (default: all)")
    args = parser.parse_args(argv)
    names = args.tasks or tasks.NAMES
    BUILD.mkdir(exist_ok=True)
    path = BUILD / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {"tasks": {}}
    manifest.update(bench_build.build_tools(), built=datetime.now().isoformat(timespec="seconds"))
    for name in names:
        with tempfile.TemporaryDirectory(prefix=f"knows-{name}-") as scratch:
            facts, envs = build_task(name, Path(scratch))
        manifest["tasks"][name] = {**facts, "venvs": envs}
        print(f"{name}: {facts['questions']} questions; removed: {', '.join(facts['removed']) or 'nothing'}")
        print(f"  raw     {facts['trace_bytes']:,} bytes, attempt {facts['trace_attempts']}")
        print(f"  ormaos  {facts['recordings']}")
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
