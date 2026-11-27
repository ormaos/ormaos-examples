"""Run report.ipynb from top to bottom and print what its last cell printed."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).parent


def main():
    notebook = nbformat.read(HERE / "report.ipynb", as_version=4)
    NotebookClient(notebook, kernel_name="python3", resources={"metadata": {"path": str(HERE)}}).execute()
    nbformat.write(notebook, HERE / "report.executed.ipynb")
    printed = [
        output["text"]
        for output in notebook.cells[-1]["outputs"]
        if output["output_type"] == "stream" and output["name"] == "stdout"
    ]
    print("".join(printed), end="")


if __name__ == "__main__":
    main()
