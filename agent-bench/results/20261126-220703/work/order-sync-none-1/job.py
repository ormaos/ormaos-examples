"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied. Exit code 1 means some orders were
rejected (kept in the rejected_orders table, not applied). Exit code 2 means
the job could not run.
"""

import argparse
import json
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
            return fetch.from_api(base_url)
    log.info("reading orders from %s", orders_csv)
    return fetch.from_csv(orders_csv)


def reject(conn, row, exc):
    """Keep a row that could not be applied and say so loudly.

    The sales API hands an order over only once: a row dropped here would be
    lost for good, so it goes to the rejected_orders table instead.
    """
    order_id = row.get("order_id") if isinstance(row, dict) else None
    reason = f"{type(exc).__name__}: {exc}"
    log.error("order %s rejected: %s", order_id, reason)
    inventory.record_rejected(
        conn, order_id, json.dumps(row, default=str, sort_keys=True), reason
    )


def sync_orders(conn, rows):
    """Parse, check and apply every row.

    Returns (applied, rejected): how many orders were applied now and how
    many were rejected (and kept in rejected_orders).
    """
    parsed = []
    rejected = 0
    for row in rows:
        try:
            order = parse.parse_row(row)
            validate.check_order(order)
        except (parse.ParseError, validate.ValidationError) as exc:
            reject(conn, row, exc)
            rejected += 1
            continue
        parsed.append((order, row))
    parsed.sort(key=lambda item: (item[0].placed_at, item[0].order_id))

    applied = 0
    for order, row in parsed:
        try:
            if inventory.apply_order(conn, order):
                applied += 1
        except inventory.UnknownSkuError as exc:
            reject(conn, row, exc)
            rejected += 1
    return applied, rejected


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
    except OSError as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    applied, rejected = sync_orders(conn, rows)
    conn.close()
    log.info(
        "%d orders read, %d applied in this run, %d rejected",
        len(rows), applied, rejected,
    )
    if rejected:
        print(
            f"sync finished: {rejected} order(s) REJECTED and not applied; "
            "see the rejected_orders table",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
