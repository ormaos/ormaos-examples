"""Grade the folder a run left, outside the container.

    python3 grading.py <benchmark> <task> <folder> <oracle file>

The runner starts this as a separate process, on a copy of the folder in a
place whose name says nothing, with an environment that holds only PATH. It
is told the benchmark and the task; it is not told the agent, the model, or
where the results go. It prints one JSON object.
"""

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]


def blind(benchmark, task, work, oracle_file):
    """Run the grader on a copy of ``work`` and return what it printed."""
    with tempfile.TemporaryDirectory(prefix="grade-") as scratch:
        copy = Path(scratch) / "work"
        shutil.copytree(work, copy, symlinks=True)
        shutil.copy(oracle_file, Path(scratch) / "oracle.json")
        done = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), benchmark, task, "work", "oracle.json"],
            cwd=scratch, env={"PATH": os.defpath}, capture_output=True, text=True, check=False, timeout=600,
        )
    if done.returncode != 0:
        raise RuntimeError(f"the grader failed: {done.stderr.strip()[-500:]}")
    return json.loads(done.stdout)


def main(argv):
    benchmark, task, work, oracle_file = argv[1:5]
    sys.path.insert(0, str(HARNESS))
    module = importlib.import_module(f"benchmarks.{benchmark}")
    print(json.dumps(module.grade(task, work, oracle_file)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
