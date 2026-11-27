"""freight-quote: quote the freight of tomorrow's shipments.

Meant to run on a schedule (see README.md)::

    python job.py

For every shipment on the dispatch list it asks the carrier for a rate and
writes the quote to the database. Exit code 0 means the quotes were written;
1 means the carrier refused some rates and nothing was written; 2 means the
job could not run.
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


class CarrierRefused(Exception):
    """The carrier gave no rate for some shipments: {shipment_id: reason}."""

    def __init__(self, failures):
        super().__init__(f"no carrier rate for {len(failures)} shipment(s)")
        self.failures = failures


def quote_all(base_url, todo):
    """One quote per shipment, in the order of the dispatch list.

    Every quote is the carrier's own rate. There is no fallback to the
    contract rate card: the card is not what the carrier charges today, and a
    quote from it would be silently wrong. If the carrier refuses any
    shipment, raise CarrierRefused and quote nothing.
    """
    rows, failures = [], {}
    for shipment in todo:
        try:
            cents = carrier.rate(base_url, shipment)
        except Exception as exc:
            failures[shipment.shipment_id] = exc
            continue
        rows.append(quotes.Quote.of(shipment, cents))
    if failures:
        raise CarrierRefused(failures)
    return rows


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
        try:
            rows = quote_all(base_url, todo)
        except CarrierRefused as exc:
            conn.close()
            for shipment_id, reason in exc.failures.items():
                print(f"  {shipment_id}: {reason}", file=sys.stderr)
            print(f"quotes failed: {exc} of {len(todo)}; no quotes written",
                  file=sys.stderr)
            return 1
    quotes.replace_all(conn, rows)
    conn.close()
    log.info("%d quotes written", len(rows))
    print("quotes finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
