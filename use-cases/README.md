# Use cases: one program per kind of developer

Seven small programs. Each is a normal program with its own README, uses the standard library plus only the library its kind needs, and runs from a copy of its folder anywhere.

| Folder | Kind | Needs |
|---|---|---|
| [`web-backend`](web-backend) | a FastAPI service over SQLite, called through its test client | fastapi, httpx |
| [`data-pipeline`](data-pipeline) | a pandas report from two CSV files | pandas |
| [`notebook`](notebook) | a Jupyter notebook, run with nbclient, with `with ormaos.record():` in its cells | nbclient, nbformat, ipykernel |
| [`ml-training`](ml-training) | a PyTorch training loop on CPU | torch |
| [`rl-env`](rl-env) | an environment with a reward and an episode loop | standard library |
| [`ai-app`](ai-app) | an app that calls a model API over HTTP, here a local stand-in | standard library |
| [`agent-change`](agent-change) | a git repository and a change a coding agent made to it | standard library, git |

## One execution of each, and questions about it

Each program prints one ordinary line, and in each execution something happened that the line does not say. Next to each program:

- `scenario.py` copies the program to a new folder and records that execution with Ormaos (`agent-change` records two, before and after the change);
- `questions.json` has factual questions about what happened in it: whether a function ran, how many times, which rows and shapes, which I/O, what the second execution did that the first did not;
- `demo.txt` is one `ormaos` command on the recording and what it printed.

There are 48 questions over the 7 executions. The answer of each is computed by `scenario.py` from a second execution of the same program, without Ormaos, under `sys.settrace` ([`common.py`](common.py)), with a trace callback on sqlite3 connections, a wrapper around `open`, the execution counts of the Jupyter kernel and `git rev-parse` where the question needs them. No answer is read from the recording. The programs are deterministic, and every answer was the same in 3 runs.

Ormaos shows what happened in an execution. Whether that is what should have happened is for the reader to decide; the questions ask only what happened.

## Run one

In a Python 3.12 or newer with Ormaos and the folder's `requirements.txt`:

```bash
python3 -m venv .venv && .venv/bin/pip install git+https://github.com/ormaos/ormaos-python -r web-backend/requirements.txt
.venv/bin/python web-backend/scenario.py /tmp/web-backend
```

It prints every question with its answer, then the command of `demo.txt` with its output, and leaves the program and its recording in the folder. The folder must not exist yet.

```bash
.venv/bin/python web-backend/scenario.py /tmp/web-backend-again --check    # exit 1 when an answer is not the committed one
.venv/bin/python web-backend/scenario.py /tmp/web-backend-new --update     # write questions.json and demo.txt again
```

For `ml-training`, the CPU build of torch is enough: add `--extra-index-url https://download.pytorch.org/whl/cpu` to the `pip install`.
