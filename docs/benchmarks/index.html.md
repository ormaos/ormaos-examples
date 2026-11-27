# Benchmarks

What Ormaos does, measured. Every number on these pages is read from a results file by a script, never typed by hand.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## What is measured

Whether a coding agent knows what happened in an execution it did not see, and whether it fixes a bug from a night that went wrong, when it has the folder the execution left and nothing more (`none`), a VizTracer trace of the execution (`raw`), or its Ormaos recording (`ormaos`, and in knows2 also `ormaos-values`); the agent is `claude-opus-5-5`, in a sandbox, and its answers or its code are graded by an oracle or a check that reads neither the trace nor the recording. And how much time recording adds to a Python program.

### What an agent knows about an execution

*knows2 · 2026-11-27 · claude-opus-5-5 · N = 108 runs, 27 per arm*

9 executions, questions by a model that was not told what Ormaos records, graded against an oracle. Mean score per arm, from 0 to 1:

- **0.71**: `none`, 95% interval 0.59 to 0.83
- **0.87**: `raw`, 95% interval 0.79 to 0.95
- **0.93**: `ormaos`, 95% interval 0.88 to 0.97
- **0.95**: `ormaos-values`, 95% interval 0.90 to 0.99

[The method, every question and every answer](https://ormaos.com/benchmarks/knows2/)

### The earlier run, questions by the makers of Ormaos

*knows · 2026-11-27 · claude-opus-5-5 · N = 81 runs, 27 per arm*

The same executions, with questions written by the people who make Ormaos; replaced by knows2. Mean score per arm:

- **0.69**: `none`, 95% interval 0.55 to 0.83
- **0.94**: `raw`, 95% interval 0.88 to 1.00
- **1.00**: `ormaos`, 95% interval 1.00 to 1.00

[The run, and why knows2 replaced it](https://ormaos.com/benchmarks/knows/)

### 8 bugs, fixed or not

*fix · 2026-11-26 · claude-opus-5-5 · N = 72 runs, 24 per arm*

A coding agent fixes a bug from the night it happened; a hidden check decides. Fixed per arm:

- **21/24**: `none`, 95% interval 69% to 96%
- **23/24**: `raw`, 95% interval 80% to 99%
- **24/24**: `ormaos`, 95% interval 86% to 100%

[The bugs, the check and every run](https://ormaos.com/benchmarks/fix/)

### What recording adds to the time of a run

*overhead · 2026-11-27 · N = 20 runs per row*

The default capability set, as a multiple of the same run without Ormaos, with the p25 to p75 of its median:

- **x34.28**: CPU-bound workload, p25 to p75 2785.0-2810.0 ms
- **x7.69**: I/O workload, p25 to p75 264.0-267.4 ms

[Every capability set, and the machine](https://ormaos.com/benchmarks/overhead/)

## What these benchmarks do not show

- The programs, the executions and the bugs were written for these benchmarks by the people who make Ormaos; they are not a sample of real programs or real bugs.
- One model, one prompt per arm, one tracer with its default settings, and few runs: 27 per arm in knows2, 24 in fix. Several 95% intervals overlap; each page says which.
- In knows2 the question writer and the agents are the same model, and in 4 of 9 tasks every arm scored 1.00.
- The overhead was timed on 2 workloads on one machine; another program has another cost.
- Whether what happened is what should have happened: the benchmarks ask what happened, and the reader decides.

## The pages as files

- Each page is also Markdown, at its address followed by `index.html.md`.
- [`/benchmarks/llms.txt`](https://ormaos.com/benchmarks/llms.txt) lists them for agents.
- The pages are written by [`site/benchmarks/build.py`](https://github.com/ormaos/ormaos-examples/blob/main/site/benchmarks/build.py) from the results files.
