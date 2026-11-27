"""Run the code cells of report.ipynb, in the folder it is started in, in the
order of their saved execution counts, in one Jupyter kernel. This is the
session that use-cases/notebook/scenario.py records."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

folder = Path.cwd()
notebook = nbformat.read(folder / "report.ipynb", as_version=4)
code = [cell for cell in notebook.cells if cell.cell_type == "code"]
saved = sorted(range(len(code)), key=lambda n: code[n]["execution_count"])
client = NotebookClient(notebook, kernel_name="python3", resources={"metadata": {"path": str(folder)}})
with client.setup_kernel():
    for n in saved:
        client.execute_cell(code[n], notebook.cells.index(code[n]))
