# commission-run

A scheduled job that works out sales commissions: the CRM's export drops the day's deals in `inbox/` every evening, and at night the job writes each rep's commission on them to a database, where payroll reads it.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py       # work out the deals in inbox/
python3 payouts.py   # show the payouts, per day
```

The job prints `commissions finished: OK` and exits with code 0 when every file in `inbox/` was handled. If it cannot run (no database, a product line without a rate), it prints `commissions failed: ...` on stderr and exits with code 2.

A handled file is deleted from `inbox/`; the CRM keeps the deals. `--date YYYY-MM-DD` writes the payouts of another day than today.

## The rules

- A rep's commission on a deal is the deal's amount times the rate, rounded down to a cent.
- The rate depends on the rep and on the product line of the deal. `rate_table` has the rates in basis points; the rep `*` is the rate of a product line for every rep without a rate of their own for it.
- A deal over 10,000.00 pays 50 basis points more.
- A deal shared by several reps (`R-12+R-15`) is paid in equal shares, each at the rep's own rate.
- A cancelled deal pays nothing.

## The deals file

`inbox/deals-YYYYMMDD.csv`: `deal_id`, `rep`, `product_line`, `amount_cents`, `status` (`won` or `cancelled`).

## Checking against finance

Finance works the commissions out on its own, from the CRM, and exports `day`, `rep_id`, `commission_cents`:

```bash
python3 payouts.py --compare data/finance_check.csv
```

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: every file in the inbox, worked out and deleted |
| `deals.py` | the deals file |
| `rates.py` | the rate of a rep for a product line, and the commission on a deal |
| `payouts.py` | the SQLite database: reps, rates, payouts |
| `inbox/` | where the deals arrive |
| `data/` | the database (`commissions.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `COMMISSION_RUN_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
5 2 * * * cd /opt/commission-run && python3 job.py
```

What the job prints is all that is kept of a run.
