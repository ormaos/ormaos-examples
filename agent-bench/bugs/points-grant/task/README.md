# points-grant

A scheduled job that grants loyalty points: the tills' export drops the day's purchases in `inbox/` every evening, and at night the job grants each member the points of their purchases, so that the app shows them in the morning.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py              # grant the purchases in inbox/
python3 members.py          # show the members and their points
python3 members.py --check  # members whose points are not the sum of their grants
```

The job prints `points finished: OK` and exits with code 0 when every file in `inbox/` was handled. If it cannot run, it prints `points failed: ...` on stderr and exits with code 2.

A handled file is deleted from `inbox/`; the tills keep the purchases.

## The rules

- One point per full euro, times the tier of the member: silver 1, gold 1.5, platinum 2 (rounded down).
- A purchase under 5 euros gives no points.
- A refund (a negative amount) takes its points back, but never takes a member below zero.
- A purchase is granted once, whatever the tills send again.
- Every grant is a row in `grants`, and a member's points are the sum of their grants.

## The purchases file

`inbox/purchases-YYYYMMDD.csv`: `purchase_id`, `member_id`, `email`, `amount_cents`, `store`.

The tills of the older stores do not know member numbers: their rows have an empty `member_id`, and the member is found by the e-mail address. A purchase of nobody the database knows is left out.

Members of one household may share an e-mail address; each has a member number of their own.

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: every file in the inbox, granted and deleted |
| `purchases.py` | the purchases file |
| `members.py` | the SQLite database: members, grants, the rules |
| `inbox/` | where the purchases arrive |
| `data/` | the database (`members.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `POINTS_GRANT_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
20 2 * * * cd /opt/points-grant && python3 job.py
```

What the job prints is all that is kept of a run.
