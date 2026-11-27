# Benchmarks

What Ormaos does, measured. Every number on these pages is read from a results file by a script, never typed by hand.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

In knows2, with an Ormaos recording (`ormaos`) the agent answered 198 of 213 questions right, over its 27 runs; with only the folder (`none`), 153 of 213. Null answers: 14 and 60. Wrong answers: 1 and 0.

**Mean score per arm, knows2.** The mean score of the runs of each arm, with its 95% bootstrap interval. none 0.71 (0.59 to 0.83); raw 0.87 (0.79 to 0.95); ormaos 0.93 (0.88 to 0.97); ormaos-values 0.95 (0.90 to 0.99).

| Arm | Runs | Mean score | 95% interval |
|---|---:|---:|---:|
| `none` | 27 | 0.71 | 0.59 to 0.83 |
| `raw` | 27 | 0.87 | 0.79 to 0.95 |
| `ormaos` | 27 | 0.93 | 0.88 to 0.97 |
| `ormaos-values` | 27 | 0.95 | 0.90 to 0.99 |

**Right, null and wrong answers per arm.** Every answer of every run of each arm, stacked: right, null, wrong. none: 153 right, 60 null, 0 wrong; raw: 186 right, 27 null, 0 wrong; ormaos: 198 right, 14 null, 1 wrong; ormaos-values: 202 right, 11 null, 0 wrong.

| Arm | Answers | Right | Null | Wrong |
|---|---:|---:|---:|---:|
| `none` | 213 | 153 | 60 | 0 |
| `raw` | 213 | 186 | 27 | 0 |
| `ormaos` | 213 | 198 | 14 | 1 |
| `ormaos-values` | 213 | 202 | 11 | 0 |

- **80.4 kB vs 12.0 MB**: median size, over the 9 executions of knows2, of the Ormaos recording (`.ormaos/`) and of the VizTracer trace (`result.json`). [Per execution](https://ormaos.com/benchmarks/knows2/#results)
- **101,359 vs 52,196**: median tokens per run in knows2, `ormaos` and `none`; `raw` 75,290, `ormaos-values` 126,028. [Per arm](https://ormaos.com/benchmarks/knows2/#results)
- **x34.28 / x7.69**: time of a run recorded with the default capability set, against the same run without Ormaos: CPU-bound workload / I/O workload. [Every capability set](https://ormaos.com/benchmarks/overhead/)

## What is measured

- **What an agent knows** about an execution it did not see: factual questions about what happened in it, graded against an oracle ([knows2](https://ormaos.com/benchmarks/knows2/), and the earlier [knows](https://ormaos.com/benchmarks/knows/)).
- **Whether the code an agent changes passes a check**, for programs whose behaviour on one night differed from what their README says ([fix](https://ormaos.com/benchmarks/fix/)).
- **The ways in**: the folder the execution left and nothing more (`none`), a VizTracer trace of the execution (`raw`), or its Ormaos recording (`ormaos`, and in knows2 also `ormaos-values`). The agent is `claude-opus-5-5`, in a sandbox; the oracle and the check read neither the trace nor the recording.
- **What recording adds to the time of a run**, per capability set, on 2 workloads ([overhead](https://ormaos.com/benchmarks/overhead/)).

## The benchmarks

### What an agent knows about an execution

*knows2 · 2026-11-27 · claude-opus-5-5 · N = 108 runs, 27 per arm*

9 executions, questions by a model that was not told what Ormaos records, graded against an oracle. Mean score per arm, from 0 to 1.

**Mean score per arm, knows2.** The mean score of the runs of each arm, with its 95% bootstrap interval. none 0.71 (0.59 to 0.83); raw 0.87 (0.79 to 0.95); ormaos 0.93 (0.88 to 0.97); ormaos-values 0.95 (0.90 to 0.99).

| Arm | Runs | Mean score | 95% interval |
|---|---:|---:|---:|
| `none` | 27 | 0.71 | 0.59 to 0.83 |
| `raw` | 27 | 0.87 | 0.79 to 0.95 |
| `ormaos` | 27 | 0.93 | 0.88 to 0.97 |
| `ormaos-values` | 27 | 0.95 | 0.90 to 0.99 |

[The method, every question and every answer](https://ormaos.com/benchmarks/knows2/)

### The earlier run, questions by the makers of Ormaos

*knows · 2026-11-27 · claude-opus-5-5 · N = 81 runs, 27 per arm*

The same executions, with questions written by the people who make Ormaos; replaced by knows2. Mean score per arm.

**Mean score per arm, knows.** The mean score of the runs of each arm, with its 95% bootstrap interval. none 0.69 (0.55 to 0.83); raw 0.94 (0.88 to 1.00); ormaos 1.00 (1.00 to 1.00).

| Arm | Runs | Mean score | 95% interval |
|---|---:|---:|---:|
| `none` | 27 | 0.69 | 0.55 to 0.83 |
| `raw` | 27 | 0.94 | 0.88 to 1.00 |
| `ormaos` | 27 | 1.00 | 1.00 to 1.00 |

[The run, and why knows2 replaced it](https://ormaos.com/benchmarks/knows/)

### 8 programs whose behaviour differed from their README

*fix · 2026-11-26 · claude-opus-5-5 · N = 72 runs, 24 per arm*

A coding agent changes a program whose behaviour on one night differed from what its README says; a check it does not see runs that night again. The metric `fixed`, per arm.

**The metric fixed, per arm.** The share of first attempts of each arm whose code passed the check, with its 95% Wilson score interval. none 21/24 (69% to 96%); raw 23/24 (80% to 99%); ormaos 24/24 (86% to 100%).

| Arm | Fixed | 95% interval |
|---|---:|---:|
| `none` | 21/24 | 69% to 96% |
| `raw` | 23/24 | 80% to 99% |
| `ormaos` | 24/24 | 86% to 100% |

[The programs, the check and every run](https://ormaos.com/benchmarks/fix/)

### What recording adds to the time of a run

*overhead · 2026-11-27 · N = 20 runs per row*

The median time of a recorded run, as a multiple of the same run without Ormaos, per capability set and workload, on a log scale.

**Time of a recorded run, as a multiple of the same run without Ormaos.** The median wall time of each capability set divided by the median without Ormaos, per workload, on a log scale. context only: CPU-bound x1.59 (130.2 ms), I/O x2.50 (86.3 ms); calls and exceptions: CPU-bound x31.17 (2544.4 ms), I/O x4.00 (138.0 ms); calls, exceptions and path: CPU-bound x33.58 (2741.4 ms), I/O x4.10 (141.7 ms); calls, exceptions and io (the default): CPU-bound x34.28 (2798.2 ms), I/O x7.69 (265.7 ms).

| Capability set | CPU-bound | I/O |
|---|---:|---:|
| context only | x1.59 | x2.50 |
| calls and exceptions | x31.17 | x4.00 |
| calls, exceptions and path | x33.58 | x4.10 |
| calls, exceptions and io (the default) | x34.28 | x7.69 |

[Every capability set, and the machine](https://ormaos.com/benchmarks/overhead/)

## What these benchmarks do not show

- The programs and their executions were written for these benchmarks by the people who make Ormaos; they are not a sample of real programs.
- One model, one prompt per arm, one tracer with its default settings, and few runs: 27 per arm in knows2, 24 in fix. Several 95% intervals overlap; each page says which.
- In knows2 the question writer and the agents are the same model, and in 4 of 9 tasks every arm scored 1.00.
- The overhead was timed on 2 workloads on one machine; another program has another cost.
- Whether what happened is what should have happened: the benchmarks ask what happened, and the reader decides.

## The pages as files

- Each page is also Markdown, at its address with `.md` in place of the last slash: [`/benchmarks.md`](https://ormaos.com/benchmarks.md), [`/benchmarks/knows2.md`](https://ormaos.com/benchmarks/knows2.md), and so on.
- [`/benchmarks/llms.txt`](https://ormaos.com/benchmarks/llms.txt) lists them for agents.
- The pages are written by [`site/benchmarks/build.py`](https://github.com/ormaos/ormaos-examples/blob/main/site/benchmarks/build.py) from the results files.
