"""A run spec, and the expectations written before the run.

A spec is ``specs/<name>.toml``:

    benchmark = "knows2"
    tasks = ["order-sync"]            # left out: every task of the benchmark
    arms = ["none", "raw", "ormaos", "ormaos-values"]
    agent = "claude-code"
    model = "claude-opus-5-5"
    effort = "default"                # or a level the agent's command line knows
    n = 1                             # runs per task and arm
    time_limit_seconds = 900          # for one run
    test = true                       # left out, or true: a test of the harness, never shown as a result

A batch does not start unless ``expectations/<name>.md`` exists: what is
expected of the run, written before it. Its sha256 is stored with the
results, and ``verify`` fails for a results folder whose expectations file
has changed since.
"""

import hashlib
import json
import tomllib
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REQUIRED = {"benchmark": str, "arms": list, "agent": str, "model": str, "effort": str,
            "n": int, "time_limit_seconds": int}
OPTIONAL = {"tasks": list, "test": bool}


class Refused(Exception):
    """The reason a batch does not start, or a build fails."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    path = Path(path)
    if path.suffix != ".toml":
        raise Refused(f"{path}: a run spec is a .toml file")
    spec = tomllib.loads(path.read_text(encoding="utf-8"))
    for key, kind in REQUIRED.items():
        if not isinstance(spec.get(key), kind) or isinstance(spec.get(key), bool):
            raise Refused(f"{path.name}: {key} is missing or not {kind.__name__}")
    for key, kind in OPTIONAL.items():
        if key in spec and not isinstance(spec[key], kind):
            raise Refused(f"{path.name}: {key} is not {kind.__name__}")
    unknown = set(spec) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        raise Refused(f"{path.name}: unknown keys: {', '.join(sorted(unknown))}")
    if spec["n"] < 1 or spec["time_limit_seconds"] < 1:
        raise Refused(f"{path.name}: n and time_limit_seconds are at least 1")
    return {"name": path.stem, **spec}


def expectations(name, root=HARNESS):
    """The expectations file of a spec; a batch without one is refused."""
    path = Path(root) / "expectations" / f"{name}.md"
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise Refused(f"expectations/{name}.md does not exist: write what you expect of this run before it starts")
    return path


def verify(out, root=HARNESS):
    """Fail when the expectations of a results folder changed after its run
    started, or when a slot of its plan has no result or more than one."""
    out = Path(out)
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    name, stored = run["spec"]["name"], run["expectations"]["sha256"]
    path = Path(root) / "expectations" / f"{name}.md"
    if not path.is_file():
        raise Refused(f"{out}: expectations/{name}.md is gone; the run started with sha256 {stored}")
    if sha256(path) != stored:
        raise Refused(f"{out}: expectations/{name}.md changed after the run started "
                      f"(sha256 {sha256(path)}, at the start {stored})")
    lines = [json.loads(line) for line in (out / "results.jsonl").read_text(encoding="utf-8").splitlines() if line]
    done = [(r["task"], r["arm"], r["run"]) for r in lines]
    planned = [tuple(slot) for slot in run["plan"]]
    if len(set(done)) != len(done):
        raise Refused(f"{out}: a slot has more than one result")
    if set(done) - set(planned):
        raise Refused(f"{out}: results that were not planned: {sorted(set(done) - set(planned))}")
    if run.get("finished") and set(planned) - set(done):
        raise Refused(f"{out}: planned slots without a result: {sorted(set(planned) - set(done))}")
    return run
