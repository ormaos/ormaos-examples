# freight-quote

A scheduled job that quotes the freight of tomorrow's shipments: for every shipment on the dispatch list it asks the carrier for a rate and writes the quote to a database, where the invoicing reads it in the morning.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
./reset.sh         # rebuild data/ from seed/
python3 job.py     # quote the shipments
python3 quotes.py  # show the quotes
```

The job prints `quotes finished: OK` and exits with code 0 when the quotes are written. If it cannot run (no database, an unreadable dispatch list), it prints `quotes failed: ...` on stderr and exits with code 2.

Every quote comes from the carrier. If the carrier gives no rate for any shipment (calls for the day used up, lane not served, weight refused, account unknown, unreachable), the job prints `quotes failed: no carrier rate for ...` on stderr, writes nothing, and exits with code 1. It does not fall back to the contract rate card: the card is older than the carrier's tariff and quotes too low.

Each run replaces the quotes: the table holds the quotes of the current dispatch list and no other.

## Shipments

The warehouse system writes the dispatch list, `data/shipments.csv`, every evening. A shipment has `shipment_id`, `origin` and `destination` (depot codes), `weight_kg`, `length_cm`, `width_cm`, `height_cm` and `service` (`standard` or `express`).

- A lane is a pair of depots and costs the same in both directions.
- The carrier charges the larger of the real weight and the volume weight (1 kg per 5000 cm³), rounded up to half a kilo.

## The carrier

The carrier answers `GET /v1/rates?lane=...&kg=...&service=...` with the freight in cents. The account is sent in the `X-Account` header (`FREIGHT_QUOTE_ACCOUNT`, default `WH-1001`). It refuses a call with 401 (unknown account), 404 (a lane it does not serve), 422 (more than 1000 kg) or 429 (the account's calls for the day are used up).

There is no real carrier here. The job starts a small stand-in on `127.0.0.1`, calls it, and stops it. What the stand-in knows is in `data/carrier.json`: the account, its calls per day and how many are used today, and the carrier's tariff of today.

Options: `--shipments PATH` for another dispatch list, `--db PATH` for another database, `--carrier PATH` for another stand-in state.

## Checking the quotes against the bookings

When the shipments are booked, the carrier confirms what it charges, and the bookings desk exports a CSV with the columns `shipment_id` and `charged_cents`. To see it next to the quotes:

```bash
python3 quotes.py --booked data/booked.csv
```

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: read the list, price every shipment, write the quotes |
| `shipments.py` | the dispatch list: `Shipment` records, lane, chargeable weight |
| `carrier.py` | the call to the carrier's rate API, and the stand-in |
| `ratecard.py`, `ratecard.csv` | the contract rate card: base price and price per kilo for every lane |
| `quotes.py` | the SQLite database of quotes |
| `seed/` | for trying it out: a dispatch list and a state of the stand-in |
| `data/` | the dispatch list, the stand-in's state and the database (`reset.sh` rebuilds them from `seed/`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `FREIGHT_QUOTE_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
15 1 * * * cd /opt/freight-quote && python3 job.py
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
