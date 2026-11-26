"""Build, for every bug, what the agents get: task/ and the three arms.

    python3 build.py              # every bug
    python3 build.py fx-rates     # some bugs

For a bug the same nights are played three times, in three copies of the
code mounted at the same path: once as they were (the data left go to
``task/``), once with last night's run under VizTracer with its default
settings (``arms/raw/result.json``) and once with it under ``ormaos run``
(``arms/ormaos/.ormaos`` and the ``.venv`` that has the ormaos command line).
The three must leave the same data, and the data must show the symptom.

Needs bubblewrap, the network once (to download VizTracer and build the
Ormaos wheel) and a checkout of ormaos-python next to this repository.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import benchlib
from benchlib import BUGS, TOOLS, VIZTRACER, World

VIZTRACER_VERSION = "1.1.1"
ORMAOS = benchlib.ROOT.parents[1] / "ormaos-python"
WHEELS = TOOLS / "wheels"
TRACE_ATTEMPTS = 40
ORMAOS_FRONT = (".venv/bin/ormaos", "run", "--", ".venv/bin/python")


def run(command, **kwargs):
    done = subprocess.run(command, capture_output=True, text=True, check=False, **kwargs)
    if done.returncode != 0:
        raise SystemExit(f"failed: {' '.join(map(str, command))}\n{done.stdout}{done.stderr}")
    return done


def in_sandbox(folder, mount, command, readonly=()):
    return run([*benchlib.sandbox(folder, mount, readonly=readonly), *command])


def build_tools():
    """The wheels, and VizTracer installed where the sandbox mounts it."""
    WHEELS.mkdir(parents=True, exist_ok=True)
    if not list(WHEELS.glob("viztracer-*.whl")):
        run([sys.executable, "-m", "pip", "download", "--quiet", "-d", str(WHEELS),
             f"viztracer=={VIZTRACER_VERSION}"])
    for old in WHEELS.glob("ormaos-*.whl"):
        old.unlink()
    with tempfile.TemporaryDirectory() as scratch:
        # Build from a copy: nothing is written in the checkout.
        copy = Path(scratch) / "ormaos-python"
        copy.mkdir()
        for part in ("src", "pyproject.toml", "README.md", "LICENSE", "ormaos.pth"):
            source = ORMAOS / part
            (shutil.copytree if source.is_dir() else shutil.copy)(source, copy / part)
        run([sys.executable, "-m", "pip", "wheel", "--quiet", "--no-deps",
             "-w", str(WHEELS), str(copy)])
    home = TOOLS / "viztracer"
    if not (home / "bin" / "viztracer").exists():
        shutil.rmtree(home, ignore_errors=True)
        home.mkdir()
        wheels = [f"/wheels/{w.name}" for w in WHEELS.glob("*.whl") if not w.name.startswith("ormaos")]
        in_sandbox(home, VIZTRACER, ["python3", "-m", "venv", "."], readonly=[(WHEELS, "/wheels")])
        in_sandbox(home, VIZTRACER, ["bin/pip", "install", "--quiet", "--no-index", *wheels],
                   readonly=[(WHEELS, "/wheels")])
    commit = run(["git", "-C", str(ORMAOS), "rev-parse", "--short", "HEAD"]).stdout.strip()
    dirty = bool(run(["git", "-C", str(ORMAOS), "status", "--porcelain"]).stdout.strip())
    return {"ormaos_commit": commit + ("+changes" if dirty else ""),
            "viztracer": VIZTRACER_VERSION,
            "python": in_sandbox(TOOLS, "/srv/tools", ["python3", "-V"]).stdout.strip()}


def fresh_task(name, story):
    """task/ with the code only. A reused example is copied from its folder."""
    task = BUGS / name / "task"
    source = getattr(story, "SOURCE", None)
    if source is not None:
        shutil.rmtree(task, ignore_errors=True)
        shutil.copytree(source, task, ignore=shutil.ignore_patterns(*story.NOT_COPIED))
    for left in ("data", "inbox", "TASK.md", ".venv", ".ormaos", "result.json"):
        path = task / left
        shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
    for cache in task.rglob("__pycache__"):
        shutil.rmtree(cache)
    return task


def install_ormaos(world):
    wheel = next(WHEELS.glob("ormaos-*.whl"))
    readonly = [(WHEELS, "/wheels")]
    in_sandbox(world.folder, world.mount, ["python3", "-m", "venv", ".venv"], readonly)
    in_sandbox(world.folder, world.mount,
               [".venv/bin/pip", "install", "--quiet", "--no-index", f"/wheels/{wheel.name}"], readonly)
    # Only the ormaos command line is needed in the folder.
    in_sandbox(world.folder, world.mount, [".venv/bin/python", "-m", "pip", "uninstall", "--quiet", "-y", "pip"])


def trace_is_whole(path, mount, printed):
    """The trace loads, has the job's own process, and no process was left out."""
    if "invalid json" in printed:
        return False
    try:
        with open(path, encoding="utf-8") as handle:
            events = json.load(handle)["traceEvents"]
    except (OSError, ValueError, KeyError):
        return False
    return any(f"({mount}/job.py:" in event.get("name", "") for event in events)


def build_bug(name, scratch):
    story = benchlib.scenario(name)
    bug = BUGS / name
    task = fresh_task(name, story)
    shutil.rmtree(bug / "arms", ignore_errors=True)
    worlds, trace_attempts = {}, 0
    for arm in benchlib.ARMS:
        folder = scratch / name / arm
        while True:
            benchlib.copy_code(task, folder)
            if arm == "none":
                worlds[arm] = World(name, folder)
            elif arm == "raw":
                worlds[arm] = World(name, folder, bad_run=(f"{VIZTRACER}/bin/viztracer",),
                                    readonly=[(TOOLS / "viztracer", VIZTRACER)])
            else:
                worlds[arm] = World(name, folder, bad_run=ORMAOS_FRONT)
                install_ormaos(worlds[arm])
            done = story.play(worlds[arm])
            if not benchlib.said_ok(done, story.SAYS):
                raise SystemExit(f"{name}/{arm}: last night did not say OK:\n{done.stdout}{done.stderr}")
            if arm != "raw":
                break
            # VizTracer sometimes writes a duration that is not a number, and then
            # leaves that process out of the file it saves: trace the night again.
            trace_attempts += 1
            if trace_is_whole(folder / "result.json", worlds[arm].mount, done.stdout):
                break
            if trace_attempts == TRACE_ATTEMPTS:
                raise SystemExit(f"{name}: no whole trace in {TRACE_ATTEMPTS} attempts")
            shutil.rmtree(folder)

    plain = worlds["none"].folder
    wrong = story.wrong(plain)
    if not wrong:
        raise SystemExit(f"{name}: the data left do not show the symptom")
    left = story.data_left(plain)
    for arm in ("raw", "ormaos"):
        if story.data_left(worlds[arm].folder) != left:
            raise SystemExit(f"{name}: the {arm} run did not leave the same data")
    today = in_sandbox(plain, worlds["none"].mount, ["python3", *story.RUNS_WITH.split()[1:]])
    if not benchlib.said_ok(today, story.SAYS):
        raise SystemExit(f"{name}: today's run did not say OK")
    new = [item for item in getattr(story, "wrong_after_today", story.wrong)(plain) if item not in wrong]
    if new:
        raise SystemExit(f"{name}: today's run made more wrong: {new}")

    for part in ("data", "inbox"):
        if (plain / part).exists():
            shutil.rmtree(plain / part)
    # today's run above changed the copy: play the nights again for task/
    worlds["none"] = World(name, scratch / name / "task")
    benchlib.copy_code(task, worlds["none"].folder)
    story.play(worlds["none"])
    plain = worlds["none"].folder
    if story.data_left(plain) != left:
        raise SystemExit(f"{name}: two plain runs did not leave the same data")
    for part in ("data", "inbox"):
        if (plain / part).exists():
            shutil.copytree(plain / part, task / part)
    (task / "TASK.md").write_text(story.SYMPTOM + "\n", encoding="utf-8")

    (bug / "arms" / "raw").mkdir(parents=True)
    shutil.copy(worlds["raw"].folder / "result.json", bug / "arms" / "raw" / "result.json")
    (bug / "arms" / "ormaos").mkdir()
    for part in (".venv", ".ormaos"):
        shutil.copytree(worlds["ormaos"].folder / part, bug / "arms" / "ormaos" / part, symlinks=True)

    if hasattr(story, "gone"):
        needles = [needle.encode() for needle in story.gone(worlds["none"])]
        for path in task.rglob("*"):
            if path.is_file():
                content = path.read_bytes()
                for needle in needles:
                    if needle in content:
                        raise SystemExit(f"{name}: {needle!r} is still in {path}")

    # Each arm as an agent gets it: the trace loads, the recording reads.
    facts = {"wrong": wrong, "trace_attempts": trace_attempts, "lines_of_code": sum(
        len(p.read_text(encoding="utf-8").splitlines()) for p in task.glob("*.py"))}
    raw = benchlib.assemble(name, "raw", scratch / name / "as-raw")
    count = in_sandbox(raw, worlds["raw"].mount, [
        "python3", "-c", "import json; print(len(json.load(open('result.json'))['traceEvents']))"])
    facts["trace_events"] = int(count.stdout)
    facts["trace_bytes"] = (raw / "result.json").stat().st_size
    recorded = benchlib.assemble(name, "ormaos", scratch / name / "as-ormaos")
    show = in_sandbox(recorded, worlds["ormaos"].mount, [".venv/bin/ormaos", "show", "last"])
    facts["recording"] = show.stdout.splitlines()[0]
    listed = in_sandbox(recorded, worlds["ormaos"].mount, [".venv/bin/ormaos", "list"])
    if not listed.stdout.startswith("1 recording"):
        raise SystemExit(f"{name}: expected one recording:\n{listed.stdout}")
    return facts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bugs", nargs="*", help="the bugs to build (default: all)")
    args = parser.parse_args(argv)
    names = args.bugs or benchlib.bug_names()
    manifest_path = TOOLS / "manifest.json"
    tools = build_tools()
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"bugs": {}}
    manifest.update(tools, built=datetime.now().isoformat(timespec="seconds"))
    with tempfile.TemporaryDirectory(prefix="agent-bench-build-") as scratch:
        for name in names:
            facts = build_bug(name, Path(scratch))
            manifest["bugs"][name] = facts
            print(f"{name}: {facts['lines_of_code']} lines; wrong this morning: "
                  f"{', '.join(map(str, facts['wrong']))}")
            print(f"  raw     {facts['trace_events']} events, {facts['trace_bytes']} bytes, "
                  f"attempt {facts['trace_attempts']}")
            print(f"  ormaos  {facts['recording']}")
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
