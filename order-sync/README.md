# order-sync

A scheduled job that takes the orders from the sales system and applies them to the warehouse inventory: for every order, the ordered quantity leaves the stock of that SKU.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
./reset.sh            # rebuild data/orders.csv and data/inventory.db from seed/
python3 job.py        # sync the orders
python3 inventory.py  # show the stock levels
```

The job prints `sync finished: OK` and exits with code 0 when the sync is done. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2.

Running the job again over the same export is safe: an order is applied only once.

## Where the orders come from

| Source | Command | What it does |
|---|---|---|
| CSV export (default) | `python3 job.py` | reads `data/orders.csv` |
| Sales API | `python3 job.py --source api` | asks `GET /orders` over HTTP |

There is no real sales API here. With `--source api` the job starts a small stand-in on `127.0.0.1` that serves the same orders, calls it, and stops it.

Options: `--orders PATH` for another export, `--db PATH` for another database.

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: fetch, parse, validate, apply |
| `fetch.py` | reads the CSV export or calls the sales API |
| `parse.py` | turns raw rows into `Order` records |
| `validate.py` | business rules: SKU format `AAA-0000`, quantity between 1 and 500 |
| `inventory.py` | the SQLite database: stock levels and the orders already applied |
| `seed/` | the starting stock and a two-day export of orders |
| `data/` | created by `reset.sh`: the working copy of the export and the database |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `ORDER_SYNC_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every 15 minutes with cron:

```
*/15 * * * * cd /opt/order-sync && python3 job.py
```

## Recording a run with Ormaos

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Ormaos must be installed in the same environment as the job: the Python that runs `job.py` must be able to `import ormaos`. The job itself needs nothing installed. From this folder:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install git+https://github.com/ormaos/ormaos-python
python -c "import ormaos"   # no error: the job's Python can see it
```

If you have a checkout of `ormaos-python`, install that instead: `pip install /path/to/ormaos-python`.

Then, with the environment still active:

```bash
./reset.sh
ormaos run -- python job.py
```

The job runs as before, and the recording is saved in `.ormaos/` in this folder. `reset.sh` does not touch it.
