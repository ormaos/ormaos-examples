# agent-bench/knows: what an agent knows about an execution

N = 81 runs: 9 tasks x 3 arms x 3 runs, every slot run once, all of them counted. Model: claude-opus-5-5. Ormaos 968f697, VizTracer 1.1.1, Python 3.14.4; built 2026-11-27T13:58:55.

The score of a run is the share of the task's questions that its `answers.json` got right, by the rules written in `rules.json` before the run. The interval is a 95% bootstrap interval of the mean over the runs of the arm (10,000 resamples).

| Arm | Runs | Mean score | 95% interval | Median wall time | Median tool calls | Median tokens | Ran the program again | Timed out |
|---|---|---|---|---|---|---|---|---|
| none | 27 | 0.69 | 0.55 to 0.83 | 31 s | 4 | 60,088 | 6/27 | 0 |
| raw | 27 | 0.94 | 0.88 to 1.00 | 41 s | 5 | 90,107 | 1/27 | 0 |
| ormaos | 27 | 1.00 | 1.00 to 1.00 | 28 s | 4 | 86,152 | 0/27 | 0 |

Tokens are input, output and cache tokens added up, as the claude command line reports them. An agent ran the program again when a command of its ran one of the program's scripts, or its own Python code imported one of the program's modules.

## Mean score per task

| Task | Questions | none | raw | ormaos |
|---|---|---|---|---|
| web-backend | 7 | 1.00 | 1.00 | 1.00 |
| data-pipeline | 7 | 0.29 | 0.52 | 1.00 |
| notebook | 6 | 0.67 | 1.00 | 1.00 |
| ml-training | 7 | 1.00 | 1.00 | 1.00 |
| rl-env | 6 | 1.00 | 1.00 | 1.00 |
| ai-app | 7 | 0.14 | 1.00 | 1.00 |
| agent-change | 8 | 1.00 | 0.96 | 1.00 |
| order-sync | 7 | 0.14 | 1.00 | 1.00 |
| freight-quote | 7 | 1.00 | 1.00 | 1.00 |

## Median wall time per task, in seconds

| Task | Questions | none | raw | ormaos |
|---|---|---|---|---|
| web-backend | 7 | 31 | 39 | 24 |
| data-pipeline | 7 | 41 | 51 | 19 |
| notebook | 6 | 31 | 45 | 27 |
| ml-training | 7 | 37 | 50 | 34 |
| rl-env | 6 | 28 | 26 | 32 |
| ai-app | 7 | 22 | 40 | 25 |
| agent-change | 8 | 31 | 43 | 33 |
| order-sync | 7 | 37 | 42 | 34 |
| freight-quote | 7 | 47 | 39 | 28 |

## Median tokens per task

| Task | Questions | none | raw | ormaos |
|---|---|---|---|---|
| web-backend | 7 | 51,014 | 98,910 | 76,430 |
| data-pipeline | 7 | 85,978 | 96,834 | 49,288 |
| notebook | 6 | 59,884 | 101,647 | 58,239 |
| ml-training | 7 | 60,088 | 78,687 | 113,535 |
| rl-env | 6 | 55,944 | 50,927 | 86,152 |
| ai-app | 7 | 36,080 | 77,880 | 67,670 |
| agent-change | 8 | 52,520 | 78,189 | 106,885 |
| order-sync | 7 | 70,146 | 123,481 | 101,951 |
| freight-quote | 7 | 92,172 | 98,331 | 96,720 |

## Runs that ran the program again, per task

| Task | Questions | none | raw | ormaos |
|---|---|---|---|---|
| web-backend | 7 | 0/3 | 0/3 | 0/3 |
| data-pipeline | 7 | 0/3 | 0/3 | 0/3 |
| notebook | 6 | 0/3 | 0/3 | 0/3 |
| ml-training | 7 | 2/3 | 1/3 | 0/3 |
| rl-env | 6 | 2/3 | 0/3 | 0/3 |
| ai-app | 7 | 0/3 | 0/3 | 0/3 |
| agent-change | 8 | 0/3 | 0/3 | 0/3 |
| order-sync | 7 | 0/3 | 0/3 | 0/3 |
| freight-quote | 7 | 2/3 | 0/3 | 0/3 |

## Per question

Runs that got the question right, out of the runs of the arm.

| Task | Question | none | raw | ormaos |
|---|---|---|---|---|
| web-backend | q1 | 3/3 | 3/3 | 3/3 |
| web-backend | q2 | 3/3 | 3/3 | 3/3 |
| web-backend | q3 | 3/3 | 3/3 | 3/3 |
| web-backend | q4 | 3/3 | 3/3 | 3/3 |
| web-backend | q5 | 3/3 | 3/3 | 3/3 |
| web-backend | q6 | 3/3 | 3/3 | 3/3 |
| web-backend | q7 | 3/3 | 3/3 | 3/3 |
| data-pipeline | q1 | 0/3 | 0/3 | 3/3 |
| data-pipeline | q2 | 0/3 | 0/3 | 3/3 |
| data-pipeline | q3 | 0/3 | 0/3 | 3/3 |
| data-pipeline | q4 | 0/3 | 2/3 | 3/3 |
| data-pipeline | q5 | 0/3 | 3/3 | 3/3 |
| data-pipeline | q6 | 3/3 | 3/3 | 3/3 |
| data-pipeline | q7 | 3/3 | 3/3 | 3/3 |
| notebook | q1 | 3/3 | 3/3 | 3/3 |
| notebook | q2 | 3/3 | 3/3 | 3/3 |
| notebook | q3 | 3/3 | 3/3 | 3/3 |
| notebook | q4 | 3/3 | 3/3 | 3/3 |
| notebook | q5 | 0/3 | 3/3 | 3/3 |
| notebook | q6 | 0/3 | 3/3 | 3/3 |
| ml-training | q1 | 3/3 | 3/3 | 3/3 |
| ml-training | q2 | 3/3 | 3/3 | 3/3 |
| ml-training | q3 | 3/3 | 3/3 | 3/3 |
| ml-training | q4 | 3/3 | 3/3 | 3/3 |
| ml-training | q5 | 3/3 | 3/3 | 3/3 |
| ml-training | q6 | 3/3 | 3/3 | 3/3 |
| ml-training | q7 | 3/3 | 3/3 | 3/3 |
| rl-env | q1 | 3/3 | 3/3 | 3/3 |
| rl-env | q2 | 3/3 | 3/3 | 3/3 |
| rl-env | q3 | 3/3 | 3/3 | 3/3 |
| rl-env | q4 | 3/3 | 3/3 | 3/3 |
| rl-env | q5 | 3/3 | 3/3 | 3/3 |
| rl-env | q6 | 3/3 | 3/3 | 3/3 |
| ai-app | q1 | 0/3 | 3/3 | 3/3 |
| ai-app | q2 | 0/3 | 3/3 | 3/3 |
| ai-app | q3 | 0/3 | 3/3 | 3/3 |
| ai-app | q4 | 0/3 | 3/3 | 3/3 |
| ai-app | q5 | 0/3 | 3/3 | 3/3 |
| ai-app | q6 | 0/3 | 3/3 | 3/3 |
| ai-app | q7 | 3/3 | 3/3 | 3/3 |
| agent-change | q1 | 3/3 | 3/3 | 3/3 |
| agent-change | q2 | 3/3 | 3/3 | 3/3 |
| agent-change | q3 | 3/3 | 3/3 | 3/3 |
| agent-change | q4 | 3/3 | 3/3 | 3/3 |
| agent-change | q5 | 3/3 | 3/3 | 3/3 |
| agent-change | q6 | 3/3 | 2/3 | 3/3 |
| agent-change | q7 | 3/3 | 3/3 | 3/3 |
| agent-change | q8 | 3/3 | 3/3 | 3/3 |
| order-sync | q1 | 3/3 | 3/3 | 3/3 |
| order-sync | q2 | 0/3 | 3/3 | 3/3 |
| order-sync | q3 | 0/3 | 3/3 | 3/3 |
| order-sync | q4 | 0/3 | 3/3 | 3/3 |
| order-sync | q5 | 0/3 | 3/3 | 3/3 |
| order-sync | q6 | 0/3 | 3/3 | 3/3 |
| order-sync | q7 | 0/3 | 3/3 | 3/3 |
| freight-quote | q1 | 3/3 | 3/3 | 3/3 |
| freight-quote | q2 | 3/3 | 3/3 | 3/3 |
| freight-quote | q3 | 3/3 | 3/3 | 3/3 |
| freight-quote | q4 | 3/3 | 3/3 | 3/3 |
| freight-quote | q5 | 3/3 | 3/3 | 3/3 |
| freight-quote | q6 | 3/3 | 3/3 | 3/3 |
| freight-quote | q7 | 3/3 | 3/3 | 3/3 |

## Limits

- No expectation was written before this run: the rules of `rules.json` were, what each arm would score was not.
- In 4 of 9 tasks every arm scored 1.00 (web-backend, ml-training, rl-env, freight-quote); those tasks do not separate the arms.
- Of the gap of 0.06 between raw and ormaos in the mean score, 0.05 comes from data-pipeline: its questions ask the row counts of DataFrames, which Ormaos records and VizTracer with its default settings does not.

## Runs that ended otherwise

Out of time, an error of the command line or the model, or no `answers.json` that reads as JSON. They count, with the score shown.

None.

## Paths outside the folder

Runs in which the agent named a path outside its folder, or another host. Information only: these runs count like the others. The sandbox has nothing of the tasks outside the folder.

- data-pipeline, none, run 1: /srv, ~ (`streams/data-pipeline-none-1.jsonl`)
- notebook, none, run 1: /, ~ (`streams/notebook-none-1.jsonl`)
- ml-training, ormaos, run 1: /home/levimbraga/.claude/projects/-srv-ml-training/4689c3d7-5255-4b63-994c-16e82b7cc877/tool-results/bgjjlmjga.txt (`streams/ml-training-ormaos-1.jsonl`)
- freight-quote, none, run 1: /, /srv, ~ (`streams/freight-quote-none-1.jsonl`)
- data-pipeline, none, run 2: / (`streams/data-pipeline-none-2.jsonl`)
- notebook, none, run 2: /, ~ (`streams/notebook-none-2.jsonl`)
- order-sync, none, run 2: /, /srv, /var/mail, /var/spool/cron, /var/spool/mail, ~ (`streams/order-sync-none-2.jsonl`)
- order-sync, raw, run 2: /srv (`streams/order-sync-raw-2.jsonl`)
- web-backend, none, run 3: / (`streams/web-backend-none-3.jsonl`)
- data-pipeline, none, run 3: / (`streams/data-pipeline-none-3.jsonl`)
- notebook, none, run 3: /, ~ (`streams/notebook-none-3.jsonl`)
- order-sync, raw, run 3: /srv (`streams/order-sync-raw-3.jsonl`)
- freight-quote, none, run 3: /srv, ~ (`streams/freight-quote-none-3.jsonl`)
