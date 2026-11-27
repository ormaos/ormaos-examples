# overhead: what recording adds to the time of a run

N = 20 runs of each row, after 1 discarded; the rows take turns. Written by `bench/run.py`. Each row is the whole command, from start to exit, in milliseconds of wall-clock time: for `ormaos run` that includes starting the CLI, running the program, and reading the recording to print the summary.

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

- **x34.28**: CPU-bound workload, the default capability set, median 2798.2 ms
- **x7.69**: I/O workload, the default capability set, median 265.7 ms

## Results

**Time of a recorded run, as a multiple of the same run without Ormaos.** The median wall time of each capability set divided by the median without Ormaos, per workload, on a log scale. context only: CPU-bound x1.59 (130.2 ms), I/O x2.50 (86.3 ms); calls and exceptions: CPU-bound x31.17 (2544.4 ms), I/O x4.00 (138.0 ms); calls, exceptions and path: CPU-bound x33.58 (2741.4 ms), I/O x4.10 (141.7 ms); calls, exceptions and io (the default): CPU-bound x34.28 (2798.2 ms), I/O x7.69 (265.7 ms).

| Capability set | CPU-bound | I/O |
|---|---:|---:|
| context only | x1.59 | x2.50 |
| calls and exceptions | x31.17 | x4.00 |
| calls, exceptions and path | x33.58 | x4.10 |
| calls, exceptions and io (the default) | x34.28 | x7.69 |

### CPU-bound workload

`bench/workloads/cpu_bound.py`: 150,000 calls of small pure-Python functions, no I/O.

| Capability set | Command | Median (ms) | p25-p75 (ms) | Min-max (ms) | Added to the median | Recorded in one run |
|---|---|---|---|---|---|---|
| without Ormaos | `python` | 81.6 | 80.2-82.2 | 78.4-99.5 |  | nothing |
| context only | `ormaos run -- env -u ORMAOS_DIR python` | 130.2 | 128.6-131.0 | 127.0-133.9 | 48.6 (x1.59) | the context of the command |
| calls and exceptions | `ormaos run --no-io -- python` | 2544.4 | 2536.5-2557.0 | 2514.1-2586.4 | 2462.8 (x31.17) | 150,002 calls, 0 exceptions, 0 io events |
| calls, exceptions and path | `ormaos run --no-io --path cpu_bound.py:score -- python` | 2741.4 | 2726.9-2757.1 | 2705.1-2886.5 | 2659.7 (x33.58) | 150,002 calls, 0 exceptions, 150,000 lines, 0 io events |
| calls, exceptions and io (the default) | `ormaos run -- python` | 2798.2 | 2785.0-2810.0 | 2770.3-2929.5 | 2716.6 (x34.28) | 150,002 calls, 0 exceptions, 0 io events |

Listed as not collected in these recordings:

- context only: everything inside Python: no Python process reported: the command started no Python, or a Python without ormaos installed in its environment

### I/O workload

`bench/workloads/io_bound.py`: a SQLite file (2,000 inserts in 20 transactions, 200 queries) and 200 small files written and read back.

| Capability set | Command | Median (ms) | p25-p75 (ms) | Min-max (ms) | Added to the median | Recorded in one run |
|---|---|---|---|---|---|---|
| without Ormaos | `python` | 34.5 | 34.1-35.2 | 33.9-38.7 |  | nothing |
| context only | `ormaos run -- env -u ORMAOS_DIR python` | 86.3 | 85.1-87.0 | 83.3-100.9 | 51.8 (x2.50) | the context of the command |
| calls and exceptions | `ormaos run --no-io -- python` | 138.0 | 136.9-138.8 | 136.0-149.4 | 103.5 (x4.00) | 2,402 calls, 0 exceptions, 0 io events |
| calls, exceptions and path | `ormaos run --no-io --path io_bound.py:store -- python` | 141.7 | 140.9-142.7 | 140.0-149.7 | 107.2 (x4.10) | 2,402 calls, 0 exceptions, 2,000 lines, 0 io events |
| calls, exceptions and io (the default) | `ormaos run -- python` | 265.7 | 264.0-267.4 | 262.5-282.3 | 231.2 (x7.69) | 2,402 calls, 0 exceptions, 3,042 io events |

Listed as not collected in these recordings:

- context only: everything inside Python: no Python process reported: the command started no Python, or a Python without ormaos installed in its environment

## The machine

- N: 20 runs of each row, after 1 discarded; the rows take turns
- Machine: AMD Ryzen 7 7735HS with Radeon Graphics, 16 logical CPUs, x86_64
- OS: Linux-7.0.0-44-generic-x86_64-with-glibc2.43
- Python: CPython 3.13.17
- Ormaos: 0.0.1
- Temporary directory: /tmp
- When: 2026-11-27 13:09 -03

## How to read it

As the results file says:

- "Added to the median" is the median of the row minus the median of "without Ormaos", and their ratio.
- "context only" is `ormaos run` around a Python that starts without the recorder: the cost of the command itself, with nothing recorded inside Python.
- The other rows record inside Python. Their cost grows with the number of calls, lines and I/O events, shown in the last column, and with the time to read the recording back for the summary.
- These are two workloads on one machine. Another program has another number of calls per second, and another cost.

## This run

- Results file: [`bench/RESULTS.md`](https://github.com/ormaos/ormaos-python/blob/968f69776c7c4f9ef5c04867ed7a0c229786bc19/bench/RESULTS.md) of ormaos-python, written by [`bench/run.py`](https://github.com/ormaos/ormaos-python/blob/968f69776c7c4f9ef5c04867ed7a0c229786bc19/bench/run.py)
- Ormaos commit: [`968f697`](https://github.com/ormaos/ormaos-python/commit/968f69776c7c4f9ef5c04867ed7a0c229786bc19), version 0.0.1
- The copy these pages read: [`site/benchmarks/overhead/RESULTS.md`](https://github.com/ormaos/ormaos-examples/blob/main/site/benchmarks/overhead/RESULTS.md), taken by `site/benchmarks/build.py --overhead`
- Date: 2026-11-27 13:09 -03
- No agent and no model: this benchmark has no `results.jsonl` and no streams.

To run it again: Linux or another POSIX system, Python 3.12 or newer, and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ormaos/ormaos-python && cd ormaos-python
git checkout 968f697
uv run python bench/run.py --runs 20
```
