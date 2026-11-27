"""freight-quote: quote the freight of tomorrow's shipments.

Meant to run on a schedule (see README.md)::

    python job.py

For every shipment on the dispatch list it asks the carrier for a rate and
writes the quote to the database. Exit code 0 means the quotes were written;
anything else means the job could not run.
"""

import argparse
import logging
import os
import sys
import urllib.error
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


class CarrierRateError(RuntimeError):
    """The carrier did not price a shipment, so it cannot be quoted."""


def price(base_url, shipment):
    """The freight of one shipment, in cents, as the carrier charges it.

    There is no fallback: the contract rate card is not what the carrier
    charges today (its tariff and fuel surcharge change), so a quote from the
    card would be wrong, and usually too low.
    """
    try:
        return carrier.rate(base_url, shipment)
    except urllib.error.HTTPError as exc:
        raise CarrierRateError(f"{shipment.shipment_id}: carrier answered {exc.code} {exc.reason}") from exc
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        raise CarrierRateError(f"{shipment.shipment_id}: no carrier rate: {exc!r}") from exc


def quote_all(base_url, todo):
    """One quote per shipment, in the order of the dispatch list.

    Returns (rows, failures). Stops asking once the carrier says the
    account's calls for the day are used up (429): the rest would fail too.
    """
    rows, failures = [], []
    for index, shipment in enumerate(todo):
        try:
            cents = price(base_url, shipment)
        except CarrierRateError as exc:
            failures.append(str(exc))
            cause = exc.__cause__
            if isinstance(cause, urllib.error.HTTPError) and cause.code == 429:
                rest = todo[index + 1:]
                if rest:
                    failures.append(f"{len(rest)} more not asked: daily call quota used up")
                break
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
        # Write nothing: a partial or made-up table would be invoiced as if right.
        conn.close()
        print(f"quotes failed: {len(todo) - len(rows)} of {len(todo)} shipments "
              f"have no carrier rate; no quotes written", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 2
    quotes.replace_all(conn, rows)
    conn.close()
    log.info("%d quotes written", len(rows))
    print("quotes finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
