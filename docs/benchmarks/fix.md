# fix: 8 programs that behaved otherwise than their README

N = 72 runs: 8 programs x 3 arms x 3 runs, the first attempt of every slot, model `claude-opus-5-5`, 2026-11-26. A coding agent gets a scheduled program that behaved otherwise than its README on one night, the data that night left and a one-sentence symptom. A check it does not see then plays that night again on the code the agent left; `fixed` is the name of the metric that counts the runs whose code passed it.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

- **21/24**: `none`, `fixed`, 95% interval 69% to 96%
- **23/24**: `raw`, `fixed`, 95% interval 80% to 99%
- **24/24**: `ormaos`, `fixed`, 95% interval 86% to 100%

## Method

### The programs

8 small scheduled Python programs, standard library only. Each runs from cron, prints its OK line and exits with code 0; on one night it behaved otherwise than its README, in a different place in each program, and that shows only in the data it left. Running it again today does not show it: that night's input is gone.

| Program | What it does, by its README | Where it behaved otherwise than its README |
|---|---|---|
| `order-sync` | applies orders to an inventory | an exception that is caught and not shown |
| `freight-quote` | quotes freight from a carrier's API | a fallback, with nothing printed, after HTTP calls that returned an error |
| `late-fees` | charges late fees on overdue invoices | a branch taken because of a value in the environment |
| `statement-import` | books a bank statement into a ledger | a loop that stops before the end of its input |
| `fx-rates` | takes over exchange rates from a feed | a retry that makes its call once |
| `price-import` | takes over a supplier's price list | a subprocess whose exit code is not read |
| `points-grant` | grants loyalty points for purchases | an SQL statement that also writes other rows |
| `commission-run` | works out sales commissions | a value kept from one item to the next |

### The arms

| Arm | Added to the folder | Added to the prompt |
|---|---|---|
| `none` | nothing | nothing |
| `raw` | `result.json`: a [VizTracer](https://github.com/gaogaotiantian/viztracer) trace of that night's run, default settings | that the file is there and how to read it |
| `ormaos` | `.ormaos/`: the Ormaos recording of that night's run, and `.venv/` with the `ormaos` command line | that the recording is there, and to run `.venv/bin/ormaos guide` first |

All arms have the same code, data and task text: the symptom, how cron runs the program, and "Find the cause and fix it." The nights are played once per arm, in copies mounted at the same path, and the build stops if the copies do not leave the same data.

### The check

For each program, `hidden/check.py`, not in the agent's folder, plays that night again on the code the agent left, and nights on which the program did what its README says. It passes when that night's data now comes out as the README describes and the other nights end as before, with exit code 0 and the program's last line as cron reads it. The metric `fixed` counts the runs whose code passed it.

### The sandbox

The folder is mounted at `/srv/<program>` inside bubblewrap, with nothing else of the machine but the system (`/usr` and `/etc`, read-only), the `claude` program and its login. `claude -p --model claude-opus-5-5 --safe-mode --strict-mcp-config` gets the task text, with the tools Bash, Read, Grep, Glob, Edit and Write, and the runner's time limit. The network is not cut: the agent needs it to reach the model.

### Scored by the first attempt of every slot

What counts is the first attempt of every program, arm and run: all 72 of them, as planned before the run. A run that used up its time counts with the code it left. An attempt in which the agent named a path outside its folder, or that ended with an error, was marked and run again; the later attempts (45) are listed in the report and do not count. First attempts that were marked: 23; they count like the others, since the sandbox has nothing of these programs outside the folder.

## Results

The interval is the 95% Wilson score interval, computed with the runner's own function. Tokens are input, output and cache tokens added up, as the claude command line reports them.

**The metric fixed, per arm.** The share of first attempts of each arm whose code passed the check, with its 95% Wilson score interval. none 21/24 (69% to 96%); raw 23/24 (80% to 99%); ormaos 24/24 (86% to 100%).

| Arm | Fixed | 95% interval | Median wall time | Median tool calls | Median tokens | Timed out |
|---|---:|---:|---:|---:|---:|---:|
| `none` | 21/24 | 69% to 96% | 50 s | 7 | 94,458 | 0 |
| `raw` | 23/24 | 80% to 99% | 56 s | 8 | 140,558 | 0 |
| `ormaos` | 24/24 | 86% to 100% | 44 s | 7 | 112,676 | 0 |

The 95% intervals of all 3 arms overlap one another.

### Per program

| Program | `none` | `raw` | `ormaos` |
|---|---:|---:|---:|
| [`order-sync`](https://ormaos.com/benchmarks/cases/fix-order-sync/) | 3/3 | 3/3 | 3/3 |
| [`freight-quote`](https://ormaos.com/benchmarks/cases/fix-freight-quote/) | 3/3 | 3/3 | 3/3 |
| [`late-fees`](https://ormaos.com/benchmarks/cases/fix-late-fees/) | 2/3 | 2/3 | 3/3 |
| [`statement-import`](https://ormaos.com/benchmarks/cases/fix-statement-import/) | 3/3 | 3/3 | 3/3 |
| [`fx-rates`](https://ormaos.com/benchmarks/cases/fix-fx-rates/) | 1/3 | 3/3 | 3/3 |
| [`price-import`](https://ormaos.com/benchmarks/cases/fix-price-import/) | 3/3 | 3/3 | 3/3 |
| [`points-grant`](https://ormaos.com/benchmarks/cases/fix-points-grant/) | 3/3 | 3/3 | 3/3 |
| [`commission-run`](https://ormaos.com/benchmarks/cases/fix-commission-run/) | 3/3 | 3/3 | 3/3 |

### First attempts whose code did not pass the check

With what the check said:

- `late-fees`, `none`, run 3: the night ran with LATE_FEES_PAUSE=0: the job did not end with `late fees finished: OK`; a night with LATE_FEES_PAUSE=1 is paused: the job did not end with `late fees finished: OK`; a night without the variable is charged: the job did not end with `late fees finished: OK`
- `late-fees`, `raw`, run 1: a night with LATE_FEES_PAUSE=1 is paused: the job did not end with `late fees finished: OK`
- `fx-rates`, `none`, run 2: the job did not end with `rates finished: OK`; it printed `rates finished: WARNING held for review: HUF`
- `fx-rates`, `none`, run 3: the job did not end with `rates finished: OK`; it printed `rates finished: INCOMPLETE (held for review: HUF)`

The report adds an analysis made after seeing the results, not planned before the run, which changes nothing in the tables: the folders these runs left were read by hand. See its section "After the run" in [`report.md`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/report.md).

## Limits

- The 8 programs, and where each one behaved otherwise than its README, were written for this benchmark by the people who make Ormaos; they are not a sample of real programs.
- One model, one prompt per arm, one tracer with its default settings.
- The dates in the data are relative to the day `build.py` ran: build on the day of the run.

## This run

- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703)
- ormaos-examples commit that added these results: [`88bec53`](https://github.com/ormaos/ormaos-examples/commit/88bec53c78471c6086564b4de8a00084c4dc4ae6)
- Ormaos commit: [`75c191a`](https://github.com/ormaos/ormaos-python/commit/75c191a); VizTracer 1.1.1; Python 3.14.4
- Model: `claude-opus-5-5`, with the `claude` command line 2.1.322
- Date: 2026-11-26

The results files, on GitHub:

- [`results.jsonl`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/results.jsonl): one line per run
- [`streams/`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams): what every agent said and did
- [`report.md`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/report.md): the report the runner wrote

To run it again: Linux with [bubblewrap](https://github.com/containers/bubblewrap), Python 3.12 or newer, git, the `claude` command line signed in, and a checkout of ormaos-python next to this repository. The run sends the folders it makes to the model's API.

```bash
git clone https://github.com/ormaos/ormaos-python
git -C ormaos-python checkout 75c191a
git clone https://github.com/ormaos/ormaos-examples
cd ormaos-examples && git checkout 88bec53 && cd agent-bench
python3 build.py
python3 run.py --runs 3
```
