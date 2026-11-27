"""fx-rates: take over today's exchange rates from the feed.

Meant to run on a schedule (see README.md)::

    python job.py

For every currency in currencies.txt it asks the feed for the latest rate
and stores it. Exit code 0 means the run is done; anything else means the
job could not run.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import feed
import rates
import retry

HERE = Path(__file__).resolve().parent
DEFAULT_CURRENCIES = HERE / "currencies.txt"
DEFAULT_FEED = HERE / "data" / "feed.json"

log = logging.getLogger("fx_rates")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("FX_RATES_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def read_currencies(path):
    with open(path, encoding="utf-8") as handle:
        lines = [line.strip() for line in handle]
    return [line for line in lines if line and not line.startswith("#")]


def update(conn, base_url, currency):
    """Take over the rate of one currency. Returns what became of it."""
    try:
        text, published = retry.call(feed.latest, base_url, currency)
    except feed.FeedError as error:
        # The stored rate stays; the next run asks again.
        log.warning("%s keeps its rate: %s", currency, error)
        return "kept"
    return rates.store(conn, currency, rates.to_micros(text), published)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Take over the rates of the feed.")
    parser.add_argument("--currencies", default=DEFAULT_CURRENCIES)
    parser.add_argument("--db", default=rates.DEFAULT_DB, help="the SQLite file")
    parser.add_argument("--feed", default=DEFAULT_FEED, help="the stand-in's state")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        wanted = read_currencies(args.currencies)
        conn = rates.connect(args.db)
    except OSError as exc:
        print(f"rates failed: {exc}", file=sys.stderr)
        return 2

    outcome = {}
    with feed.local_api(args.feed) as base_url:
        for currency in wanted:
            outcome[currency] = update(conn, base_url, currency)
    conn.close()
    log.info("outcome: %s", outcome)
    print("rates finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
