# agent-bench/knows

A benchmark for one question: does an agent know what happened in an execution, with nothing but the folder it left, with a raw trace of it, or with an Ormaos recording of it?

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## The tasks

Nine executions. Seven are the programs of [`../../use-cases`](../../use-cases), each with the execution its `scenario.py` records and the questions of its `questions.json`. Two are the jobs [`order-sync`](../../order-sync) and [`freight-quote`](../../freight-quote), on the night that [`../bugs`](../bugs) plays; their questions are in [`tasks.py`](tasks.py).

| Task | The execution | Taken out of the folder afterwards | Questions |
|---|---|---|---|
| `web-backend` | `python main.py`: one request through the test client | nothing (the program builds its own database) | 7 |
| `data-pipeline` | `python pipeline.py` | `orders.csv`, `customers.csv` | 7 |
| `notebook` | the code cells of `report.ipynb`, in a Jupyter kernel, in the order of their saved execution counts | `sales.csv` | 6 |
| `ml-training` | `python train.py` | nothing (the data comes from a seed) | 7 |
| `rl-env` | `python3 run.py` | nothing (the policy is seeded) | 6 |
| `ai-app` | `python3 app.py` | `tickets.json` | 7 |
| `agent-change` | `python3 run.py` at each of the two commits of a repository | nothing (the input is in the commits) | 8 |
| `order-sync` | last night's `python3 job.py --source api` | nothing more: the sales system has today's orders | 7 |
| `freight-quote` | last night's `python3 job.py` | nothing more: the dispatch list is today's | 7 |

An agent gets the folder as the execution left it, without the input files named above, and `questions.json`: every question with its id and the format of its answer, and no answer. It writes `answers.json`.

The questions ask what happened: whether a function ran, how many times, in which order, which exceptions were handled where, which rows went in and out, which files and requests. The answers come from an oracle that does not read a trace or a recording: for the seven programs, the second execution under `sys.settrace` that `scenario.py` makes ([`../../use-cases/common.py`](../../use-cases/common.py)); for the two jobs, one more copy of the night under the same tracer.

## The arms

All three arms have the same task text: what ran, that the folder is as it left it, and what to write. Two arms add one thing to the folder and one sentence to the text:

| Arm | Added to the folder | Added to the text |
|---|---|---|
| `none` | nothing | nothing |
| `raw` | `result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of the execution, default settings (`result-r1.json` and `result-r2.json` for `agent-change`) | that the file is there and how to read it |
| `ormaos` | `.ormaos/`: the Ormaos recording of the execution, and the `ormaos` command line in `.venv/` | that the recording is there, and to run `.venv/bin/ormaos guide` first |

The execution is played once per arm, in separate copies mounted at the same path, `/srv/<task>`: as it is, under `viztracer`, under `ormaos run`. `build.py` stops if the copies do not leave the same files.

The four programs that need a library have it in `.venv/`, mounted read-only, in every arm. In the `ormaos` arm that environment also has Ormaos; VizTracer is in none of them. The cells of the notebook import `ormaos`: in the `none` and `raw` arms that name is a module whose `record()` does nothing.

## Grading

`answers.json` is one JSON object: the id of every question, and under it the answer. Each question has a rule in [`rules.json`](rules.json), written before any run; [`grade.py`](grade.py) describes the rules. In short: numbers are equal in value; names of functions and of exception types are compared by their last dotted part; file names without `./`; a list is compared in order or as a set, as the rule says; an object by its keys. An answer is right or wrong as a whole, and the score of a run is the share of its questions that are right. No `answers.json`, or one that is not JSON, is score 0.

## Running it

Needs Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, git, the `claude` command line signed in, and a checkout of `ormaos-python` next to this repository.

```bash
python3 build.py            # the folders of every task and arm, in .build/
python3 run.py --runs 3     # 9 tasks x 3 arms x 3 runs
```

A run: the folder is copied, mounted at `/srv/<task>` inside bubblewrap with nothing else of the machine but the system (`/usr` and `/etc`, read-only), the `claude` program and its login; `claude -p --model claude-opus-5-5 --safe-mode --strict-mcp-config` gets the task text, with the tools Bash, Read, Grep, Glob, Edit and Write, and 15 minutes. Then `answers.json` is graded. The network is not cut inside the sandbox: the agent needs it to reach the model.

Every slot is run once and counts. Nothing is run again and nothing is left out: a run that used up its time, or that ended with an error, counts with the answers it left. The paths outside its folder that an agent named are recorded, as information.

`run.py` writes, in `results/<date>-<time>/`:

- `results.jsonl`: one line per run, with the score and which questions were right, the answers, the wall time, the tool calls, the tokens as the command line reports them, whether the agent ran the program again, and the paths outside its folder that it named;
- `report.md`: per arm, the mean score with a 95% bootstrap interval over its runs, the median time, tool calls and tokens, and how many runs ran the program again; the same per task; per question, the runs that got it right;
- `streams/` and `work/`: what every agent said and did, and the folder it left.

Options: `--tasks a,b`, `--arms none,raw`, `--timeout SECONDS`, `--jobs N` (agents at the same time, default 3), `--out DIR`, `--report DIR` (write the report of a finished run again).

## Limits

- No expectation was written before the run of 2026-11-27 ([`results/20261127-140018`](results/20261127-140018/report.md)): the rules of `rules.json` were, what each arm would score was not.
- In that run, in 4 of the 9 tasks every arm scored 1.00 (`web-backend`, `ml-training`, `rl-env`, `freight-quote`); those tasks do not separate the arms.
- The gap between `raw` and `ormaos` in that run (0.94 and 1.00) comes mostly from `data-pipeline` (0.05 of the 0.06): its questions ask the row counts of DataFrames, which Ormaos records and VizTracer with its default settings does not.
- The programs, the executions and the questions were written by the people who make Ormaos. The questions are about calls, exceptions, shapes and I/O, which is what Ormaos records.
- Four of the nine programs (`web-backend`, `ml-training`, `rl-env`, `agent-change`) read no input that can be taken away, so an agent can run them again and count for itself; the report says how many runs did.
- One model, one prompt per arm, one tracer with its default settings.
- The dates in the data of the two jobs are relative to the day `build.py` ran: build on the day of the run.
