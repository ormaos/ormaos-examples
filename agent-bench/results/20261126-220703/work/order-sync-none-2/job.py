"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes: 0 the sync finished and every order was applied; 1 the sync
finished but some orders were skipped (listed on stderr); 2 it could not run.
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import fetch
import inventory
import parse
import validate

HERE = Path(__file__).resolve().parent
DEFAULT_ORDERS = HERE / "data" / "orders.csv"
# The sales API hands every order over only once, so keep what it sent:
# an order that is skipped can be fixed and applied later from this copy.
FETCHED_DIR = HERE / "data" / "fetched"

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def load_orders(source, orders_csv):
    """Fetch the raw rows from the chosen source and parse them."""
    if source == "api":
        with fetch.local_api(orders_csv) as base_url:
            log.info("fetching orders from %s", base_url)
            rows = fetch.from_api(base_url)
        save_fetched(rows)
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    return parse.parse_rows(rows)


def save_fetched(rows):
    """Keep a copy of the raw rows the API handed over (it will not resend them)."""
    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = FETCHED_DIR / f"orders-{stamp}.csv"
    columns = list(parse.FIELDS) + ["unit"]
    for row in rows:
        columns += [key for key in row if key not in columns]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    log.info("saved the fetched orders in %s", path)
    return path


def sync_orders(conn, orders):
    """Apply every order to the inventory.

    Returns (applied, skipped): how many were applied now, and a list of
    (order_id, reason) for the orders that could not be applied.
    """
    applied = 0
    skipped = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            log.info("order %s skipped: %s", order.order_id, exc)
            skipped.append((order.order_id, str(exc)))
    return applied, skipped


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        orders = load_orders(args.source, args.orders)
    except (OSError, parse.ParseError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    try:
        applied, skipped = sync_orders(conn, orders)
    finally:
        conn.close()
    log.info("%d orders read, %d applied in this run", len(orders), applied)
    if skipped:
        for order_id, reason in skipped:
            print(f"order {order_id} skipped: {reason}", file=sys.stderr)
        print(
            f"sync finished: {len(skipped)} of {len(orders)} orders SKIPPED",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
