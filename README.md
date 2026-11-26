# ormaos-examples

Example programs for [Ormaos](https://github.com/ormaos/ormaos-python).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## Examples

| Folder | What it is |
|---|---|
| [`order-sync/`](order-sync/) | a scheduled job that syncs orders from a sales system into an inventory (CSV or a local HTTP API in, SQLite out) |
| [`freight-quote/`](freight-quote/) | a scheduled job that asks a carrier's API for the freight of tomorrow's shipments and writes the quotes (a local HTTP API in, SQLite out) |

## A run that already happened

`scenarios/morning_after.py` builds, in a new folder, the state in which `order-sync` is found on the morning after a night run: the job ran from cron and printed `sync finished: OK`, the sales system has moved on to today's orders, and the stock of some products does not match the warehouse count.

```bash
python3 scenarios/morning_after.py /tmp/order-sync-morning            # nothing recorded
python3 scenarios/morning_after.py /tmp/order-sync-recorded --record  # last night's run recorded with Ormaos
```

With `--record` the folder gets a `.venv` with Ormaos, and last night's recording is in its `.ormaos/`; read it with `.venv/bin/ormaos show last`. `--ormaos PATH` installs from a checkout of `ormaos-python` instead of GitHub.

`scenarios/two_nights.py` does the same for `freight-quote`, with two night runs: the night before last the carrier answered every call; last night the job printed `quotes finished: OK`, and this morning some of its quotes are lower than what the carrier charged. The quotes of the night before last are gone: each run replaces them.

```bash
python3 scenarios/two_nights.py /tmp/freight-quote-morning            # nothing recorded
python3 scenarios/two_nights.py /tmp/freight-quote-recorded --record  # both nights recorded with Ormaos
```

With `--record` the two recordings are `r1` and `r2` in the folder's `.ormaos/`; compare them with `.venv/bin/ormaos diff r1 r2`.

## The benchmark

[`agent-bench/`](agent-bench/) measures whether a coding agent fixes a bug more often with an Ormaos recording of the run that went wrong than with nothing, or with a raw trace: eight small jobs with one bug each, three arms, a hidden check per bug. Its README says how to build and run it.

## The demo page

[`docs/`](docs/) is the demo page, published at <https://ormaos.com/demo>: the job, a recorded terminal session, and how to try it. [`docs/README.md`](docs/README.md) says how the recordings are made and how the page is deployed.

Each example is self-contained and uses only the Python standard library. Its README says how to run it and how to record a run with Ormaos.

## License

Apache 2.0. See [LICENSE](LICENSE).
