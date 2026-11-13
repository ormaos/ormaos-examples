# order-sync

A scheduled job that takes the new orders from the sales system and applies them to the warehouse inventory: for every order, the ordered quantity leaves the stock of that SKU.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
./reset.sh            # rebuild data/orders.csv and data/inventory.db from seed/
python3 job.py        # sync the orders
python3 inventory.py  # show the stock levels
```

The job prints `sync finished: OK` and exits with code 0 when the sync is done. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2.

Running the job again over the same orders is safe: an order is applied only once.

## Where the orders come from

| Source | Command | What it does |
|---|---|---|
| CSV export (default) | `python3 job.py` | reads `data/orders.csv` |
| Sales API | `python3 job.py --source api` | asks `GET /orders` over HTTP |

The sales system is external. Its API hands every order over once: it keeps a cursor, and a fetch returns the orders placed since the fetch before. Orders already handed over cannot be asked for again. The last orders before a fetch may come again with the next one; the job applies them only once.

There is no real sales API here. With `--source api` the job starts a small stand-in on `127.0.0.1`, calls it, and stops it. The stand-in serves what is in `data/orders.csv`: the orders the sales system would hand over now.

Options: `--orders PATH` for another export, `--db PATH` for another database.

## Orders

An order has `order_id`, `placed_at`, `sku`, `quantity`, `channel` (`web`, `store`, `marketplace`) and, optionally, `unit`:

- `each` (the default): the quantity counts single items;
- `pack`: the quantity counts packs, and the pack size of the SKU (in the inventory) gives the number of items.

An order for more items than there are on hand takes what is there. The rest is kept as a back-order (table `backorders`), and the stock does not go below zero.

## Checking the stock against a count

The warehouse counts the shelves and sends a CSV with the columns `sku` and `counted`. To see it next to the inventory:

```bash
python3 inventory.py --count data/count.csv
```

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: fetch, parse, validate, apply |
| `fetch.py` | reads the CSV export or calls the sales API |
| `parse.py` | turns raw rows into `Order` records |
| `validate.py` | business rules: SKU format `AAA-0000`, quantity between 1 and 500, unit `each` or `pack` |
| `inventory.py` | the SQLite database: stock levels, pack sizes, the orders already applied, back-orders |
| `seed/` | for trying it out: the starting stock and a two-day export of orders |
| `data/` | the orders to fetch and the database (`reset.sh` rebuilds both from `seed/`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `ORDER_SYNC_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron, against the sales API:

```
30 2 * * * cd /opt/order-sync && python3 job.py --source api
```

What the job prints is all that is kept of a run.

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
