# fx-rates

A scheduled job that takes over the day's exchange rates: for every currency the price lists need, it asks the rate feed for the latest rate and stores it in a database, where the price lists read it in the morning.

It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.

## Run it

```bash
python3 job.py     # take over the rates
python3 rates.py   # show the rates
```

The job prints `rates finished: OK` and exits with code 0 when the run is done. If it cannot run (no database, no list of currencies), it prints `rates failed: ...` on stderr and exits with code 2.

## The feed

The feed answers `GET /v2/latest/<currency>` with the rate (how much of the currency one euro buys) and the day it was published. It publishes once a day, in the evening.

- When the feed is busy it answers 502, 503 or 504 for a moment. The job asks again: up to 3 attempts for a currency, with a short wait in between (`FX_RATES_ATTEMPTS`, `FX_RATES_WAIT_SECONDS`, `FX_RATES_RETRY_STATUSES`).
- A currency the feed does not give (404, or still busy after the last attempt) keeps its stored rate, and the next run asks again.
- A rate that is not newer than the stored one changes nothing.
- A rate that moved more than 20% against the stored one is not taken over: it goes to the table `held`, for a person to look at.

There is no real feed here. The job starts a small stand-in on `127.0.0.1`, calls it, and stops it. What the stand-in knows is in `data/feed.json`: the day of its rates, the rates, and for which currencies it is busy.

Options: `--currencies PATH`, `--db PATH`, `--feed PATH`.

## How it is built

| File | Role |
|---|---|
| `job.py` | the entry point: every currency, asked and stored |
| `currencies.txt` | the currencies |
| `feed.py` | the call to the feed, and the stand-in |
| `retry.py` | asking again when the feed is busy |
| `rates.py` | the SQLite table of rates |
| `data/` | the stand-in's state (`feed.json`) and the database (`rates.db`) |

## Logging

The job is quiet by default, because cron mails every line a job prints. Set `FX_RATES_LOG_LEVEL` (`INFO`, `WARNING`, ...) to see more; log lines go to stderr.

## Scheduling

Every night with cron:

```
10 3 * * * cd /opt/fx-rates && python3 job.py
```

What the job prints is all that is kept of a run.
