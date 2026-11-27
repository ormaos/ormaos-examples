"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied; 1 means some orders were not
applied (they are listed on stderr); 2 means the sync could not run.
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

    Returns (applied, skipped): how many were applied now, and the orders that
    could not be applied, as (order, reason) pairs.
    """
    applied = 0
    skipped = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            log.warning("order %s skipped: %s", order.order_id, exc)
            skipped.append((order, exc))
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

    applied, skipped = sync_orders(conn, orders)
    conn.close()
    log.info("%d orders read, %d applied in this run", len(orders), applied)
    if skipped:
        # The sales API hands an order over only once: a skipped order is lost
        # unless it is reported here (cron mails this output).
        print(f"sync finished: {len(skipped)} order(s) NOT applied:", file=sys.stderr)
        for order, exc in skipped:
            print(
                f"  {order.order_id} placed_at={order.placed_at.isoformat()} "
                f"sku={order.sku!r} quantity={order.quantity} unit={order.unit}: {exc}",
                file=sys.stderr,
            )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
