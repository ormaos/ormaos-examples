# price-import

A scheduled job that takes over the supplier's price list: the supplier's sync writes the current list to `data/supplier/pricelist.csv`, and at night the job converts it and writes its prices to the catalog, where the shop reads them in the morning.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py                                           # take over the prices
python3 catalog.py                                       # show the catalog
python3 catalog.py --compare data/supplier/pricelist.csv # catalog prices that are not the list's
```

The job prints `price import finished: OK` and exits with code 0 when the prices were taken over. If it cannot run, it prints `price import failed: ...` on stderr and exits with code 2.

## The supplier's list

A CSV with semicolons: `article`, `description`, `price`, `currency`, `pack`.

- A price is written the continental way (`1.234,50`) and is the price of one pack of `pack` pieces. The catalog has the price of one piece, rounded half up to a cent.
- Only rows in `EUR` are taken over.
- A price of `0,00` is how the supplier marks an article it no longer sells: the product becomes inactive and keeps its price.
- An article the catalog does not know is added inactive, for someone to give it a name.

The supplier's sync replaces the list whenever the supplier changes it, also during the day.

## The converter

`convert.py` turns the supplier's list into the import format (`sku`, `price_cents`). It is a program of its own, because purchasing also runs it by hand:

```bash
python3 convert.py data/supplier/pricelist.csv /tmp/converted.csv
```

The job runs it, with `data/staging.csv` as the output, and then loads that file.

Options of the job: `--list PATH`, `--staging PATH`, `--db PATH`.

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: convert the list, load it |
| `convert.py` | the converter |
| `catalog.py` | the SQLite catalog: loading a converted list, comparing with a supplier list |
| `data/` | the supplier's list, the converted list and the database (`catalog.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `PRICE_IMPORT_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
50 1 * * * cd /opt/price-import && python3 job.py
```

What the job prints is all that is kept of a run.
