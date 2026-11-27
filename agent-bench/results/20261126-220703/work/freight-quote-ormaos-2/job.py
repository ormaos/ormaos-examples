"""freight-quote: quote the freight of tomorrow's shipments.

Meant to run on a schedule (see README.md)::

    python job.py

For every shipment on the dispatch list it asks the carrier for a rate and
writes the quote to the database. Exit code 0 means the quotes were written;
anything else means the job could not run, and the quotes were not touched.
"""

import argparse
import logging
import os
import sys
import urllib.error
from pathlib import Path

import carrier
import quotes
import ratecard
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


class CarrierRateError(RuntimeError):
    """The carrier gave no rate for a shipment; no quote may be guessed for it."""


def price(base_url, card, shipment):
    """The freight of one shipment, in cents, as the carrier prices it.

    There is no fallback to the contract rate card: the card has no fuel
    surcharge and older prices, so a quote from it is lower than what the
    carrier charges. If the carrier gives no rate, the job fails instead.
    """
    try:
        return carrier.rate(base_url, shipment)
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            reason = f"HTTP {exc.code} {exc.reason}"
        else:
            reason = f"{type(exc).__name__}: {exc}"
        raise CarrierRateError(
            f"no carrier rate for {shipment.shipment_id} ({shipment.lane}, "
            f"{shipment.chargeable_kg} kg, {shipment.service}): {reason}"
        ) from exc


def quote_all(base_url, card, todo):
    """One quote per shipment, in the order of the dispatch list."""
    rows = []
    for shipment in todo:
        cents = price(base_url, card, shipment)
        rows.append(quotes.Quote.of(shipment, cents))
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
        card = ratecard.load()
        conn = quotes.connect(args.db)
    except (OSError, ValueError) as exc:
        print(f"quotes failed: {exc}", file=sys.stderr)
        return 2

    with carrier.local_api(args.carrier) as base_url:
        log.info("asking %s for %d rates", base_url, len(todo))
        try:
            rows = quote_all(base_url, card, todo)
        except CarrierRateError as exc:
            conn.close()
            print(f"quotes failed: {exc}; no quotes written", file=sys.stderr)
            return 1
    quotes.replace_all(conn, rows)
    conn.close()
    log.info("%d quotes written", len(rows))
    print("quotes finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
