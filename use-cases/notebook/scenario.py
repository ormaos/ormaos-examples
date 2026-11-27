"""Record one session of the notebook, and compute what happened in it.

    python scenario.py /tmp/notebook

`report.ipynb` is saved as its last session left it: each code cell has the
execution count the kernel gave it. This script runs the cells again in
that order, in a real kernel, with nbclient. Four cells hold a
`with ormaos.record():` block, so the folder gets four recordings, `r1` to
`r4`, in the order the blocks ran.

Then the same session runs again in another copy, in another kernel, where
`ormaos.record()` does nothing and `sys.settrace` is on; the answers in
`questions.json` come from the calls seen there and from the execution
counts that kernel gave.

Needs, in the Python that runs it: ormaos, and the requirements.txt.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "requirements.txt", "report.ipynb", "sales.csv", "run_notebook.py"]
SHOW = ["ormaos", "tree", "r2"]
FUNCTIONS = ("load", "drop_key_accounts", "add_tax", "total")

# Run in the kernel of the second session, before the first cell and after
# the last one. Neither is a cell of the notebook, and neither gets an
# execution count.
BEFORE = """
import contextlib, sys, types
_stub = types.ModuleType("ormaos")
_stub.record = lambda *args, **kwargs: contextlib.nullcontext()
sys.modules["ormaos"] = _stub
sys.path.insert(0, {use_cases!r})
import common as _common
_tracer = _common.kernel_tracer()
"""
AFTER = """
import json as _json
with open({out!r}, "w") as _out:
    _json.dump(_tracer.result(), _out)
"""


def session(folder, traced=None):
    """Run the code cells of the notebook in `folder` in the order of their
    saved execution counts. Give, for each cell that ran, its position among
    the code cells (from 1) and the execution count this kernel gave it."""
    import nbformat
    from nbclient import NotebookClient

    notebook = nbformat.read(folder / "report.ipynb", as_version=4)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    saved = sorted(range(len(code)), key=lambda n: code[n]["execution_count"])
    client = NotebookClient(
        notebook, kernel_name="python3", resources={"metadata": {"path": str(folder)}}
    )
    extra = nbformat.v4.new_code_cell
    with client.setup_kernel(env=common.environment()):
        if traced:
            client.execute_cell(
                extra(BEFORE.format(use_cases=str(HERE.parent))), 0, store_history=False
            )
        for n in saved:
            client.execute_cell(code[n], notebook.cells.index(code[n]))
        if traced:
            client.execute_cell(extra(AFTER.format(out=str(traced))), 0, store_history=False)
    return [{"cell": n + 1, "execution_count": code[n]["execution_count"]} for n in saved]


def main():
    args = common.arguments(__doc__)
    common.need("nbclient", "nbformat", "ipykernel")
    os.environ.pop("ORMAOS_DIR", None)
    common.copy_program(HERE, args.target, FILES)
    session(args.target)

    import json

    with tempfile.TemporaryDirectory(prefix="oracle-") as name:
        folder = Path(name).resolve() / "program"
        common.copy_program(HERE, folder, FILES)
        ran = session(folder, traced=folder.parent / "trace.json")
        found = json.loads((folder.parent / "trace.json").read_text())
    shutil.rmtree(args.target / "__pycache__", ignore_errors=True)

    by_count = sorted(ran, key=lambda item: item["execution_count"])
    in_order = [c for c in found["calls"] if c["fn"] in FUNCTIONS]
    one = lambda name: common.calls(found, name)[0]  # noqa: E731
    rows = lambda name: {  # noqa: E731
        "in": one(name)["args"]["rows"]["len"],
        "out": one(name)["result"]["len"],
    }

    questions = [
        {
            "id": "q1",
            "question": "In which order did the code cells run? Give each by its position among the code cells of the notebook, from 1.",
            "answer": [item["cell"] for item in by_count],
            "oracle": "the execution counts the kernel gave, read through nbclient",
        },
        {
            "id": "q2",
            "question": "In which order did load, drop_key_accounts, add_tax and total run?",
            "answer": [c["fn"] for c in in_order],
            "oracle": "sys.settrace in the kernel",
        },
        {
            "id": "q3",
            "question": "How many times did each of load, drop_key_accounts, add_tax and total run?",
            "answer": {name: len(common.calls(found, name)) for name in FUNCTIONS},
            "oracle": "sys.settrace in the kernel",
        },
        {
            "id": "q4",
            "question": "How many rows did add_tax receive, and how many did it return?",
            "answer": rows("add_tax"),
            "oracle": "sys.settrace call and return events, len()",
        },
        {
            "id": "q5",
            "question": "How many rows did drop_key_accounts receive, and how many did it return?",
            "answer": rows("drop_key_accounts"),
            "oracle": "sys.settrace call and return events, len()",
        },
        {
            "id": "q6",
            "question": "How many rows did total receive?",
            "answer": one("total")["args"]["rows"]["len"],
            "oracle": "sys.settrace call event, len()",
        },
    ]
    common.finish(args, HERE, "notebook", ["r1", "r2", "r3", "r4"], questions, SHOW)


if __name__ == "__main__":
    main()
