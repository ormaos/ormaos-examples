"""Build, for every task, the folder an agent gets in each of the four arms,
and the oracle's answers.

    python3 build.py                 # every task
    python3 build.py rl-env ai-app   # some tasks

As in ``../knows/build.py`` the same execution is played in separate copies
of the program, each mounted at ``/srv/<task>``: as it was (``none``), under
VizTracer with its default settings (``raw``), under ``ormaos run``
(``ormaos``), under ``ormaos run --values`` (``ormaos-values``), and once
more under the tracer of ``tracer.py`` (the oracle). The copies must leave
the same files.

The questions are those of ``writer/<task>/questions.json``, word for word,
with the format the writer gave. ``oracle.py`` answers them from the
oracle's copy. A question it cannot answer with one unambiguous answer is
dropped, and ``dropped.json`` is written with the reason.

Everything else goes to ``.build/`` (not committed): ``folders/<task>/<arm>/``,
``venvs/<task>/``, ``answers/<task>.json`` and ``manifest.json``.
"""

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import k2
import oracle
import rules
from k2 import ARMS, BUILD, HERE, TASKS, grade, kb


def left(name, stage):
    return (kb.left(name, stage) if TASKS[name].get("job") else
            {file: digest for file, digest in kb.left(name, stage).items() if not file.startswith("oracle-trace")})


def written_questions(name):
    """The questions as the writer left them: a list of {"id", "question", "format"}."""
    found = json.loads((HERE / "writer" / name / "questions.json").read_text(encoding="utf-8"))
    if not (isinstance(found, list) and all(set(q) >= {"id", "question", "format"} for q in found)):
        raise SystemExit(f"{name}: writer/{name}/questions.json is not a list of questions")
    return found


def build_task(name, scratch):
    task = TASKS[name]
    envs = k2.venvs(name)
    stages, attempts = {}, 0
    for arm in (*ARMS, "oracle"):
        folder = scratch / arm
        while True:
            stages[arm] = k2.played(name, arm, folder, envs)
            if arm != "raw":
                break
            attempts += 1  # VizTracer sometimes leaves a process out: play it again
            if kb.trace_is_whole(stages[arm]):
                break
            if attempts == kb.TRACE_ATTEMPTS:
                raise SystemExit(f"{name}: no whole trace in {kb.TRACE_ATTEMPTS} attempts")
            shutil.rmtree(folder)
    same = left(name, stages["none"])
    for arm in (*ARMS[1:], "oracle"):
        if left(name, stages[arm]) != same:
            raise SystemExit(f"{name}: the {arm} copy did not leave what the plain one left")

    where = stages["oracle"].folder
    read = lambda file: json.loads((where / file).read_text(encoding="utf-8"))  # noqa: E731
    labels = task.get("labels")
    found = {label: read(f"oracle-trace-{label}.json") for label in labels} if labels else read(k2.ORACLE_TRACE)
    answered = oracle.answers(name, found, where)
    questions = written_questions(name)
    if [q["id"] for q in questions] != list(rules.ALL[name]) or set(answered) != set(rules.ALL[name]):
        raise SystemExit(f"{name}: rules.json and oracle.py do not have the ids of the questions")
    dropped = {qid: a.reason for qid, a in answered.items() if isinstance(a, oracle.Dropped)}
    answers = json.loads(json.dumps({qid: a for qid, a in answered.items() if qid not in dropped}))
    kept = {qid: rule for qid, rule in rules.ALL[name].items() if qid not in dropped}
    rules.RULES[name] = kept
    shown = {"questions": [{"id": q["id"], "question": q["question"], "format": q["format"]}
                           for q in questions if q["id"] not in dropped]}
    if grade.grade(name, answers, answers)[0] != 1.0 or grade.grade(name, {}, answers)[0] != 0.0:
        raise SystemExit(f"{name}: the oracle's answers do not grade 1.0, or an empty file not 0")

    out = BUILD / "folders" / name
    shutil.rmtree(out, ignore_errors=True)
    facts = {"questions": len(kept), "dropped": dropped, "removed": task["removed"], "trace_attempts": attempts}
    for arm in ARMS:
        folder = stages[arm].folder
        for cache in folder.rglob("__pycache__"):
            shutil.rmtree(cache)
        for file in task["removed"]:
            (folder / file).unlink()
        (folder / "questions.json").write_text(json.dumps(shown, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(folder, out / arm, symlinks=True)
    facts["files"] = sorted(p.name for p in (out / "none").iterdir())
    facts["trace_bytes"] = sum(p.stat().st_size for p in kb.traces_of(out / "raw"))
    expected = len(labels or []) or (4 if name == "notebook" else 1)
    for arm in ("ormaos", "ormaos-values"):
        stage = k2.Stage(name, arm, out / arm, envs[arm])
        listed = stage.sh([".venv/bin/ormaos", "list"]).stdout
        if not listed.startswith(f"{expected} recording"):
            raise SystemExit(f"{name}/{arm}: expected {expected} recordings:\n{listed}")
        with_values = "\nvalues: recorded" in stage.sh([".venv/bin/ormaos", "show", "last"]).stdout
        if with_values != (arm == "ormaos-values"):
            raise SystemExit(f"{name}/{arm}: `ormaos show last` {'speaks' if with_values else 'does not speak'} of --values")
        facts[f"recordings_{arm}"] = listed.splitlines()[0]
        facts[f"bytes_{arm}"] = sum(p.stat().st_size for p in (out / arm / ".ormaos").rglob("*") if p.is_file())
    (BUILD / "answers").mkdir(exist_ok=True)
    (BUILD / "answers" / f"{name}.json").write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
    agents = {"none": envs["none"], "raw": envs["none"], "ormaos": envs["ormaos"], "ormaos-values": envs["ormaos"]}
    return facts, {arm: (str(agents[arm]) if agents[arm] else None) for arm in ARMS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tasks", nargs="*", help="the tasks to build (default: all)")
    args = parser.parse_args(argv)
    names = args.tasks or k2.NAMES
    BUILD.mkdir(exist_ok=True)
    path = BUILD / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {"tasks": {}}
    manifest.update(kb.bench_build.build_tools(), built=datetime.now().isoformat(timespec="seconds"))
    for name in names:
        with tempfile.TemporaryDirectory(prefix=f"knows2-{name}-") as scratch:
            facts, envs = build_task(name, Path(scratch))
        manifest["tasks"][name] = {**facts, "venvs": envs}
        print(f"{name}: {facts['questions']} questions; removed: {', '.join(facts['removed']) or 'nothing'}")
        for qid, reason in facts["dropped"].items():
            print(f"  dropped {qid}: {reason}")
        print(f"  raw            {facts['trace_bytes']:,} bytes, attempt {facts['trace_attempts']}")
        print(f"  ormaos         {facts['recordings_ormaos']}, {facts['bytes_ormaos']:,} bytes")
        print(f"  ormaos-values  {facts['recordings_ormaos-values']}, {facts['bytes_ormaos-values']:,} bytes", flush=True)
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    dropped = {name: manifest["tasks"][name]["dropped"] for name in k2.NAMES
               if manifest["tasks"].get(name, {}).get("dropped")}
    (HERE / "dropped.json").write_text(json.dumps(dropped, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
