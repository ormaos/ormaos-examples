# agent-bench/knows2: the same executions, questions by a writer who was not told what Ormaos records

N = 108 runs: 9 tasks x 4 arms x 3 runs, every slot run once, all of them counted. Model: claude-opus-5-5. Ormaos 968f697, VizTracer 1.1.1, Python 3.14.4; built 2026-11-27T16:56:42.

The score of a run is the share of the task's questions that its `answers.json` got right, by the rules written in `rules.json` before any agent ran. The interval is a 95% bootstrap interval of the mean over the runs of the arm (10,000 resamples).

| Arm | Runs | Mean score | 95% interval | Median wall time | Median tool calls | Median tokens | Ran the program again | Timed out |
|---|---|---|---|---|---|---|---|---|
| none | 27 | 0.71 | 0.59 to 0.83 | 26 s | 4 | 52,196 | 7/27 | 0 |
| raw | 27 | 0.87 | 0.79 to 0.95 | 39 s | 5 | 75,290 | 3/27 | 0 |
| ormaos | 27 | 0.93 | 0.88 to 0.97 | 32 s | 5 | 101,359 | 4/27 | 0 |
| ormaos-values | 27 | 0.95 | 0.90 to 0.99 | 34 s | 6 | 126,028 | 0/27 | 0 |

Tokens are input, output and cache tokens added up, as the claude command line reports them. An agent ran the program again when a command of its ran one of the program's scripts, or its own Python code imported one of the program's modules.

Cost, as the claude command line reports it (`total_cost_usd`): $17.72 for 108 runs; mean per run, none $0.100, raw $0.170, ormaos $0.181, ormaos-values $0.205.

## Right, null, wrong

Every answer of every run: right by the rule of its question; null, the agent wrote null; wrong, an answer that is not null and that the rule marks wrong.

| Arm | Answers | Right | Null | Wrong |
|---|---|---|---|---|
| none | 213 | 153 | 60 | 0 |
| raw | 213 | 186 | 27 | 0 |
| ormaos | 213 | 198 | 14 | 1 |
| ormaos-values | 213 | 202 | 11 | 0 |

Every wrong answer:

| Task | Arm | Run | Question | Answer | Oracle |
|---|---|---|---|---|---|
| web-backend | ormaos | 3 | q5 | "17, 2880" | [8, 3660] |

## Mean score per task

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | 8 | 1.00 | 1.00 | 0.96 | 1.00 |
| data-pipeline | 8 | 0.25 | 0.38 | 0.88 | 0.92 |
| notebook | 8 | 0.50 | 0.62 | 0.62 | 0.62 |
| ml-training | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| rl-env | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| ai-app | 7 | 0.29 | 0.86 | 1.00 | 1.00 |
| agent-change | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| order-sync | 8 | 0.38 | 1.00 | 0.92 | 1.00 |
| freight-quote | 8 | 1.00 | 1.00 | 1.00 | 1.00 |

## Median wall time per task, in seconds

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | 8 | 31 | 38 | 31 | 29 |
| data-pipeline | 8 | 26 | 29 | 26 | 27 |
| notebook | 8 | 23 | 51 | 28 | 35 |
| ml-training | 8 | 27 | 41 | 40 | 38 |
| rl-env | 8 | 23 | 26 | 39 | 33 |
| ai-app | 7 | 18 | 33 | 28 | 31 |
| agent-change | 8 | 26 | 32 | 32 | 38 |
| order-sync | 8 | 42 | 55 | 54 | 56 |
| freight-quote | 8 | 37 | 57 | 36 | 37 |

## Median tokens per task

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | 8 | 80,197 | 90,646 | 94,507 | 98,270 |
| data-pipeline | 8 | 53,763 | 68,967 | 67,985 | 70,789 |
| notebook | 8 | 51,923 | 113,451 | 85,441 | 127,594 |
| ml-training | 8 | 46,997 | 62,110 | 119,744 | 130,419 |
| rl-env | 8 | 46,849 | 52,730 | 114,889 | 106,909 |
| ai-app | 7 | 36,101 | 68,921 | 86,814 | 112,865 |
| agent-change | 8 | 52,881 | 74,146 | 101,359 | 137,166 |
| order-sync | 8 | 73,893 | 182,999 | 155,911 | 255,162 |
| freight-quote | 8 | 93,621 | 164,720 | 119,402 | 186,298 |

## Runs that ran the program again, per task

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | 8 | 0/3 | 0/3 | 0/3 | 0/3 |
| data-pipeline | 8 | 0/3 | 0/3 | 0/3 | 0/3 |
| notebook | 8 | 0/3 | 0/3 | 0/3 | 0/3 |
| ml-training | 8 | 2/3 | 0/3 | 0/3 | 0/3 |
| rl-env | 8 | 2/3 | 3/3 | 3/3 | 0/3 |
| ai-app | 7 | 0/3 | 0/3 | 0/3 | 0/3 |
| agent-change | 8 | 0/3 | 0/3 | 1/3 | 0/3 |
| order-sync | 8 | 0/3 | 0/3 | 0/3 | 0/3 |
| freight-quote | 8 | 3/3 | 0/3 | 0/3 | 0/3 |

## Per question

Runs that got the question right, out of the runs of the arm.

| Task | Question | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q5 | 3/3 | 3/3 | 2/3 | 3/3 |
| web-backend | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| web-backend | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| data-pipeline | q1 | 0/3 | 0/3 | 3/3 | 3/3 |
| data-pipeline | q2 | 0/3 | 0/3 | 3/3 | 3/3 |
| data-pipeline | q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| data-pipeline | q4 | 0/3 | 0/3 | 3/3 | 3/3 |
| data-pipeline | q5 | 0/3 | 0/3 | 3/3 | 3/3 |
| data-pipeline | q6 | 0/3 | 0/3 | 0/3 | 1/3 |
| data-pipeline | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| data-pipeline | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| notebook | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| notebook | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| notebook | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| notebook | q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| notebook | q5 | 0/3 | 0/3 | 0/3 | 0/3 |
| notebook | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| notebook | q7 | 0/3 | 0/3 | 0/3 | 0/3 |
| notebook | q8 | 0/3 | 0/3 | 0/3 | 0/3 |
| ml-training | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| ml-training | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| rl-env | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q2 | 0/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q5 | 0/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q6 | 0/3 | 0/3 | 3/3 | 3/3 |
| ai-app | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| ai-app | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| agent-change | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q1 | 0/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q3 | 0/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q4 | 0/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q5 | 0/3 | 3/3 | 2/3 | 3/3 |
| order-sync | q6 | 0/3 | 3/3 | 2/3 | 3/3 |
| order-sync | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| order-sync | q8 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q1 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q2 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q3 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q4 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q5 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q6 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q7 | 3/3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q8 | 3/3 | 3/3 | 3/3 | 3/3 |

## Dropped questions

The writers wrote 72 questions; 1 dropped, each because the oracle cannot give one unambiguous answer.

- ai-app, q1: "On which TCP port on 127.0.0.1 did the model_server stand-in listen during this run?" Reason: the server listens on a free port the system picks (`("127.0.0.1", 0)`): the oracle's execution and the execution of each arm got different ports.

## Limits

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

## Runs that ended otherwise

Out of time, an error of the command line or the model, or no `answers.json` that reads as JSON. They count, with the score shown.

None.

## Paths outside the folder

Runs in which the agent named a path outside its folder, or another host. Information only: these runs count like the others. The sandbox has nothing of the tasks outside the folder.

- data-pipeline, none, run 1: /, ~ (`streams/data-pipeline-none-1.jsonl`)
- notebook, none, run 1: /, ~ (`streams/notebook-none-1.jsonl`)
- rl-env, raw, run 1: /srv (`streams/rl-env-raw-1.jsonl`)
- order-sync, none, run 1: ~ (`streams/order-sync-none-1.jsonl`)
- freight-quote, none, run 1: /, ~ (`streams/freight-quote-none-1.jsonl`)
- data-pipeline, none, run 2: /, ~ (`streams/data-pipeline-none-2.jsonl`)
- notebook, none, run 2: /, ~ (`streams/notebook-none-2.jsonl`)
- notebook, ormaos, run 2: / (`streams/notebook-ormaos-2.jsonl`)
- notebook, raw, run 2: / (`streams/notebook-raw-2.jsonl`)
- order-sync, none, run 2: /srv, ~ (`streams/order-sync-none-2.jsonl`)
- data-pipeline, none, run 3: / (`streams/data-pipeline-none-3.jsonl`)
- notebook, none, run 3: /, /run (`streams/notebook-none-3.jsonl`)
- notebook, ormaos, run 3: / (`streams/notebook-ormaos-3.jsonl`)
- notebook, ormaos-values, run 3: / (`streams/notebook-ormaos-values-3.jsonl`)
- ml-training, raw, run 3: / (`streams/ml-training-raw-3.jsonl`)
