# late-fees

A scheduled job that charges late fees: every night, each invoice that is overdue gets the fee of that night, written to the billing database, where the statements read it.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py        # charge tonight's fees
python3 invoices.py   # show the fees charged, per night
```

The job prints `late fees finished: OK` and exits with code 0 when the night was handled. If it cannot run (no database, unreadable settings), it prints `late fees failed: ...` on stderr and exits with code 2.

`--date YYYY-MM-DD` charges another night than today; `--db PATH` uses another database. A night is charged once: running it again adds nothing.

## The rules

- An invoice is charged from the day after its grace period: 3 days after the due date on the `standard` plan, 14 on `business`.
- Paid invoices and disputed invoices are not charged.
- The fee of a night is 5 basis points of the invoice amount, at least 0.25, and the fees of one invoice never add up to more than 10% of its amount.

The numbers are in `settings.ini`.

## Pausing

During maintenance of the billing system the job must not charge. Set `pause = yes` in `settings.ini`, or `LATE_FEES_PAUSE=1` in the environment of the job (the environment wins). Both are booleans: `1`/`yes`/`true`/`on` pause, `0`/`no`/`false`/`off` do not, an empty or unset variable falls back to the file, and any other value makes the job fail with exit code 2. A paused night charges nothing and ends with `late fees finished: OK (paused, nothing charged)`.

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: one night, charged or paused |
| `settings.py`, `settings.ini` | the numbers of the rules and the pause switch |
| `fees.py` | whether an invoice is chargeable, and its fee for a night |
| `invoices.py` | the SQLite database: invoices and fees |
| `data/` | the database (`billing.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `LATE_FEES_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
40 23 * * * cd /opt/late-fees && python3 job.py
```

What the job prints is all that is kept of a run.
