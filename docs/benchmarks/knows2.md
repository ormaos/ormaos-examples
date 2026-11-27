# knows2: what an agent knows about an execution

N = 108 runs: 9 tasks x 4 arms x 3 runs, model `claude-opus-5-5`, 2026-11-27. An agent gets the folder an execution left and questions about what happened in it, written by a model that was not told what Ormaos records; its answers are graded against an oracle that reads neither the trace nor the recording.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

- **0.71**: `none`, mean score, 95% interval 0.59 to 0.83
- **0.87**: `raw`, mean score, 95% interval 0.79 to 0.95
- **0.93**: `ormaos`, mean score, 95% interval 0.88 to 0.97
- **0.95**: `ormaos-values`, mean score, 95% interval 0.90 to 0.99

## Method

### The questions: a writer that was not told about Ormaos

For each task, `claude-opus-5-5` wrote the questions once, in bubblewrap, in a folder that held only the source files of the program, its README, and what the execution printed (`stdout.txt`, `stderr.txt`). No input file, no file the execution wrote, no `.venv`, no `.ormaos`, no trace; nothing in the folder or in the prompt names Ormaos or says that the execution was recorded or traced. Where a README or the notebook spoke of Ormaos, those words were taken out for the writer. No question was edited, reworded or replaced. The prompt, after its first two sentences (what ran, what the folder holds):

The writer's prompt:

```text
Write 8 factual questions about what happened inside this execution that the output alone does not answer, each with one unambiguous answer and its expected format. Write them to questions.json in this folder: a JSON list of 8 objects, each with the keys "id" ("q1" to "q8"), "question" and "format".
```

The writers wrote 72 questions; 71 are kept. An agent gets each question with the writer's words and the writer's format. The writer's folder, prompt, transcript and questions are in [`agent-bench/knows2/writer/`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/writer).

### The oracle: one more execution, under sys.settrace

The answers come from one more execution of the same program, independent of the arms, under `sys.settrace`, with wrappers around `open` and `sqlite3.connect`. [`oracle.py`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/oracle.py) computes every answer from that trace and from the files that execution left. It never reads an Ormaos recording or a VizTracer trace.

### Rules written before any agent ran

Each question has a rule in [`rules.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/rules.json), written, with the oracle, before any agent ran: numbers equal in value, names compared by their last dotted part, lists in order or as sets, a word out of a few without regard to capitals, a number rounded to the decimals its format names. An answer is right or wrong as a whole. The score of a run is the share of the task's kept questions it got right. Every answer is counted as **right** (by the rule of its question), **null** (the agent wrote null) or **wrong** (not null, and the rule marks it wrong).

### The drop rule

A question is dropped only when the oracle cannot give one unambiguous answer to it: not because an arm cannot answer it, not because it is hard, not because of what any agent answered. Dropped:

- `ai-app`, q1, "On which TCP port on 127.0.0.1 did the model_server stand-in listen during this run?": the server listens on a free port the system picks (`("127.0.0.1", 0)`): the oracle's execution and the execution of each arm got different ports

### The sandbox

Each run copies the task's folder and mounts it at `/srv/<task>` inside bubblewrap, with nothing else of the machine but the system (`/usr` and `/etc`, read-only), the `claude` program and its login. `claude -p --model claude-opus-5-5 --safe-mode --strict-mcp-config` gets the prompt, with the tools Bash, Read, Grep, Glob, Edit and Write, and the runner's time limit. The network is not cut: the agent needs it to reach the model. The execution was played once per arm and once more for the oracle, in separate copies mounted at the same path, and the build stopped if the copies did not leave the same files.

### The first attempt counts

Every slot (task, arm, run) was run once, and every run counts: nothing was run again and nothing is left out. Runs that ended out of time, with an error, or without an `answers.json` that reads as JSON: 0.

### The arms

| Arm | Added to the folder | Added to the prompt |
|---|---|---|
| `none` | nothing | nothing |
| `raw` | `result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of the execution, default settings | that the file is there and how to read it |
| `ormaos` | `.ormaos/`: the recording of `ormaos run`, default settings, and the `ormaos` command line in `.venv/` | that the recording is there, and to run `.venv/bin/ormaos guide` first |
| `ormaos-values` | `.ormaos/`: the recording of `ormaos run --values`, and the same command line | the sentence of `ormaos`, with "values included" |

### Each arm's prompt, verbatim

The prompts of `data-pipeline`. The first sentence and the files taken out are the task's own; each task's section below has its four prompts.

`none`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Results

The score of a run is the share of the task's questions its `answers.json` got right. The interval is a 95% bootstrap interval of the mean over the runs of the arm (10,000 resamples), computed with the runner's own function.

**Mean score per arm, knows2.** The mean score of the runs of each arm, with its 95% bootstrap interval. none 0.71 (0.59 to 0.83); raw 0.87 (0.79 to 0.95); ormaos 0.93 (0.88 to 0.97); ormaos-values 0.95 (0.90 to 0.99).

| Arm | Runs | Mean score | 95% interval | Median wall time | Median tool calls | Median tokens | Ran the program again | Timed out |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `none` | 27 | 0.71 | 0.59 to 0.83 | 26 s | 4 | 52,196 | 7/27 | 0 |
| `raw` | 27 | 0.87 | 0.79 to 0.95 | 39 s | 5 | 75,290 | 3/27 | 0 |
| `ormaos` | 27 | 0.93 | 0.88 to 0.97 | 32 s | 5 | 101,359 | 4/27 | 0 |
| `ormaos-values` | 27 | 0.95 | 0.90 to 0.99 | 34 s | 6 | 126,028 | 0/27 | 0 |

**Right, null and wrong answers per arm.** Every answer of every run of each arm, stacked: right, null, wrong. none: 153 right, 60 null, 0 wrong; raw: 186 right, 27 null, 0 wrong; ormaos: 198 right, 14 null, 1 wrong; ormaos-values: 202 right, 11 null, 0 wrong.

| Arm | Answers | Right | Null | Wrong |
|---|---:|---:|---:|---:|
| `none` | 213 | 153 | 60 | 0 |
| `raw` | 213 | 186 | 27 | 0 |
| `ormaos` | 213 | 198 | 14 | 1 |
| `ormaos-values` | 213 | 202 | 11 | 0 |

Every wrong answer:

| Task | Arm | Run | Question | Answer | Oracle |
|---|---|---|---|---|---|
| web-backend | `ormaos` | 3 | q5 | `"17, 2880"` | `[8, 3660]` |

**Mean score per task and arm, knows2.** The mean score of the runs of each task and arm, from 0 (no question right) to 1 (all right). web-backend: none 1.00, raw 1.00, ormaos 0.96, ormaos-values 1.00. data-pipeline: none 0.25, raw 0.38, ormaos 0.88, ormaos-values 0.92. notebook: none 0.50, raw 0.62, ormaos 0.62, ormaos-values 0.62. ml-training: none 1.00, raw 1.00, ormaos 1.00, ormaos-values 1.00. rl-env: none 1.00, raw 1.00, ormaos 1.00, ormaos-values 1.00. ai-app: none 0.29, raw 0.86, ormaos 1.00, ormaos-values 1.00. agent-change: none 1.00, raw 1.00, ormaos 1.00, ormaos-values 1.00. order-sync: none 0.38, raw 1.00, ormaos 0.92, ormaos-values 1.00. freight-quote: none 1.00, raw 1.00, ormaos 1.00, ormaos-values 1.00.

| Task | Questions | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|---:|
| web-backend | 8 | 1.00 | 1.00 | 0.96 | 1.00 |
| data-pipeline | 8 | 0.25 | 0.38 | 0.88 | 0.92 |
| notebook | 8 | 0.50 | 0.62 | 0.62 | 0.62 |
| ml-training | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| rl-env | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| ai-app | 7 | 0.29 | 0.86 | 1.00 | 1.00 |
| agent-change | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| order-sync | 8 | 0.38 | 1.00 | 0.92 | 1.00 |
| freight-quote | 8 | 1.00 | 1.00 | 1.00 | 1.00 |

In 4 of 9 tasks every arm scored 1.00: `ml-training`, `rl-env`, `agent-change` and `freight-quote`.

**Median tokens per run, per arm.** Input, output and cache tokens added up, as the claude command line reports them; the median over the runs of each arm. none 52,196; raw 75,290; ormaos 101,359; ormaos-values 126,028.

| Arm | Median tokens |
|---|---:|
| `none` | 52,196 |
| `raw` | 75,290 |
| `ormaos` | 101,359 |
| `ormaos-values` | 126,028 |

**Median wall time per run, per arm.** From the start of the agent to its end, the median over the runs of each arm, in seconds. none 26.2 s; raw 39.2 s; ormaos 32.0 s; ormaos-values 33.6 s.

| Arm | Median wall time (s) |
|---|---:|
| `none` | 26.2 |
| `raw` | 39.2 |
| `ormaos` | 32.0 |
| `ormaos-values` | 33.6 |

Cost, as the claude command line reports it (`total_cost_usd`): $17.72 for 108 runs; mean per run, `none` $0.100, `raw` $0.170, `ormaos` $0.181, `ormaos-values` $0.205.

**Size of the trace and of the recording, per task.** What the raw arm and the two Ormaos arms add to the folder, in bytes, on a log scale: the VizTracer trace (`result.json`) and the `.ormaos/` folder. web-backend: raw 75.7 MB, ormaos 49.7 kB, ormaos-values 52.0 kB; data-pipeline: raw 51.4 MB, ormaos 13.5 kB, ormaos-values 14.4 kB; notebook: raw 123 MB, ormaos 34.1 kB, ormaos-values 41.6 kB; ml-training: raw 159 MB, ormaos 114 kB, ormaos-values 116 kB; rl-env: raw 710 kB, ormaos 516 kB, ormaos-values 582 kB; ai-app: raw 7.5 MB, ormaos 40.0 kB, ormaos-values 59.4 kB; agent-change: raw 2.8 MB, ormaos 80.4 kB, ormaos-values 94.5 kB; order-sync: raw 8.1 MB, ormaos 110 kB, ormaos-values 125 kB; freight-quote: raw 12.0 MB, ormaos 195 kB, ormaos-values 240 kB.

| Task | `raw` (bytes) | `ormaos` (bytes) | `ormaos-values` (bytes) |
|---|---:|---:|---:|
| web-backend | 75,736,352 | 49,715 | 51,991 |
| data-pipeline | 51,413,977 | 13,531 | 14,403 |
| notebook | 123,183,271 | 34,109 | 41,631 |
| ml-training | 158,799,770 | 113,969 | 116,341 |
| rl-env | 710,203 | 516,107 | 582,464 |
| ai-app | 7,523,641 | 39,998 | 59,446 |
| agent-change | 2,750,985 | 80,439 | 94,464 |
| order-sync | 8,064,939 | 109,541 | 125,277 |
| freight-quote | 12,009,753 | 195,302 | 239,816 |

## For web backends

A FastAPI service over a SQLite database of customers, products and orders, with one route that lists a customer's orders, each with its total. Source: [`use-cases/web-backend`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/web-backend).

The execution: `.venv/bin/python main.py` ran once in this folder.

Mean score: `none` 1.00, `raw` 1.00, `ormaos` 0.96, `ormaos-values` 1.00.

**Runs right per question and arm, web-backend.** For each question of web-backend, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 3/3, raw 3/3, ormaos 2/3, ormaos-values 3/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| q5 | 3/3 | 3/3 | 2/3 | 3/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. What customer name did the route put in the "customer" field of the response body it returned for this request?

Format: A single name exactly as stored in the database, e.g. "Name". The oracle: `"Clara"`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"Clara"` | right: `"Clara"` | right: `"Clara"` |
| `raw` | right: `"Clara"` | right: `"Clara"` | right: `"Clara"` |
| `ormaos` | right: `"Clara"` | right: `"Clara"` | right: `"Clara"` |
| `ormaos-values` | right: `"Clara"` | right: `"Clara"` | right: `"Clara"` |

### q2. What discount percentage did discount_for return for the requested customer during this request, and was it reached through the except KeyError branch?

Format: An integer followed by yes or no, e.g. "7, no". The oracle: `[0, true]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"0, yes"` | right: `"0, yes"` | right: `"0, yes"` |
| `raw` | right: `"0, yes"` | right: `"0, yes"` | right: `"0, yes"` |
| `ormaos` | right: `"0, yes"` | right: `"0, yes"` | right: `"0, yes"` |
| `ormaos-values` | right: `"0, yes"` | right: `"0, yes"` | right: `"0, yes"` |

### q3. What was the id of the first order in the "orders" list of the response?

Format: An integer. The oracle: `8`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `8` | right: `8` | right: `8` |
| `raw` | right: `8` | right: `8` | right: `8` |
| `ormaos` | right: `8` | right: `8` | right: `8` |
| `ormaos-values` | right: `8` | right: `8` | right: `8` |

### q4. What was the sum of the "total_cents" values across all orders in the response?

Format: An integer number of cents. The oracle: `18200`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `18200` | right: `18200` | right: `18200` |
| `raw` | right: `18200` | right: `18200` | right: `18200` |
| `ormaos` | right: `18200` | right: `18200` | right: `18200` |
| `ormaos-values` | right: `18200` | right: `18200` | right: `18200` |

### q5. Which order in the response had the largest "total_cents", and what was that value?

Format: Order id and total, as "id, cents" (two integers). The oracle: `[8, 3660]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"8, 3660"` | right: `"8, 3660"` | right: `"8, 3660"` |
| `raw` | right: `"8, 3660"` | right: `"8, 3660"` | right: `"8, 3660"` |
| `ormaos` | right: `"8, 3660"` | right: `"8, 3660"` | wrong: `"17, 2880"` |
| `ormaos-values` | right: `"8, 3660"` | right: `"8, 3660"` | right: `"8, 3660"` |

### q6. How many times was price_of called while the request was handled?

Format: An integer. The oracle: `24`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `24` | right: `24` | right: `24` |
| `raw` | right: `24` | right: `24` | right: `24` |
| `ormaos` | right: `24` | right: `24` | right: `24` |
| `ormaos-values` | right: `24` | right: `24` | right: `24` |

### q7. In total, how many SQL statements were run with db.execute on the request's database connection while list_orders handled the request (counting find_customer, the orders query, items_of, price_of and product_names calls)?

Format: An integer. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

### q8. How many rows did store.create() insert into the order_items table when it rebuilt orders.db before the request?

Format: An integer. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

**The four prompts of web-backend**

`none`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For data pipelines

A monthly report made with pandas from two exports: it drops the orders without an amount and repeated order numbers, joins each order to its customer and sums the amounts by region. Source: [`use-cases/data-pipeline`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/data-pipeline).

The execution: `.venv/bin/python pipeline.py` ran once in this folder. Taken out of the folder afterwards: `orders.csv` and `customers.csv`.

Mean score: `none` 0.25, `raw` 0.38, `ormaos` 0.88, `ormaos-values` 0.92.

**Runs right per question and arm, data-pipeline.** For each question of data-pipeline, how many of the runs of each arm got it right. q1: none 0/3, raw 0/3, ormaos 3/3, ormaos-values 3/3. q2: none 0/3, raw 0/3, ormaos 3/3, ormaos-values 3/3. q3: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 0/3, raw 0/3, ormaos 3/3, ormaos-values 3/3. q5: none 0/3, raw 0/3, ormaos 3/3, ormaos-values 3/3. q6: none 0/3, raw 0/3, ormaos 0/3, ormaos-values 1/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 0/3 | 0/3 | 3/3 | 3/3 |
| q2 | 0/3 | 0/3 | 3/3 | 3/3 |
| q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| q4 | 0/3 | 0/3 | 3/3 | 3/3 |
| q5 | 0/3 | 0/3 | 3/3 | 3/3 |
| q6 | 0/3 | 0/3 | 0/3 | 1/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. How many rows did the orders DataFrame have right after load_orders read orders.csv, before any filtering?

Format: A non-negative integer, e.g. 200. The oracle: `200`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | right: `200` | right: `200` | right: `200` |
| `ormaos-values` | right: `200` | right: `200` | right: `200` |

### q2. How many order rows did drop_unpriced remove because their amount was missing (NaN)?

Format: A non-negative integer, e.g. 3. The oracle: `5`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | right: `5` | right: `5` | right: `5` |
| `ormaos-values` | right: `5` | right: `5` | right: `5` |

### q3. Was drop_repeats actually called during this run, i.e. did orders['order_id'].duplicated().any() evaluate to True after the unpriced orders were dropped?

Format: "yes" or "no". The oracle: `false`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `"no"` | right: `"no"` | right: `"no"` |
| `ormaos` | right: `"no"` | right: `"no"` | right: `"no"` |
| `ormaos-values` | right: `"no"` | right: `"no"` | right: `"no"` |

### q4. How many rows did the orders DataFrame have immediately before being passed to join_customers (after drop_unpriced and, if it ran, drop_repeats)?

Format: A non-negative integer, e.g. 195. The oracle: `195`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | right: `195` | right: `195` | right: `195` |
| `ormaos-values` | right: `195` | right: `195` | right: `195` |

### q5. How many rows did the joined DataFrame returned by join_customers (inner merge on customer_id) have?

Format: A non-negative integer, e.g. 190. The oracle: `178`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | right: `178` | right: `178` | right: `178` |
| `ormaos-values` | right: `178` | right: `178` | right: `178` |

### q6. How many order rows that reached join_customers were lost in the inner merge because their customer_id had no match in customers.csv?

Format: A non-negative integer, e.g. 0. The oracle: `17`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | null | null | null |
| `ormaos-values` | null | right: `17` | null |

### q7. Which region appears in the first data row of report.csv (the alphabetically first region after sorting), and what is its total amount as written?

Format: Region name and amount separated by a comma, e.g. "North, 12345.67". The oracle: `["east", 4349.29]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"east, 4349.29"` | right: `"east, 4349.29"` | right: `"east, 4349.29"` |
| `raw` | right: `"east, 4349.29"` | right: `"east, 4349.29"` | right: `"east, 4349.29"` |
| `ormaos` | right: `"east, 4349.29"` | right: `"east, 4349.29"` | right: `"east, 4349.29"` |
| `ormaos-values` | right: `"east, 4349.29"` | right: `"east, 4349.29"` | right: `"east, 4349.29"` |

### q8. What is the sum of the amount column over all 4 rows of the report written to report.csv?

Format: A decimal number rounded to 2 decimal places, e.g. 48210.55. The oracle: `17182.34`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `17182.34` | right: `17182.34` | right: `17182.34` |
| `raw` | right: `17182.34` | right: `17182.34` | right: `17182.34` |
| `ormaos` | right: `17182.34` | right: `17182.34` | right: `17182.34` |
| `ormaos-values` | right: `17182.34` | right: `17182.34` | right: `17182.34` |

**The four prompts of data-pipeline**

`none`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For notebooks

A Jupyter notebook that reads the sales of the week, leaves out single sales above a limit, adds tax and sums the week; its cells ran in the order of their saved execution counts. Source: [`use-cases/notebook`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/notebook).

The execution: The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. Taken out of the folder afterwards: `sales.csv`.

Mean score: `none` 0.50, `raw` 0.62, `ormaos` 0.62, `ormaos-values` 0.62.

**Runs right per question and arm, notebook.** For each question of notebook, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 0/3, raw 0/3, ormaos 0/3, ormaos-values 0/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 0/3, raw 0/3, ormaos 0/3, ormaos-values 0/3. q8: none 0/3, raw 0/3, ormaos 0/3, ormaos-values 0/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| q5 | 0/3 | 0/3 | 0/3 | 0/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 0/3 | 0/3 | 0/3 | 0/3 |
| q8 | 0/3 | 0/3 | 0/3 | 0/3 |

### q1. How many rows did load("sales.csv") return in this execution, i.e. what was len(rows) right after the cell with id cell-2 ran?

Format: integer, e.g. 37. The oracle: `40`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `40` | right: `40` | right: `40` |
| `raw` | right: `40` | right: `40` | right: `40` |
| `ormaos` | right: `40` | right: `40` | right: `40` |
| `ormaos-values` | right: `40` | right: `40` | right: `40` |

### q2. Following the saved execution counts, which code cell (by cell id) was the third one executed in the kernel?

Format: a cell id string, e.g. cell-3. The oracle: `"cell-4"`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"cell-4"` | right: `"cell-4"` | right: `"cell-4"` |
| `raw` | right: `"cell-4"` | right: `"cell-4"` | right: `"cell-4"` |
| `ormaos` | right: `"cell-4"` | right: `"cell-4"` | right: `"cell-4"` |
| `ormaos-values` | right: `"cell-4"` | right: `"cell-4"` | right: `"cell-4"` |

### q3. When drop_key_accounts compared each row's price to LIMIT in this execution, was that price the original price from sales.csv or the price with 20% tax already added?

Format: one of: pre-tax, tax-inclusive. The oracle: `"tax-inclusive"`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"tax-inclusive"` | right: `"tax-inclusive"` | right: `"tax-inclusive"` |
| `raw` | right: `"tax-inclusive"` | right: `"tax-inclusive"` | right: `"tax-inclusive"` |
| `ormaos` | right: `"tax-inclusive"` | right: `"tax-inclusive"` | right: `"tax-inclusive"` |
| `ormaos-values` | right: `"tax-inclusive"` | right: `"tax-inclusive"` | right: `"tax-inclusive"` |

### q4. How many rows were left in rows after drop_key_accounts(rows) returned in this execution?

Format: integer, e.g. 31. The oracle: `22`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `22` | right: `22` | right: `22` |
| `ormaos` | right: `22` | right: `22` | right: `22` |
| `ormaos-values` | right: `22` | right: `22` | right: `22` |

### q5. How many rows had an original price of at most 1000 in sales.csv but were still removed by drop_key_accounts in this execution, because their price had been increased by the tax before the filter ran?

Format: integer, e.g. 4. The oracle: `12`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | null | null | null |
| `ormaos-values` | null | null | null |

### q6. What value did the variable week hold at the end of the execution, rounded to two decimal places?

Format: decimal number with exactly two decimals, e.g. 12345.67. The oracle: `15602.4`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"15602.40"` | right: `"15602.40"` | right: `"15602.40"` |
| `raw` | right: `"15602.40"` | right: `"15602.40"` | right: `15602.4` |
| `ormaos` | right: `15602.4` | right: `"15602.40"` | right: `"15602.40"` |
| `ormaos-values` | right: `"15602.40"` | right: `"15602.40"` | right: `15602.4` |

### q7. What was the highest price among the rows that remained in rows at the end of the execution (the tax-inclusive price used in the final total)?

Format: decimal number with exactly two decimals, e.g. 999.60. The oracle: `936.0`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | null | null | null |
| `ormaos-values` | null | null | null |

### q8. What was the sum of the quantity field over all rows that remained in rows at the end of the execution?

Format: integer, e.g. 120. The oracle: `42`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | null | null | null |
| `ormaos-values` | null | null | null |

**The four prompts of notebook**

`none`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For ML training

A PyTorch model trained on CPU that predicts how long a delivery takes, on data made from a seed; each batch is standardized, and a batch whose loss is not finite is left out. Source: [`use-cases/ml-training`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/ml-training).

The execution: `.venv/bin/python train.py` ran once in this folder.

Mean score: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00.

**Runs right per question and arm, ml-training.** For each question of ml-training, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. Of the 40 batches counted in the printed "trained 40 steps", how many actually produced an Adam optimizer update (optimizer.step() called)?

Format: integer. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

### q2. How many batches were skipped because their loss was not a finite number?

Format: integer. The oracle: `2`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `2` | right: `2` | right: `2` |
| `raw` | right: `2` | right: `2` | right: `2` |
| `ormaos` | right: `2` | right: `2` | right: `2` |
| `ormaos-values` | right: `2` | right: `2` | right: `2` |

### q3. Which batches were skipped because of a non-finite loss? Give their 0-based positions in the order the batches were processed.

Format: JSON list of integers in ascending order, e.g. [3, 17]. The oracle: `[10, 11]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `[10, 11]` | right: `[10, 11]` | right: `[10, 11]` |
| `raw` | right: `[10, 11]` | right: `[10, 11]` | right: `[10, 11]` |
| `ormaos` | right: `[10, 11]` | right: `[10, 11]` | right: `[10, 11]` |
| `ormaos-values` | right: `[10, 11]` | right: `[10, 11]` | right: `[10, 11]` |

### q4. Which input feature column caused the skipped batches' losses to be non-finite, because its standard deviation within the batch was zero?

Format: one of: distance, parcels, hour, weekend. The oracle: `"weekend"`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"weekend"` | right: `"weekend"` | right: `"weekend"` |
| `raw` | right: `"weekend"` | right: `"weekend"` | right: `"weekend"` |
| `ormaos` | right: `"weekend"` | right: `"weekend"` | right: `"weekend"` |
| `ormaos-values` | right: `"weekend"` | right: `"weekend"` | right: `"weekend"` |

### q5. Across all 320 generated rows, how many rows have the weekend flag set to 1.0?

Format: integer. The oracle: `92`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `92` | right: `92` | right: `92` |
| `raw` | right: `92` | right: `92` | right: `92` |
| `ormaos` | right: `92` | right: `92` | right: `92` |
| `ormaos-values` | right: `92` | right: `92` | right: `92` |

### q6. The printed "last loss 379.2" is the loss of which batch? Give its 0-based position in the order the batches were processed.

Format: integer. The oracle: `39`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `39` | right: `39` | right: `39` |
| `raw` | right: `39` | right: `39` | right: `39` |
| `ormaos` | right: `39` | right: `39` | right: `39` |
| `ormaos-values` | right: `39` | right: `39` | right: `39` |

### q7. In the batches that were skipped, what single value did the weekend flag take for all 8 rows?

Format: number with one decimal, e.g. 0.0. The oracle: `0.0`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `0.0` | right: `0.0` | right: `0.0` |
| `raw` | right: `0.0` | right: `0.0` | right: `0.0` |
| `ormaos` | right: `0.0` | right: `0.0` | right: `0.0` |
| `ormaos-values` | right: `0.0` | right: `0.0` | right: `0.0` |

### q8. How many of the 40 batches had a weekend flag that varied across their 8 rows (i.e. contained both 0.0 and 1.0)?

Format: integer. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

**The four prompts of ml-training**

`none`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For RL environments

A grid world in pure Python, where a courier walks from a depot to a customer, and a loop that runs episodes of it with a seeded policy. Source: [`use-cases/rl-env`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/rl-env).

The execution: `python3 run.py` ran once in this folder.

Mean score: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00.

**Runs right per question and arm, rl-env.** For each question of rl-env, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. Of the 20 episodes, how many ended with the courier at the customer at (5, 5), as opposed to ending because the 30-step limit was reached?

Format: An integer, e.g. 7. The oracle: `19`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `19` | right: `19` | right: `19` |
| `raw` | right: `19` | right: `19` | right: `19` |
| `ormaos` | right: `19` | right: `19` | right: `19` |
| `ormaos-values` | right: `19` | right: `19` | right: `19` |

### q2. How many times during the whole execution did GridEnv._arrival_bonus() get called (that is, how many times was the 10.0 arrival reward actually given out)?

Format: An integer, e.g. 7. The oracle: `0`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `0` | right: `0` | right: `0` |
| `raw` | right: `0` | right: `0` | right: `0` |
| `ormaos` | right: `0` | right: `0` | right: `0` |
| `ormaos-values` | right: `0` | right: `0` | right: `0` |

### q3. What was the value of env.bumps (the counter of moves blocked by a wall or the grid edge) after all 20 episodes had finished?

Format: An integer, e.g. 7. The oracle: `89`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `89` | right: `89` | right: `89` |
| `raw` | right: `89` | right: `89` | right: `89` |
| `ormaos` | right: `89` | right: `89` | right: `89` |
| `ormaos-values` | right: `89` | right: `89` | right: `89` |

### q4. What was the total number of env.step() calls made over all 20 episodes combined?

Format: An integer, e.g. 7. The oracle: `363`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `363` | right: `363` | right: `363` |
| `raw` | right: `363` | right: `363` | right: `363` |
| `ormaos` | right: `363` | right: `363` | right: `363` |
| `ormaos-values` | right: `363` | right: `363` | right: `363` |

### q5. Which episode, counting from 1, ended because the 30-step limit was reached rather than at the customer?

Format: An integer episode number from 1 to 20, e.g. 7. The oracle: `13`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `13` | right: `13` | right: `13` |
| `raw` | right: `13` | right: `13` | right: `13` |
| `ormaos` | right: `13` | right: `13` | right: `13` |
| `ormaos-values` | right: `13` | right: `13` | right: `13` |

### q6. How many steps did the shortest episode of the run take?

Format: An integer, e.g. 7. The oracle: `13`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `13` | right: `13` | right: `13` |
| `raw` | right: `13` | right: `13` | right: `13` |
| `ormaos` | right: `13` | right: `13` | right: `13` |
| `ormaos-values` | right: `13` | right: `13` | right: `13` |

### q7. How many times in the whole run did the policy function choose() return the action "right"?

Format: An integer, e.g. 7. The oracle: `162`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `162` | right: `162` | right: `162` |
| `raw` | right: `162` | right: `162` | right: `162` |
| `ormaos` | right: `162` | right: `162` | right: `162` |
| `ormaos-values` | right: `162` | right: `162` | right: `162` |

### q8. What was the highest total return of any single episode in the run?

Format: A decimal number rounded to one decimal place, e.g. -3.4. The oracle: `-6.7`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `-6.7` | right: `-6.7` | right: `-6.7` |
| `raw` | right: `-6.7` | right: `-6.7` | right: `-6.7` |
| `ormaos` | right: `-6.7` | right: `-6.7` | right: `-6.7` |
| `ormaos-values` | right: `-6.7` | right: `-6.7` | right: `-6.7` |

**The four prompts of rl-env**

`none`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For AI apps

An app that sends each support ticket to a model API, a local stand-in with a small and a large model, and keeps a one-sentence summary of each ticket. Source: [`use-cases/ai-app`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/ai-app).

The execution: `python3 app.py` ran once in this folder. Taken out of the folder afterwards: `tickets.json`.

Mean score: `none` 0.29, `raw` 0.86, `ormaos` 1.00, `ormaos-values` 1.00.

**Runs right per question and arm, ai-app.** For each question of ai-app, how many of the runs of each arm got it right. q2: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q6: none 0/3, raw 0/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q2 | 0/3 | 3/3 | 3/3 | 3/3 |
| q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| q5 | 0/3 | 3/3 | 3/3 | 3/3 |
| q6 | 0/3 | 0/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q2. How many of the tickets got their summary from the small-1 model, without falling back to large-1?

Format: An integer between 0 and 8. The oracle: `5`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `5` | right: `5` | right: `5` |
| `ormaos` | right: `5` | right: `5` | right: `5` |
| `ormaos-values` | right: `5` | right: `5` | right: `5` |

### q3. How many HTTP 503 ('model overloaded') responses did the model server send during the run?

Format: An integer. The oracle: `3`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `3` | right: `3` | right: `3` |
| `ormaos` | right: `3` | right: `3` | right: `3` |
| `ormaos-values` | right: `3` | right: `3` | right: `3` |

### q4. How many POST requests in total did app.py send to the model server, counting both small-1 and large-1 calls?

Format: An integer. The oracle: `11`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `11` | right: `11` | right: `11` |
| `ormaos` | right: `11` | right: `11` | right: `11` |
| `ormaos-values` | right: `11` | right: `11` | right: `11` |

### q5. What are the ids of the tickets whose summary came from the large-1 model, in the order they were processed?

Format: A JSON list of the ticket ids exactly as they appear in tickets.json, e.g. [3, 7]; [] if none. The oracle: `[403, 405, 408]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `[403, 405, 408]` | right: `[403, 405, 408]` | right: `[403, 405, 408]` |
| `ormaos` | right: `[403, 405, 408]` | right: `[403, 405, 408]` | right: `[403, 405, 408]` |
| `ormaos-values` | right: `[403, 405, 408]` | right: `[403, 405, 408]` | right: `[403, 405, 408]` |

### q6. What was the length, in characters, of the longest prompt (instruction plus ticket text) that app.py sent in this run?

Format: An integer. The oracle: `665`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | null | null | null |
| `ormaos` | right: `665` | right: `665` | right: `665` |
| `ormaos-values` | right: `665` | right: `665` | right: `665` |

### q7. What summary text was written to summaries.json for the first ticket in tickets.json?

Format: The exact summary string, without surrounding quotes. The oracle: `"The invoice of October shows the old address."`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` |
| `raw` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` |
| `ormaos` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` |
| `ormaos-values` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` | right: `"The invoice of October shows the old address."` |

### q8. What was the size, in bytes, of the summaries.json file that this run wrote?

Format: An integer. The oracle: `703`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `703` | right: `703` | right: `703` |
| `raw` | right: `703` | right: `703` | right: `703` |
| `ormaos` | right: `703` | right: `703` | right: `703` |
| `ormaos-values` | right: `703` | right: `703` | right: `703` |

**The four prompts of ai-app**

`none`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For changes made by an agent

A small billing tool in a git repository that writes invoices and refunds, run at each of two commits: before and after a change that a coding agent made. Source: [`use-cases/agent-change`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/agent-change).

The execution: This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2).

Mean score: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00.

**Runs right per question and arm, agent-change.** For each question of agent-change, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. In r1, how many times in total was billing.line_price called (counting calls from both invoice_total and refund_amount)?

Format: A single integer, e.g. 42. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

### q2. In r2, how many times was tiers.json opened during the execution?

Format: A single integer, e.g. 42. The oracle: `38`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `38` | right: `38` | right: `38` |
| `raw` | right: `38` | right: `38` | right: `38` |
| `ormaos` | right: `38` | right: `38` | right: `38` |
| `ormaos-values` | right: `38` | right: `38` | right: `38` |

### q3. In r1, what was the sum of the total_cents values over all 12 rows written to invoices.csv?

Format: A single integer number of cents, e.g. 123456. The oracle: `44270`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `44270` | right: `44270` | right: `44270` |
| `raw` | right: `44270` | right: `44270` | right: `44270` |
| `ormaos` | right: `44270` | right: `44270` | right: `44270` |
| `ormaos-values` | right: `44270` | right: `44270` | right: `44270` |

### q4. In r2, what was the sum of the total_cents values over all 12 rows written to invoices.csv?

Format: A single integer number of cents, e.g. 123456. The oracle: `41868`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `41868` | right: `41868` | right: `41868` |
| `raw` | right: `41868` | right: `41868` | right: `41868` |
| `ormaos` | right: `41868` | right: `41868` | right: `41868` |
| `ormaos-values` | right: `41868` | right: `41868` | right: `41868` |

### q5. Of the 12 orders, how many had a different total_cents in r2's invoices.csv than in r1's invoices.csv?

Format: A single integer from 0 to 12. The oracle: `9`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `9` | right: `9` | right: `9` |
| `raw` | right: `9` | right: `9` | right: `9` |
| `ormaos` | right: `9` | right: `9` | right: `9` |
| `ormaos-values` | right: `9` | right: `9` | right: `9` |

### q6. In r2, how many of the calls to billing.discount_percent returned 10 (i.e. the customer was looked up as a gold tier)?

Format: A single integer, e.g. 7. The oracle: `21`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `21` | right: `21` | right: `21` |
| `raw` | right: `21` | right: `21` | right: `21` |
| `ormaos` | right: `21` | right: `21` | right: `21` |
| `ormaos-values` | right: `21` | right: `21` | right: `21` |

### q7. In r2, in how many calls to billing.line_price was the integer division by 100 inexact, i.e. unit_cents * quantity * (100 - discount) was not a multiple of 100, so cents were truncated?

Format: A single integer, e.g. 3. The oracle: `1`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `1` | right: `1` | right: `1` |
| `raw` | right: `1` | right: `1` | right: `1` |
| `ormaos` | right: `1` | right: `1` | right: `1` |
| `ormaos-values` | right: `1` | right: `1` | right: `1` |

### q8. What were the three refund_cents values written to refunds.csv in r2, in the order the rows were written?

Format: Three integers separated by commas, in row order, e.g. 1200,450,9900. The oracle: `[228, 1620, 1575]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"228,1620,1575"` | right: `"228,1620,1575"` | right: `"228,1620,1575"` |
| `raw` | right: `"228,1620,1575"` | right: `"228,1620,1575"` | right: `"228,1620,1575"` |
| `ormaos` | right: `"228,1620,1575"` | right: `"228,1620,1575"` | right: `"228,1620,1575"` |
| `ormaos-values` | right: `"228,1620,1575"` | right: `"228,1620,1575"` | right: `"228,1620,1575"` |

**The four prompts of agent-change**

`none`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of each execution is in result-r1.json and result-r2.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. Those executions were recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. Those executions were recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For scheduled jobs: order-sync

A scheduled job that applies the new orders of a sales system to a warehouse inventory; the execution is a night on which it printed its OK line and some orders did not reach the inventory. Source: [`order-sync`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/order-sync).

The execution: Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's.

Mean score: `none` 0.38, `raw` 1.00, `ormaos` 0.92, `ormaos-values` 1.00.

**Runs right per question and arm, order-sync.** For each question of order-sync, how many of the runs of each arm got it right. q1: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 0/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 0/3, raw 3/3, ormaos 2/3, ormaos-values 3/3. q6: none 0/3, raw 3/3, ormaos 2/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 0/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| q5 | 0/3 | 3/3 | 2/3 | 3/3 |
| q6 | 0/3 | 3/3 | 2/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. How many order rows did the sales API's GET /orders return to the job in this run (the number of orders parsed, len(orders) in job.main)?

Format: A non-negative integer, e.g. 42. The oracle: `26`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `26` | right: `26` | right: `26` |
| `ormaos` | right: `26` | right: `26` | right: `26` |
| `ormaos-values` | right: `26` | right: `26` | right: `26` |

### q2. How many orders were newly applied to the inventory in this run, i.e. for how many orders did inventory.apply_order return True and insert a row into applied_orders?

Format: A non-negative integer, e.g. 37. The oracle: `19`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `19` | right: `19` | right: `19` |
| `raw` | right: `19` | right: `19` | right: `19` |
| `ormaos` | right: `19` | right: `19` | right: `19` |
| `ormaos-values` | right: `19` | right: `19` | right: `19` |

### q3. How many orders were passed over without error because an earlier run had already applied their order_id (inventory.apply_order returned False)?

Format: A non-negative integer, e.g. 3. The oracle: `2`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `2` | right: `2` | right: `2` |
| `ormaos` | right: `2` | right: `2` | right: `2` |
| `ormaos-values` | right: `2` | right: `2` | right: `2` |

### q4. How many orders were skipped because an exception was raised for them inside sync_orders (validation failure, unknown SKU, or any other error), each of which produced an 'order ... skipped' warning that the default ERROR log level suppressed?

Format: A non-negative integer, e.g. 2. The oracle: `5`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `5` | right: `5` | right: `5` |
| `ormaos` | right: `5` | right: `5` | right: `5` |
| `ormaos-values` | right: `5` | right: `5` | right: `5` |

### q5. What are the order_ids of the orders skipped because of an exception in sync_orders (the orders counted in q4)?

Format: A JSON list of order_id strings sorted in ascending lexicographic order, e.g. ["A-1007", "A-1012"]; [] if none. The oracle: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| `ormaos` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` | null | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| `ormaos-values` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` | right: `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |

### q6. For each skipped order (the orders counted in q4), which exception class caused it to be skipped?

Format: A JSON object mapping each skipped order_id to the exception class name, e.g. {"A-1007": "SkuFormatError", "A-1012": "UnknownSkuError"}; {} if none. The oracle: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | null | null | null |
| `raw` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| `ormaos` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` | null | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| `ormaos-values` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` | right: `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |

### q7. How many single items in total were taken out of stock in this run, i.e. the sum of the 'taken' quantity over all orders newly applied in this run (after pack-to-item conversion and capping at the stock on hand)?

Format: A non-negative integer, e.g. 318. The oracle: `104`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `104` | right: `104` | right: `104` |
| `raw` | right: `104` | right: `104` | right: `104` |
| `ormaos` | right: `104` | right: `104` | right: `104` |
| `ormaos-values` | right: `104` | right: `104` | right: `104` |

### q8. How many back-order rows did this run insert into the backorders table, and how many items did they add up to in total?

Format: Two non-negative integers separated by a comma: rows,items, e.g. 2,15. The oracle: `[2, 5]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"2,5"` | right: `"2,5"` | right: `"2,5"` |
| `raw` | right: `"2,5"` | right: `"2,5"` | right: `"2,5"` |
| `ormaos` | right: `"2,5"` | right: `"2,5"` | right: `"2,5"` |
| `ormaos-values` | right: `"2,5"` | right: `"2,5"` | right: `"2,5"` |

**The four prompts of order-sync**

`none`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## For scheduled jobs: freight-quote

A scheduled job that asks a carrier's rate API for the freight of tomorrow's shipments and writes one quote per shipment; the execution is a night on which some calls were refused. Source: [`freight-quote`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/freight-quote).

The execution: Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again.

Mean score: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00.

**Runs right per question and arm, freight-quote.** For each question of freight-quote, how many of the runs of each arm got it right. q1: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q2: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q3: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q4: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q5: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q6: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q7: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3. q8: none 3/3, raw 3/3, ormaos 3/3, ormaos-values 3/3.

| Question | `none` | `raw` | `ormaos` | `ormaos-values` |
|---|---:|---:|---:|---:|
| q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| q8 | 3/3 | 3/3 | 3/3 | 3/3 |

### q1. How many quote rows did the run write to the quotes table (that is, how many shipments were on the dispatch list it read)?

Format: A non-negative integer, e.g. 42. The oracle: `26`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `26` | right: `26` | right: `26` |
| `raw` | right: `26` | right: `26` | right: `26` |
| `ormaos` | right: `26` | right: `26` | right: `26` |
| `ormaos-values` | right: `26` | right: `26` | right: `26` |

### q2. For how many shipments was the written amount_cents the carrier stand-in's answer (an HTTP 200 from /v1/rates), not a price from the contract rate card?

Format: A non-negative integer, e.g. 37. The oracle: `9`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `9` | right: `9` | right: `9` |
| `raw` | right: `9` | right: `9` | right: `9` |
| `ormaos` | right: `9` | right: `9` | right: `9` |
| `ormaos-values` | right: `9` | right: `9` | right: `9` |

### q3. For how many shipments did the carrier call fail, so that job.price silently fell back to ratecard.rate (the warning was not printed because the log level defaults to ERROR)?

Format: A non-negative integer, e.g. 5. The oracle: `17`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `17` | right: `17` | right: `17` |
| `raw` | right: `17` | right: `17` | right: `17` |
| `ormaos` | right: `17` | right: `17` | right: `17` |
| `ormaos-values` | right: `17` | right: `17` | right: `17` |

### q4. How many of the run's rate requests did the stand-in refuse with HTTP 429 because the account's calls_used_today had reached calls_per_day?

Format: A non-negative integer, e.g. 3. The oracle: `17`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `17` | right: `17` | right: `17` |
| `raw` | right: `17` | right: `17` | right: `17` |
| `ormaos` | right: `17` | right: `17` | right: `17` |
| `ormaos-values` | right: `17` | right: `17` | right: `17` |

### q5. What was the shipment_id of the first shipment, in dispatch-list order, whose quote came from the contract rate card instead of the carrier?

Format: A single shipment_id string exactly as written in the dispatch list, or the string "none" if every quote came from the carrier. The oracle: `"FR-8136"`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `"FR-8136"` | right: `"FR-8136"` | right: `"FR-8136"` |
| `raw` | right: `"FR-8136"` | right: `"FR-8136"` | right: `"FR-8136"` |
| `ormaos` | right: `"FR-8136"` | right: `"FR-8136"` | right: `"FR-8136"` |
| `ormaos-values` | right: `"FR-8136"` | right: `"FR-8136"` | right: `"FR-8136"` |

### q6. Which shipments were refused by the stand-in with HTTP 422 (chargeable weight above 1000 kg) and therefore quoted from the rate card?

Format: A JSON list of shipment_id strings in dispatch-list order, e.g. ["S-104", "S-131"]; [] if none. The oracle: `[]`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `[]` | right: `[]` | right: `[]` |
| `raw` | right: `[]` | right: `[]` | right: `[]` |
| `ormaos` | right: `[]` | right: `[]` | right: `[]` |
| `ormaos-values` | right: `[]` | right: `[]` | right: `[]` |

### q7. By how much did the run increase calls_used_today in data/carrier.json (each request with the right account and quota left counts, including ones then refused with 404 or 422)?

Format: A non-negative integer, e.g. 40. The oracle: `9`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `9` | right: `9` | right: `9` |
| `raw` | right: `9` | right: `9` | right: `9` |
| `ormaos` | right: `9` | right: `9` | right: `9` |
| `ormaos-values` | right: `9` | right: `9` | right: `9` |

### q8. What was the sum of amount_cents over all quote rows the run wrote to the quotes table?

Format: A non-negative integer number of euro cents, e.g. 1234567. The oracle: `114835`.

| Arm | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `none` | right: `114835` | right: `114835` | right: `114835` |
| `raw` | right: `114835` | right: `114835` | right: `114835` |
| `ormaos` | right: `114835` | right: `114835` | right: `114835` |
| `ormaos-values` | right: `114835` | right: `114835` | right: `114835` |

**The four prompts of freight-quote**

`none`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## What the agents said when they could not answer

Run 1 of every task and arm, always run 1: 36 runs, of which 11 wrote null for at least one question. For each of them, the last message the agent wrote, quoted from its stream as it is.

### data-pipeline, `none`, run 1: null for q1, q2, q3, q4, q5, q6

The agent's last message, from [`streams/data-pipeline-none-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-none-1.jsonl):

```text
I wrote `answers.json`, but only two of the eight questions could be answered. The other six are `null`.

**Answered, from `report.csv`:**
- **q7:** `"east, 4349.29"`. "east" is the first data row after sorting by region.
- **q8:** `17182.34`. That is 4349.29 + 2567.98 + 6196.49 + 4068.58, the four region totals.

**`null`, q1–q6:** These need row counts from inside the run: rows loaded, rows dropped for a missing amount, whether repeated order IDs were dropped, and rows lost in the join. `orders.csv` and `customers.csv` are gone. The script logs nothing beyond its one-line summary, and I couldn't find any log, cache or leftover output on the system that records these counts.

The README says the orders export holds "200 orders of October", but I didn't use that for q1. It describes the usual export, not the file this run actually read. If that file had repeated order IDs, it would have had more than 200 rows.
```

### data-pipeline, `raw`, run 1: null for q1, q2, q4, q5, q6

The agent's last message, from [`streams/data-pipeline-raw-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-raw-1.jsonl):

```text
I wrote `answers.json`. Three answers come from what the run left behind; the five row-count questions are `null`, because nothing left in the folder records them.

| id | answer | source |
|---|---|---|
| q1 | null | row count after load not recorded |
| q2 | null | number of rows dropped not recorded |
| q3 | "no" | the trace has calls to `load_orders`, `load_customers`, `drop_unpriced`, `join_customers`, `revenue_by_region` and `write_report`, but none to `drop_repeats`, so the duplicate check was False |
| q4 | null | not recorded |
| q5 | null | not recorded |
| q6 | null | not recorded |
| q7 | "east, 4349.29" | first data row of `report.csv` |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why the row counts are null:** the trace only has function names, start times and durations, with no arguments or return values. pandas reads, filters and merges the rows in compiled code, so no traced call repeats once per row that I could count. The README says the orders file has "200 orders", but that describes the export in general, not the file this run read. So I didn't use it for q1.
```

### data-pipeline, `ormaos`, run 1: null for q6

The agent's last message, from [`streams/data-pipeline-ormaos-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl):

```text
I wrote `answers.json`. Seven answers come from the Ormaos recording (`r1`) and `report.csv`; one is null because the recording can't settle it.

| id | answer | where it comes from |
|---|---|---|
| q1 | 200 | `load_orders` returned 200 rows × 4 columns |
| q2 | 5 | `amount` had 5 nulls; `drop_unpriced` turned 200 rows into 195 |
| q3 | "no" | there was no call to `drop_repeats` in the recording; `main` called only `load_orders`, `load_customers`, `drop_unpriced`, `join_customers`, `revenue_by_region` and `write_report` |
| q4 | 195 | `join_customers` received 195 rows |
| q5 | 178 | `join_customers` returned 178 rows × 6 columns |
| q6 | null | see below |
| q7 | "east, 4349.29" | first data row of `report.csv` |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why q6 is null:** the merge went from 195 rows to 178, a drop of 17. That drop equals the number of unmatched orders only if each `customer_id` appears once in `customers.csv`. If an ID appeared twice, the inner merge would duplicate those orders, and more than 17 could have been lost. Ormaos records the row count, column types and nulls of the customers table (40 rows, no nulls), but not its values. So whether the IDs were unique can't be checked, and `customers.csv` is no longer here. If you know the IDs are unique, the answer is 17.

The run wrote `report.csv` (it shows as opened for writing at `pipeline.py:37`), so the file in the folder is the one that run produced. That backs up q7 and q8.
```

### data-pipeline, `ormaos-values`, run 1: null for q6

The agent's last message, from [`streams/data-pipeline-ormaos-values-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl):

```text
I wrote `answers.json` with seven answers taken from the Ormaos recording (`r1`, which finished with exit code 0) and `report.csv`. I left one answer, q6, as null.

| id | answer | source |
|---|---|---|
| q1 | 200 | `load_orders` returned a frame of 200 rows × 4 columns |
| q2 | 5 | `amount` had 5 nulls; `drop_unpriced` went from 200 rows to 195, with 0 nulls left |
| q3 | "no" | there's no `drop_repeats` call in the recorded call tree |
| q4 | 195 | the `orders` argument to `join_customers` had 195 rows |
| q5 | 178 | `join_customers` returned 178 rows × 6 columns |
| q6 | null | see below |
| q7 | "east, 4349.29" | first data row of `report.csv`, which was written by that run |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why q6 is null:** the inner merge went from 195 rows to 178, a net drop of 17. That net drop only equals the number of unmatched orders if every `customer_id` in `customers.csv` was unique. If some customer appeared twice, matching orders would be doubled in the merge, and more than 17 orders could have gone unmatched. Ormaos records the row and null counts of each table, but not the values or how many are distinct, and `customers.csv` is gone. The README says the file has "one row per customer", but that describes the export, not what this run read. If you trust the README on that point, the answer would be 17.
```

### notebook, `none`, run 1: null for q4, q5, q7, q8

The agent's last message, from [`streams/notebook-none-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-none-1.jsonl):

```text
I wrote `answers.json`. Four questions have answers and four are `null`, because they need the row data from `sales.csv`, which is gone.

| id | answer | evidence |
|---|---|---|
| q1 | `40` | The saved output of cell-2 is `40`. |
| q2 | `"cell-4"` | The execution counts are cell-1=1, cell-2=2, **cell-4=3**, cell-3=4, cell-5=5. So `add_tax` (cell-4) ran before `drop_key_accounts` (cell-3). |
| q3 | `"tax-inclusive"` | Because of that order, the filter compared prices that already included the 20% tax against `LIMIT`. |
| q4 | `null` | |
| q5 | `null` | |
| q6 | `"15602.40"` | The saved output of cell-5 is `week total with tax: 15602.40`. |
| q7 | `null` | |
| q8 | `null` | |

**Why q4, q5, q7 and q8 are null:** each one depends on individual rows. The notebook only kept the row count and the final total. The `ormaos` package in `.venv` is a stand-in whose `record()` does nothing, so no recording of the steps exists either. I found no other leftover files from the run.

**Format note:** I wrote q6 as the string `"15602.40"` so it keeps exactly two decimals. As a JSON number it would read `15602.4`.

The out-of-order run is also why this total doesn't match the README's `47498.40`. The README number comes from running the cells top to bottom, which filters before adding tax.
```

### notebook, `raw`, run 1: null for q5, q7, q8

The agent's last message, from [`streams/notebook-raw-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-raw-1.jsonl):

```text
I've written `answers.json` in `/srv/notebook`. I could answer five of the eight questions; the other three are null because the data they need isn't in the folder.

| id | answer | where it comes from |
|---|---|---|
| q1 | 40 | The saved output of cell-2. The trace agrees: `DictReader.__next__` was called 41 times (40 rows plus the end of file). |
| q2 | cell-4 | Execution counts by cell: cell-1=1, cell-2=2, **cell-4=3**, cell-3=4, cell-5=5. |
| q3 | tax-inclusive | The cells ran out of their order on the page: `add_tax` (cell-4) ran before `drop_key_accounts` (cell-3). The trace timestamps confirm this (`add_tax` at …779400, `drop_key_accounts` at …784154). So the filter saw prices with the 20% tax already added. |
| q4 | 22 | `total`'s generator was entered 23 times, which means 22 rows (one extra entry at the end). |
| q6 | "15602.40" | The printed output of cell-5. |
| q5, q7, q8 | null | `sales.csv` isn't here, and the trace doesn't record argument or return values. So I can't recover individual prices or quantities. |

Two other things:
- The `ormaos` package in `.venv` is a stand-in whose `record()` does nothing, so it recorded nothing for these steps.
- The README's expected total (47498.40) comes from running the cells top to bottom, so the filter sees pre-tax prices. That is a different order from this session's, which is why its total doesn't match the 15602.40 printed here.
```

### notebook, `ormaos`, run 1: null for q5, q7, q8

The agent's last message, from [`streams/notebook-ormaos-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl):

````text
I wrote `answers.json`. I could answer five of the eight questions from the recording and the saved notebook. The other three depend on values from `sales.csv`, which is gone, and the recording doesn't store values, so those are `null`.

```json
{"q1": 40, "q2": "cell-4", "q3": "tax-inclusive", "q4": 22, "q5": null, "q6": 15602.40, "q7": null, "q8": null}
```

**What happened in that run:** the cells did not run top to bottom. Going by the saved execution counts, the order was cell-1 (1), cell-2 (2), cell-4 (3), cell-3 (4), cell-5 (5). So `add_tax` ran before `drop_key_accounts`.

- **q1 = 40:** `load` returned a list of 40 dicts (recording r1), and cell-2's saved output is `40`.
- **q2 = cell-4:** it has execution count 3.
- **q3 = tax-inclusive:** `add_tax` (r2) ran before `drop_key_accounts` (r3), so the limit of 1000 was checked against prices that already included the 20% tax.
- **q4 = 22:** `drop_key_accounts` went from a list of 40 dicts to 22 (r3), and `total` then got those 22 (r4).
- **q6 = 15602.40:** this is cell-5's printed output, `week total with tax: 15602.40`. The README's 47498.40 is from a top-to-bottom run, not this one.
- **q5, q7, q8 = null:** these need actual prices and quantities. The recording keeps only types and lengths, and the input file isn't there anymore.
````

### notebook, `ormaos-values`, run 1: null for q5, q7, q8

The agent's last message, from [`streams/notebook-ormaos-values-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl):

```text
I've written `answers.json`. Five questions have answers; three are null because the recording doesn't contain the data they need.

| id | answer | how I know |
|---|---|---|
| q1 | 40 | The output saved in cell-2 is `40`, and in recording r1 `load` returned a list of 40 items. |
| q2 | cell-4 | The saved execution counts are cell-1=1, cell-2=2, cell-4=3, cell-3=4, cell-5=5. So `add_tax` ran before `drop_key_accounts`. |
| q3 | tax-inclusive | Because of that order, recording r3 shows `drop_key_accounts` receiving prices that already include the tax (144.0, 936.0, 2160.0…). |
| q4 | 22 | In r3 `drop_key_accounts` returned 22 rows, and in r4 `total` received 22. |
| q5 | null | See below. |
| q6 | "15602.40" | `total` returned 15602.4, and the cell printed `week total with tax: 15602.40`. |
| q7 | null | See below. |
| q8 | null | See below. |

**Why three are null:** the recording keeps only the first 10 items of each list, so 30 of the 40 input rows and 12 of the 22 remaining rows were never stored. In the rows that were stored, one was wrongly dropped: desk, 860 → 1032 after tax. The highest remaining price seen is 936.00. Neither is a complete count or maximum, so I didn't answer with them.

**Format choice:** I wrote q6 as the string `"15602.40"` because a JSON number would drop the trailing zero that "exactly two decimals" asks for.

The total of 15602.40 is lower than the 47498.40 in the README because the cells ran out of order. With the tax added before the filter, every sale priced above about 833.33 went over the 1000 limit and was removed.
```

### ai-app, `none`, run 1: null for q2, q3, q4, q5, q6

The agent's last message, from [`streams/ai-app-none-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-none-1.jsonl):

```text
I wrote `answers.json`. I could answer two of the seven questions; the other five are `null`.

**Answered:**
- **q7:** `"The invoice of October shows the old address."` `app.py` writes summaries in the same order as the tickets, so the first entry in `summaries.json` (id 401) belongs to the first ticket.
- **q8:** `703`. That's the current size of `summaries.json`. It has the exact layout the run's `json.dump(..., indent=2)` produces, with no trailing newline, so it looks like the file that run wrote.

**Null (q2–q6):** these need the length of each ticket's text. The model server sends a 503 to `small-1` for any prompt over 600 characters, and `app.py` then retries the same prompt with `large-1`. So the ticket lengths would tell me which tickets fell back, how many 503s there were, the total number of POSTs (8 plus one per fallback), and the longest prompt. But `tickets.json` is gone. The server didn't log anything, and `summaries.json` doesn't record which model wrote each summary. Both models produce the same text: the first sentence of the ticket. So there's nothing left to work these out from.
```

### ai-app, `raw`, run 1: null for q6

The agent's last message, from [`streams/ai-app-raw-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-raw-1.jsonl):

```text
I've written `answers.json` in `/srv/ai-app`, and it parses as valid JSON. I answered six of the seven questions from the trace and the files the run left behind; q6 is `null`.

| Question | Answer | How I got it |
|---|---|---|
| q2: summaries from small-1 alone | 5 | 8 tickets went through `summarize`, and 3 of them hit an error and fell back. |
| q3: HTTP 503 responses | 3 | There were 3 `HTTPError` calls. The model server only sends 503 when a small-1 prompt is over 600 characters. |
| q4: total POST requests | 11 | There were 11 `ask` calls, 11 `urlopen` calls and 11 server `do_POST` calls. |
| q5: tickets summarized by large-1 | `[403, 405, 408]` | The errors happened inside the 3rd, 5th and 8th `summarize` calls. I matched those positions to the ids in the order they appear in `summaries.json`. |
| q6: longest prompt length | `null` | The trace has no call arguments, and `tickets.json` is missing, so the prompt texts can't be recovered. All that's certain is that the 3 prompts that fell back were each over 600 characters. |
| q7: first ticket's summary | "The invoice of October shows the old address." | From `summaries.json`, entry id 401. |
| q8: size of `summaries.json` | 703 | The file's size on disk. It was last changed at the same time as the trace, so I took it to be this run's output. |

The trace has three server-side `generate` calls stamped about 1.4 seconds before `main` started, and server events don't line up neatly with each request. None of the answers depend on those events, because I took everything from app.py's own calls (`summarize`, `ask`, `HTTPError`).
```

### order-sync, `none`, run 1: null for q1, q3, q4, q5, q6

The agent's last message, from [`streams/order-sync-none-1.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-none-1.jsonl):

```text
I've written `answers.json` with answers to three of the eight questions (q2, q7, q8). The other five are `null`, because the information about that run no longer exists.

**What's left of the run:**
- `data/cron.log` has two runs, both ending `exit=0 sync finished: OK`, at 16:57:43 and 16:57:44. I took the second one as last night's cron run, since the folder is as the last run left it.
- In `data/inventory.db`, every row in `applied_orders` has an `applied_at` time. Orders SO-20501 to SO-20514 are stamped 19:57:43 UTC and SO-20515 to SO-20538 are stamped 19:57:44 UTC. The first run had already logged that it finished at :43, so the :44 rows belong to the second run.
- `data/orders.csv` now holds today's orders, there is no `.ormaos/` recording, and warnings were hidden by the default ERROR log level. So nothing records what the API actually returned or which orders were skipped.

**Answers:**
- **q2 = 19:** the 19 orders stamped at :44.
- **q7 = 104:** the total of the `quantity` (items taken) on those 19 rows.
- **q8 = "2,5":** both back-orders belong to orders stamped at :44: SO-20524 (2 items) and SO-20534 (3 items).
- **q1, q3, q4, q5, q6 = null:** these need the list of orders the API returned, which was overwritten. SO-20521, 20526, 20530, 20533 and 20537 are missing from `applied_orders`, so they were probably skipped. But I can't tell which run received them or what error each hit. I also can't tell how many already-applied orders came in again. Some stock levels don't match `data/count.csv` (KBD-0101 is 9 higher than the count, MON-0201 is 1 higher, HDS-0402 is 4 higher). That fits orders being dropped silently, but it isn't enough to answer these questions.

**One caveat:** if the second run started within the same second the first one finished (:43), some of the :43 rows could also be from it. In that case q2 and q7 would be higher. I counted only the :44 rows.
```

## Limits

As the run's report lists them:

- No expected result was written before the run.
- With --values, a list keeps its first 10 items; notebook q5, q7 and q8 need more and no arm answered them.
- In 4 of 9 tasks every arm scored 1.00 (ml-training, rl-env, agent-change, freight-quote); those tasks do not separate the arms.
- The gap between raw and ormaos in the mean score is 0.058. Per task, the difference of the task's mean scores divided by 9, every task where it is not zero: web-backend -0.005, data-pipeline +0.056, ai-app +0.016, order-sync -0.009.
- The intervals of raw and ormaos overlap.
- The questions were written by claude-opus-5-5 from the source, the README and the printed output of each program, one writer per task, one attempt; the prompt, the transcript and the questions are in `writer/`. The programs and the executions are still those the makers of Ormaos wrote for `knows`.
- The agents and the question writer are the same model.
- The oracle (`oracle.py`, `tracer.py`) and the rule of each question (`rules.json`) were written by the makers of Ormaos after reading the questions and before any agent ran. Where a question can be read in two ways the oracle answers one of them.
- A question is dropped only when the oracle cannot give one unambiguous answer; a question that an arm cannot answer is kept.
- The writer's folder had no input file, so some questions ask for what the removed input held; the writer of `rl-env` ran the program in its folder before writing.
- `notebook`: the cells call `ormaos.record()` themselves. In `ormaos-values` a cell that is not of the notebook first makes that call record values; it is not `ormaos run --values`. The printed output given to the writer is that of the process that ran the kernel, not of the cells.
- Values in a recording are cut at 200 characters, and likely secrets are written as `***`.
- Four of the nine programs (`web-backend`, `ml-training`, `rl-env`, `agent-change`) read no input that can be taken away, so an agent can run them again; the report says how many runs did.
- One model, one prompt per arm, one tracer with its default settings, N runs per task and arm as shown.
- The dates in the data of the two jobs are relative to the day `build.py` ran: build on the day of the run.

## This run

- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801)
- ormaos-examples commit that added these results: [`091b688`](https://github.com/ormaos/ormaos-examples/commit/091b688f01b0b233631f0fe714935ebc52ab7fd9)
- Ormaos commit: [`968f697`](https://github.com/ormaos/ormaos-python/commit/968f697); VizTracer 1.1.1; Python 3.14.4
- Model: `claude-opus-5-5`, with the `claude` command line 2.1.322
- Date: 2026-11-27

The results files, on GitHub:

- [`results.jsonl`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/results.jsonl): one line per run
- [`streams/`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams): what every agent said and did
- [`report.md`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/report.md): the report the runner wrote

To run it again: Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, git, the `claude` command line signed in, and a checkout of ormaos-python next to this repository. The run sends the folders it makes to the model's API.

```bash
git clone https://github.com/ormaos/ormaos-python
git -C ormaos-python checkout 968f697
git clone https://github.com/ormaos/ormaos-examples
cd ormaos-examples && git checkout 091b688 && cd agent-bench/knows2
python3 build.py
python3 run.py --runs 3 --replacements 0
```
