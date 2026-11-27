"""freight-quote: quote the freight of tomorrow's shipments.

Meant to run on a schedule (see README.md)::

    python job.py

For every shipment on the dispatch list it asks the carrier for a rate and
writes the quote to the database. Exit code 0 means the quotes were written;
anything else means they were not (2: the job could not start, 1: the carrier
gave no rate for some shipment, and the previous quotes were left in place).
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


class CarrierRateError(Exception):
    """The carrier gave no rate for a shipment."""


def price(base_url, shipment):
    """The freight of one shipment, in cents, as the carrier charges it.

    There is deliberately no fallback to the contract rate card: the card
    lags the carrier's tariff (no fuel surcharge, older prices), so a quote
    from it is lower than what the carrier charges. A shipment without a
    carrier rate fails the run instead.
    """
    try:
        return carrier.rate(base_url, shipment)
    except Exception as exc:
        raise CarrierRateError(f"no carrier rate for {shipment.shipment_id}: {exc}") from exc


def quote_all(base_url, todo):
    """One quote per shipment, in the order of the dispatch list."""
    return [quotes.Quote.of(shipment, price(base_url, shipment)) for shipment in todo]


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
        except CarrierRateError as exc:
            # Keep the previous quotes rather than write a partial or wrong set.
            conn.close()
            print(f"quotes failed: {exc}", file=sys.stderr)
            return 1
    quotes.replace_all(conn, rows)
    conn.close()
    log.info("%d quotes written", len(rows))
    print("quotes finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
