"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied; 1 means the sync ran but some
orders were skipped (listed on stderr and kept in data/skipped_orders.csv);
2 means it could not run.
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
DEFAULT_SKIPPED = HERE / "data" / "skipped_orders.csv"
SKIPPED_FIELDS = ("order_id", "placed_at", "sku", "quantity", "channel", "unit", "reason")

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
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    return parse.parse_rows(rows)


def sync_orders(conn, orders):
    """Apply every order to the inventory.

    Returns (applied, skipped): how many were applied now, and a list of
    (order, reason) for the orders that could not be applied.
    """
    applied = 0
    skipped = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except Exception as exc:
            log.warning("order %s skipped: %s", order.order_id, exc)
            skipped.append((order, str(exc)))
    return applied, skipped


def save_skipped(path, skipped):
    """Append the skipped orders to a CSV that `job.py --orders` can read again.

    The sales API hands an order over only once, so this file is the only
    copy left of an order the job could not apply.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(SKIPPED_FIELDS)
        for order, reason in skipped:
            writer.writerow([
                order.order_id,
                order.placed_at.isoformat(timespec="minutes"),
                order.sku,
                order.quantity,
                order.channel,
                order.unit,
                reason,
            ])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    parser.add_argument(
        "--skipped", default=DEFAULT_SKIPPED, help="CSV where skipped orders are kept"
    )
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        orders = load_orders(args.source, args.orders)
    except (OSError, parse.ParseError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    applied, skipped = sync_orders(conn, orders)
    conn.close()
    log.info("%d orders read, %d applied in this run", len(orders), applied)
    if skipped:
        # Always shown, whatever the log level: cron mails it, and the API
        # will not send these orders again.
        for order, reason in skipped:
            print(f"order {order.order_id} skipped: {reason}", file=sys.stderr)
        try:
            save_skipped(args.skipped, skipped)
            where = f"saved to {args.skipped}"
        except OSError as exc:
            where = f"could not be saved ({exc})"
        print(
            f"sync finished: {len(skipped)} of {len(orders)} orders skipped, {where}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
