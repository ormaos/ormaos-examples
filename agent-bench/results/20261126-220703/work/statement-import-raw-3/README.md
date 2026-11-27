# statement-import

A scheduled job that books the bank's statements into the ledger of the account: the bank's transfer drops a statement file in `inbox/` every evening, and the job books it at night, so that the ledger shows the bank's closing balance in the morning.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py      # book the statements in inbox/
python3 ledger.py   # show the balance
```

The job prints `statement import finished: OK` and exits with code 0 when every file in `inbox/` is booked. A file that is not a statement of the account, or that has a line the job cannot read, stops it: it prints `statement import failed: ...` on stderr, exits with code 2, books nothing of that file and leaves it in `inbox/`.

A booked file is deleted from `inbox/`; the bank keeps the statements.

## The statement file

`inbox/statement-YYYYMMDD.txt`, one record per line, fields separated by `|`:

```
H|ACC-7701|2026-03-02
T|B-40117|2026-03-02|1250.00|B|Invoice 4411 Alder Supply
T|B-40118|2026-03-02|89.90-|B|Card 4471 fuel
R|B-40122|2026-03-02|B-40118
```

- `H` is the header: the account (`STATEMENT_IMPORT_ACCOUNT`, default `ACC-7701`) and the date.
- `T` is a transaction: the bank's id, the date, the amount (`89.90-` is money out), the status and a text. Status `P` is pending: it is not booked, and the bank sends it again with status `B` when it is.
- `R` is a reversal: it takes back the transaction it names.
- Lines that start with `#` are comments, and empty lines are ignored.
- The bank sends the last records of a statement again with the next one. An id is booked once.

## Checking against the bank

The bank's closing balances, as exported from online banking, go to `data/bank_balance.csv` (`date`, `closing_cents`):

```bash
python3 ledger.py --compare data/bank_balance.csv
```

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: every file in the inbox, booked and deleted |
| `statement.py` | the statement format |
| `ledger.py` | the SQLite ledger: booking a record, the balance |
| `inbox/` | where the statements arrive |
| `data/` | the ledger (`ledger.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `STATEMENT_IMPORT_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
30 2 * * * cd /opt/statement-import && python3 job.py
```

What the job prints is all that is kept of a run.
