"""freight-quote: quote the freight of tomorrow's shipments.

Meant to run on a schedule (see README.md)::

    python job.py

For every shipment on the dispatch list it asks the carrier for a rate and
writes the quote to the database. Exit code 0 means every shipment got a
carrier rate and the quotes were written. Exit code 1 means the carrier did not
price some shipments: nothing is written. Exit code 2 means the job could not run.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import carrier
import quotes
import shipments

HERE = Path(__file__).resolve().parent
DEFAULT_SHIPMENTS = HERE / "data" / "shipments.csv"
DEFAULT_CARRIER = HERE / "data" / "carrier.json"

log = logging.getLogger("freight_quote")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("FREIGHT_QUOTE_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def quote_all(base_url, todo):
    """One quote per shipment, in the order of the dispatch list.

    Returns (rows, failures). The carrier's rate is the price it charges, so a
    shipment it does not price gets no quote; it is listed in failures as
    (shipment_id, reason). Falling back to the contract rate card would quote
    below what the carrier charges (the card has no fuel surcharge and older
    prices).
    """
    rows, failures = [], []
    for shipment in todo:
        try:
            cents = carrier.rate(base_url, shipment)
        except Exception as exc:
            log.error("no carrier rate for %s: %s", shipment.shipment_id, exc)
            failures.append((shipment.shipment_id, str(exc)))
            continue
        rows.append(quotes.Quote.of(shipment, cents))
    return rows, failures


def main(argv=None):
    parser = argparse.ArgumentParser(description="Quote the freight of the shipments.")
    parser.add_argument("--shipments", default=DEFAULT_SHIPMENTS, help="the dispatch list")
    parser.add_argument("--db", default=quotes.DEFAULT_DB, help="the SQLite file")
    parser.add_argument("--carrier", default=DEFAULT_CARRIER, help="the stand-in's state")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        todo = shipments.read(args.shipments)
        conn = quotes.connect(args.db)
    except (OSError, ValueError) as exc:
        print(f"quotes failed: {exc}", file=sys.stderr)
        return 2

    with carrier.local_api(args.carrier) as base_url:
        log.info("asking %s for %d rates", base_url, len(todo))
        rows, failures = quote_all(base_url, todo)
    if failures:
        conn.close()
        first_id, first_reason = failures[0]
        print(
            f"quotes failed: no carrier rate for {len(failures)} of {len(todo)} "
            f"shipments ({first_id}: {first_reason}); nothing written",
            file=sys.stderr,
        )
        return 1
    quotes.replace_all(conn, rows)
    conn.close()
    log.info("%d quotes written", len(rows))
    print("quotes finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
