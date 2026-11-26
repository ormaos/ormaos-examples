# agent-bench

A benchmark for one question: does a coding agent fix a bug more often when it has an Ormaos recording of the run that went wrong, than with nothing, or with a raw trace of that run?

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## The bugs

Eight small Python jobs (standard library only), each with one bug of a different kind. Each one runs from cron, prints its `... finished: OK` line and exits with code 0; what went wrong is visible only in the data it left. Running the job again today does not show it: the input of the bad night is gone.

| Bug | The job | The kind of bug |
|---|---|---|
| `order-sync` | applies orders to an inventory ([`../order-sync`](../order-sync)) | an exception that is caught and never seen |
| `freight-quote` | quotes freight from a carrier's API ([`../freight-quote`](../freight-quote)) | a silent fallback after HTTP calls that failed |
| `late-fees` | charges late fees on overdue invoices | the wrong branch, because of a value in the environment |
| `statement-import` | books a bank statement into a ledger | a loop that stops early |
| `fx-rates` | takes over exchange rates from a feed | a retry that never retries |
| `price-import` | takes over a supplier's price list | a subprocess whose failure is ignored |
| `points-grant` | grants loyalty points for purchases | an SQL statement that writes other rows too |
| `commission-run` | works out sales commissions | a value kept from one item to the next (not about exceptions) |

For a bug, in `bugs/<bug>/`:

- `task/` is what the agent gets: the code, the data left after the bad night, and the symptom in one sentence (`TASK.md`). `build.py` makes the data, and for the two jobs that live elsewhere in this repository it copies the code.
- `scenario.py` plays the nights: the nights before, the bad night, and what this morning looks like. It is not in `task/`.
- `hidden/check.py` decides whether the code is fixed. It is not in `task/` either. It plays the bad night again on the code it is given, and nights on which nothing is wrong; it passes only when the bad night no longer ends wrong and the other nights end as before. Its docstring says exactly what counts.
- `arms/` is what an arm adds (made by `build.py`).

## The arms

All three arms have the same `task/` and the same task text: the symptom, how cron runs the job, and "Find the cause and fix it." Two arms add one thing to the folder and one sentence to the text:

| Arm | Added to the folder | Added to the text |
|---|---|---|
| `none` | nothing | nothing |
| `raw` | `result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of the bad night's run, default settings | that the file is there and how to read it |
| `ormaos` | `.ormaos/`: the Ormaos recording of the bad night's run, and `.venv/` with the `ormaos` command line | that the recording is there, and to run `.venv/bin/ormaos guide` first |

The same nights are played three times, in three copies of the code mounted at the same path, with the same input: once as they are, once with the bad night under `viztracer`, once with it under `ormaos run`. `build.py` stops if the three do not leave the same data.

## Running it

Needs Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, the `claude` command line signed in, and a checkout of `ormaos-python` next to this repository.

```bash
python3 build.py            # task/ and arms/ of every bug
python3 run.py --runs 3     # 8 bugs x 3 arms x 3 runs
```

A run: `task/` and what the arm adds are copied to a new folder; the folder is mounted at `/srv/<bug>` inside bubblewrap, with nothing else of the machine but the system (`/usr` and `/etc`, read-only), the `claude` program and its login; `claude -p --model claude-opus-5-5 --safe-mode --strict-mcp-config` gets the task text, with the tools Bash, Read, Grep, Glob, Edit and Write, and 15 minutes. Then `hidden/check.py` judges the code it left. The network is not cut inside the sandbox: the agent needs it to reach the model.

`run.py` writes, in `results/<date>-<time>/`:

- `results.jsonl`: one line per run, with whether it is fixed and what the check said, the wall time, the tool calls, the tokens as the command line reports them, and the paths outside its folder that the agent named;
- `report.md`: per arm, fixes out of runs with the 95% Wilson score interval, and the same per bug;
- `streams/` and `work/`: what every agent said and did, and the folder it left.

A run in which the agent named a path outside its folder (or another host) does not count: it stays in `results.jsonl`, marked, and is run again. So is a run that ended with an error of the command line or of the model. A run that used up its time counts, with the code it left.

Options: `--bugs a,b`, `--arms none,raw`, `--timeout SECONDS`, `--jobs N` (agents at the same time, default 3), `--out DIR`, `--report DIR` (write the report of a finished run again).

## What it does not show

- Eight bugs written for this benchmark, by the people who make Ormaos, are not a sample of real bugs.
- One model, one prompt per arm, one tracer with its default settings.
- The dates in the data are relative to the day `build.py` ran: build on the day of the run.
