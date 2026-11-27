# knows: the earlier run

N = 81 runs: 9 tasks x 3 arms x 3 runs, model `claude-opus-5-5`, 2026-11-27. The same 9 executions as knows2, with questions written by the people who make Ormaos.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## Why knows2 replaced it

In knows, the programs, the executions and the questions were all written by the people who make Ormaos, and the questions ask about calls, exceptions, shapes and I/O: what Ormaos records. That choice of questions can favour the recording. [knows2](https://ormaos.com/benchmarks/knows2/) keeps the same executions and an oracle under `sys.settrace`, and has the questions written by a model that saw only the source, the README and the printed output of each program and was not told about Ormaos; it adds a fourth arm, a recording with values, counts every answer as right, null or wrong, and drops a question only when the oracle cannot answer it. The tasks and the oracle are described on its page.

## Results

The score of a run is the share of its questions that are right, by the rules of [`rules.json`](https://github.com/ormaos/ormaos-examples/blob/e0ffe13724a3147b1ed40177890ef757b48c00eb/agent-bench/knows/rules.json), written before the run. The interval is a 95% bootstrap interval of the mean over the runs of the arm.

**Mean score per arm, knows.** The mean score of the runs of each arm, with its 95% bootstrap interval. none 0.69 (0.55 to 0.83); raw 0.94 (0.88 to 1.00); ormaos 1.00 (1.00 to 1.00).

| Arm | Runs | Mean score | 95% interval | Median wall time | Median tool calls | Median tokens | Ran the program again | Timed out |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `none` | 27 | 0.69 | 0.55 to 0.83 | 31 s | 4 | 60,088 | 6/27 | 0 |
| `raw` | 27 | 0.94 | 0.88 to 1.00 | 41 s | 5 | 90,107 | 1/27 | 0 |
| `ormaos` | 27 | 1.00 | 1.00 to 1.00 | 28 s | 4 | 86,152 | 0/27 | 0 |

**Mean score per task and arm, knows.** The mean score of the runs of each task and arm, from 0 (no question right) to 1 (all right). web-backend: none 1.00, raw 1.00, ormaos 1.00. data-pipeline: none 0.29, raw 0.52, ormaos 1.00. notebook: none 0.67, raw 1.00, ormaos 1.00. ml-training: none 1.00, raw 1.00, ormaos 1.00. rl-env: none 1.00, raw 1.00, ormaos 1.00. ai-app: none 0.14, raw 1.00, ormaos 1.00. agent-change: none 1.00, raw 0.96, ormaos 1.00. order-sync: none 0.14, raw 1.00, ormaos 1.00. freight-quote: none 1.00, raw 1.00, ormaos 1.00.

| Task | Questions | `none` | `raw` | `ormaos` |
|---|---:|---:|---:|---:|
| web-backend | 7 | 1.00 | 1.00 | 1.00 |
| data-pipeline | 7 | 0.29 | 0.52 | 1.00 |
| notebook | 6 | 0.67 | 1.00 | 1.00 |
| ml-training | 7 | 1.00 | 1.00 | 1.00 |
| rl-env | 6 | 1.00 | 1.00 | 1.00 |
| ai-app | 7 | 0.14 | 1.00 | 1.00 |
| agent-change | 8 | 1.00 | 0.96 | 1.00 |
| order-sync | 7 | 0.14 | 1.00 | 1.00 |
| freight-quote | 7 | 1.00 | 1.00 | 1.00 |

## Limits

As the run's report lists them:

- No expectation was written before this run: the rules of `rules.json` were, what each arm would score was not.
- In 4 of 9 tasks every arm scored 1.00 (web-backend, ml-training, rl-env, freight-quote); those tasks do not separate the arms.
- Of the gap of 0.06 between raw and ormaos in the mean score, 0.05 comes from data-pipeline: its questions ask the row counts of DataFrames, which Ormaos records and VizTracer with its default settings does not.

## This run

- Results folder: [`agent-bench/knows/results/20261127-140018`](https://github.com/ormaos/ormaos-examples/tree/e0ffe13724a3147b1ed40177890ef757b48c00eb/agent-bench/knows/results/20261127-140018)
- ormaos-examples commit that added these results: [`e0ffe13`](https://github.com/ormaos/ormaos-examples/commit/e0ffe13724a3147b1ed40177890ef757b48c00eb)
- Ormaos commit: [`968f697`](https://github.com/ormaos/ormaos-python/commit/968f697); VizTracer 1.1.1; Python 3.14.4
- Model: `claude-opus-5-5`, with the `claude` command line 2.1.322
- Date: 2026-11-27

The results files, on GitHub:

- [`results.jsonl`](https://github.com/ormaos/ormaos-examples/blob/e0ffe13724a3147b1ed40177890ef757b48c00eb/agent-bench/knows/results/20261127-140018/results.jsonl): one line per run
- [`streams/`](https://github.com/ormaos/ormaos-examples/tree/e0ffe13724a3147b1ed40177890ef757b48c00eb/agent-bench/knows/results/20261127-140018/streams): what every agent said and did
- [`report.md`](https://github.com/ormaos/ormaos-examples/blob/e0ffe13724a3147b1ed40177890ef757b48c00eb/agent-bench/knows/results/20261127-140018/report.md): the report the runner wrote

To run it again: Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, git, the `claude` command line signed in, and a checkout of ormaos-python next to this repository. The run sends the folders it makes to the model's API.

```bash
git clone https://github.com/ormaos/ormaos-python
git -C ormaos-python checkout 968f697
git clone https://github.com/ormaos/ormaos-examples
cd ormaos-examples && git checkout e0ffe13 && cd agent-bench/knows
python3 build.py
python3 run.py --runs 3
```
