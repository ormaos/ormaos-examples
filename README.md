# ormaos-examples

Example programs for [Ormaos](https://github.com/ormaos/ormaos-python).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

## Examples

| Folder | What it is |
|---|---|
| [`order-sync/`](order-sync/) | a scheduled job that syncs orders from a sales system into an inventory (CSV or a local HTTP API in, SQLite out) |

## A run that already happened

`scenarios/morning_after.py` builds, in a new folder, the state in which `order-sync` is found on the morning after a night run: the job ran from cron and printed `sync finished: OK`, the sales system has moved on to today's orders, and the stock of some products does not match the warehouse count.

```bash
python3 scenarios/morning_after.py /tmp/order-sync-morning            # nothing recorded
python3 scenarios/morning_after.py /tmp/order-sync-recorded --record  # last night's run recorded with Ormaos
```

With `--record` the folder gets a `.venv` with Ormaos, and last night's recording is in its `.ormaos/`; read it with `.venv/bin/ormaos show last`. `--ormaos PATH` installs from a checkout of `ormaos-python` instead of GitHub.

Each example is self-contained and uses only the Python standard library. Its README says how to run it and how to record a run with Ormaos.

## License

Apache 2.0. See [LICENSE](LICENSE).
