"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes:
  0  every order fetched was applied (or had been applied before);
  1  the sync ran, but some orders were rejected: they are listed on stderr and
     saved to data/rejected.csv, from where they can be replayed with
     ``python job.py --orders data/rejected.csv`` once they are corrected;
  2  the sync could not run.
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

import fetch
import inventory
import parse
import validate

HERE = Path(__file__).resolve().parent
DEFAULT_ORDERS = HERE / "data" / "orders.csv"
DEFAULT_REJECTED = HERE / "data" / "rejected.csv"
REJECTED_FIELDS = parse.FIELDS + ("unit", "reason")

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def load_rows(source, orders_csv):
    """Fetch the raw rows from the chosen source."""
    if source == "api":
        with fetch.local_api(orders_csv) as base_url:
            log.info("fetching orders from %s", base_url)
            rows = fetch.from_api(base_url)
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    return rows


def parse_all(rows):
    """Parse every row. Returns (orders oldest first, [(row, reason)] rejected).

    A bad row must not abort the run: the API hands every order over only
    once, so the good ones have to be applied and the bad ones kept.
    """
    orders, rejected = [], []
    for row in rows:
        try:
            orders.append((parse.parse_row(row), row))
        except parse.ParseError as exc:
            rejected.append((row, str(exc)))
    orders.sort(key=lambda pair: (pair[0].placed_at, pair[0].order_id))
    return orders, rejected


def sync_orders(conn, orders):
    """Apply every order. Returns (how many were applied now, [(row, reason)])."""
    applied = 0
    rejected = []
    for order, row in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            rejected.append((row, str(exc)))
    return applied, rejected


def save_rejected(path, rejected):
    """Append the rejected rows to a CSV that job.py can read back as orders."""
    path = Path(path)
    new_file = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REJECTED_FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for row, reason in rejected:
            writer.writerow({**row, "reason": reason})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    parser.add_argument(
        "--rejected", default=DEFAULT_REJECTED, help="where rejected orders are saved"
    )
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        rows = load_rows(args.source, args.orders)
    except (OSError, ValueError, KeyError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    orders, rejected = parse_all(rows)
    applied, not_applied = sync_orders(conn, orders)
    conn.close()
    rejected += not_applied
    log.info("%d orders read, %d applied in this run", len(rows), applied)
    if rejected:
        try:
            save_rejected(args.rejected, rejected)
            where = f"saved to {args.rejected}"
        except OSError as exc:
            where = f"could NOT be saved ({exc}); the rows are above"
        for row, reason in rejected:
            print(f"rejected: {dict(row)}: {reason}", file=sys.stderr)
        print(
            f"sync finished: {len(rejected)} of {len(rows)} orders REJECTED, {where}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
