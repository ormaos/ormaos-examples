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

*From the knows2 run of 2026-11-27, in the environment "earlier: bubblewrap, network open", agent `claude-code / claude-opus-5-5`: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801).*

## Where Ormaos changed the result and where it did not

All 17 situations: the 9 executions of knows2, with the mean score of their runs (0 to 1), and the 8 programs of fix, with the first attempts that passed the check. Sorted by the mean of `ormaos` minus the mean of `none`, over every run of every agent; in 7 of them the two differ. Each name links to the situation's page: what happened, what the agent was given, and run 1 of each arm side by side.

| Situation | `none` | `raw` | `ormaos` | `ormaos-values` | `ormaos` − `none` |
|---|---:|---:|---:|---:|---:|
| [ai-app](https://ormaos.com/benchmarks/cases/knows2-ai-app/) (knows2): support tickets summarized through a model API with a small and a large model | 0.29 | 0.86 | 1.00 | 1.00 | +0.71 |
| [fx-rates](https://ormaos.com/benchmarks/cases/fix-fx-rates/) (fix): a scheduled job that takes over exchange rates from a feed; where it behaved otherwise than its README: a retry that makes its call once | 1/3 | 3/3 | 3/3 |  | +0.67 |
| [data-pipeline](https://ormaos.com/benchmarks/cases/knows2-data-pipeline/) (knows2): a pandas report that joins two exports and sums them by region | 0.25 | 0.38 | 0.88 | 0.92 | +0.62 |
| [order-sync](https://ormaos.com/benchmarks/cases/knows2-order-sync/) (knows2): a night run of a job that applies orders to an inventory | 0.38 | 1.00 | 0.92 | 1.00 | +0.54 |
| [late-fees](https://ormaos.com/benchmarks/cases/fix-late-fees/) (fix): a scheduled job that charges late fees on overdue invoices; where it behaved otherwise than its README: a branch taken because of a value in the environment | 2/3 | 2/3 | 3/3 |  | +0.33 |
| [notebook](https://ormaos.com/benchmarks/cases/knows2-notebook/) (knows2): a Jupyter notebook that sums a week of sales, with tax | 0.50 | 0.62 | 0.62 | 0.62 | +0.12 |
| [commission-run](https://ormaos.com/benchmarks/cases/fix-commission-run/) (fix): a scheduled job that works out sales commissions; where it behaved otherwise than its README: a value kept from one item to the next | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [freight-quote](https://ormaos.com/benchmarks/cases/fix-freight-quote/) (fix): a scheduled job that quotes freight from a carrier's API; where it behaved otherwise than its README: a fallback, with nothing printed, after HTTP calls that returned an error | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [order-sync](https://ormaos.com/benchmarks/cases/fix-order-sync/) (fix): a scheduled job that applies orders to an inventory; where it behaved otherwise than its README: an exception that is caught and not shown | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [points-grant](https://ormaos.com/benchmarks/cases/fix-points-grant/) (fix): a scheduled job that grants loyalty points for purchases; where it behaved otherwise than its README: an SQL statement that also writes other rows | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [price-import](https://ormaos.com/benchmarks/cases/fix-price-import/) (fix): a scheduled job that takes over a supplier's price list; where it behaved otherwise than its README: a subprocess whose exit code is not read | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [statement-import](https://ormaos.com/benchmarks/cases/fix-statement-import/) (fix): a scheduled job that books a bank statement into a ledger; where it behaved otherwise than its README: a loop that stops before the end of its input | 3/3 | 3/3 | 3/3 |  | +0.00 |
| [agent-change](https://ormaos.com/benchmarks/cases/knows2-agent-change/) (knows2): a billing tool run before and after a change an agent made | 1.00 | 1.00 | 1.00 | 1.00 | +0.00 |
| [freight-quote](https://ormaos.com/benchmarks/cases/knows2-freight-quote/) (knows2): a night run of a job that quotes freight from a carrier's API | 1.00 | 1.00 | 1.00 | 1.00 | +0.00 |
| [ml-training](https://ormaos.com/benchmarks/cases/knows2-ml-training/) (knows2): a PyTorch training run that leaves out batches whose loss is not finite | 1.00 | 1.00 | 1.00 | 1.00 | +0.00 |
| [rl-env](https://ormaos.com/benchmarks/cases/knows2-rl-env/) (knows2): episodes of a grid world, a courier walking to a customer | 1.00 | 1.00 | 1.00 | 1.00 | +0.00 |
| [web-backend](https://ormaos.com/benchmarks/cases/knows2-web-backend/) (knows2): a FastAPI route that lists a customer's orders with their totals | 1.00 | 1.00 | 0.96 | 1.00 | -0.04 |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them. Over the 27 runs of `ormaos` and 27 runs of `ormaos-values` in knows2; each situation's page has it per question.

| Verb | `ormaos`: runs | answered after it | right | `ormaos-values`: runs | answered after it | right |
|---|---:|---:|---:|---:|---:|---:|
| `guide` | 27 | 199 | 198 | 27 | 202 | 202 |
| `show` | 27 | 199 | 198 | 27 | 202 | 202 |
| `tree` | 25 | 183 | 182 | 27 | 202 | 202 |
| `list` | 24 | 176 | 176 | 24 | 180 | 180 |
| `io` | 19 | 139 | 138 | 16 | 124 | 124 |
| `exceptions` | 10 | 69 | 69 | 11 | 79 | 79 |
| `logs` | 3 | 22 | 22 | 2 | 16 | 16 |
| `diff` | 2 | 16 | 16 | 1 | 8 | 8 |
| `help` | 0 | 0 | 0 | 1 | 8 | 8 |

## The benchmarks

### What an agent knows about an execution

*knows2 · 2026-11-27 · claude-opus-5-5 · N = 108 runs, 27 per arm · earlier*

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

### 8 programs that behaved otherwise than their README

*fix · 2026-11-26 · claude-opus-5-5 · N = 72 runs, 24 per arm*

A coding agent changes a program that behaved otherwise than its README on one night; a check it does not see runs that night again. The metric `fixed`, per arm.

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

## Not measured yet

- Other agents and models: Codex, Gemini, Grok and other Claude models. Every run on these pages is `claude-code / claude-opus-5-5`.
- RL environments: knows2 has one small grid world (`rl-env`), as a program an agent asks about; no environment in which an agent is trained.
- Large codebases: the programs of fix have 216 to 434 lines of code.
- Harder repairs, where the agent alone fails: in fix, `none` passed the check in 21 of 24 first attempts.

## What these benchmarks do not show

- The programs and their executions were written for these benchmarks by the people who make Ormaos; they are not a sample of real programs.
- One prompt per arm, one tracer with its default settings, and few runs: 27 per arm in knows2, 24 in fix. Several 95% intervals overlap; each page says which.
- In knows2 the question writer and the agents are the same model, and in 4 of 9 tasks every arm scored 1.00.
- The overhead was timed on 2 workloads on one machine; another program has another cost.
- Whether what happened is what should have happened: the benchmarks ask what happened, and the reader decides.
- The knows2 questions and the oracle's answers are public since 2026-11-27, the day they were committed: a later run must not let the agent reach the network, other than the model's API.

## The pages as files

- Each page is also Markdown, at its address with `.md` in place of the last slash: [`/benchmarks.md`](https://ormaos.com/benchmarks.md), [`/benchmarks/knows2.md`](https://ormaos.com/benchmarks/knows2.md), [`/benchmarks/cases/knows2-ai-app.md`](https://ormaos.com/benchmarks/cases/knows2-ai-app.md), and so on.
- [`/benchmarks/llms.txt`](https://ormaos.com/benchmarks/llms.txt) lists them for agents.
- The pages are written by [`site/benchmarks/build.py`](https://github.com/ormaos/ormaos-examples/blob/main/site/benchmarks/build.py) from the results files.
