"""Run the code cells of report.ipynb, in the folder it is started in, in the
order of their saved execution counts, in one Jupyter kernel: the session of
``../knows/session.py``.

    session.py                     as it is
    session.py --values            `ormaos.record()` records values too
    session.py --trace out.json    under the tracer of tracer.py, no Ormaos

The two options run one cell before the first (and --trace one after the
last) that is not a cell of the notebook and gets no execution count, as
``use-cases/notebook/scenario.py`` does for its oracle.
"""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

VALUES = """
import functools as _functools, ormaos as _ormaos
_ormaos.record = _functools.partial(_ormaos.record, values=True)
"""
BEFORE = """
import contextlib, sys, types
_stub = types.ModuleType("ormaos")
_stub.record = lambda *args, **kwargs: contextlib.nullcontext()
sys.modules["ormaos"] = _stub
sys.path.insert(0, "/opt/knows2")
import tracer as _tracer_module
_tracer = _tracer_module.kernel_tracer()
"""
AFTER = """
import json as _json
with open({out!r}, "w") as _out:
    _json.dump(_tracer.result(), _out)
"""

folder = Path.cwd()
values = "--values" in sys.argv
trace = str(folder / sys.argv[sys.argv.index("--trace") + 1]) if "--trace" in sys.argv else None
notebook = nbformat.read(folder / "report.ipynb", as_version=4)
code = [cell for cell in notebook.cells if cell.cell_type == "code"]
saved = sorted(range(len(code)), key=lambda n: code[n]["execution_count"])
client = NotebookClient(notebook, kernel_name="python3", resources={"metadata": {"path": str(folder)}})
extra = nbformat.v4.new_code_cell
counts = []
with client.setup_kernel():
    if values:
        client.execute_cell(extra(VALUES), 0, store_history=False)
    if trace:
        client.execute_cell(extra(BEFORE), 0, store_history=False)
    for n in saved:
        client.execute_cell(code[n], notebook.cells.index(code[n]))
        counts.append({"cell": n + 1, "execution_count": code[n]["execution_count"],
                       "outputs": [dict(o) for o in code[n].get("outputs", [])]})
    if trace:
        client.execute_cell(extra(AFTER.format(out=trace)), 0, store_history=False)
if trace:
    import json

    found = json.loads(Path(trace).read_text())
    found["cells"] = counts
    Path(trace).write_text(json.dumps(found, default=str))
