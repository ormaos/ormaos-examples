"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied (or had been already).
Exit code 1 means the sync ran but some orders were rejected: they are kept in
the table ``rejected_orders`` and listed on stderr, and need a look.
Exit code 2 means the job could not run.
"""

import argparse
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


def reject(conn, rejected, order_id, raw, exc):
    """Keep a rejected order so it is not lost, and report it."""
    reason = f"{type(exc).__name__}: {exc}"
    log.error("order %s rejected: %s", order_id, reason)
    inventory.record_rejected(conn, order_id, raw, reason)
    rejected.append((order_id, reason))


def sync_orders(conn, rows):
    """Parse, check and apply every row.

    Returns (orders read, orders applied now, rejected [(order_id, reason)]).
    A row that cannot be parsed, checked or applied does not stop the others;
    it is stored in ``rejected_orders`` with the raw data, because the sales
    API will not hand it over again.
    """
    orders, rejected = [], []
    for row in rows:
        try:
            orders.append((parse.parse_row(row), row))
        except parse.ParseError as exc:
            reject(conn, rejected, row.get("order_id"), row, exc)
    orders.sort(key=lambda pair: (pair[0].placed_at, pair[0].order_id))

    applied = 0
    for order, row in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            reject(conn, rejected, order.order_id, row, exc)
    return len(rows), applied, rejected


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        rows = load_rows(args.source, args.orders)
    except (OSError, ValueError, KeyError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    read, applied, rejected = sync_orders(conn, rows)
    conn.close()
    log.info("%d orders read, %d applied in this run", read, applied)
    if rejected:
        for order_id, reason in rejected:
            print(f"rejected order {order_id}: {reason}", file=sys.stderr)
        print(
            f"sync finished: {len(rejected)} of {read} orders REJECTED "
            f"(kept in table rejected_orders), {applied} applied"
        )
        return 1
    print(f"sync finished: OK ({read} read, {applied} applied)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
