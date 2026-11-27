"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied (or had been already); 1 means the
sync ran but some orders were skipped (they are listed on stderr and saved in
data/rejected_orders.jsonl, because the sales API does not hand them over
again); 2 means it could not run.
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
DEFAULT_REJECTED = HERE / "data" / "rejected_orders.jsonl"

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
    (order, reason) for the orders that were refused.
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
            skipped.append((order, str(exc)))
    return applied, skipped


def save_rejected(path, skipped):
    """Append the skipped orders to a JSON-lines file, so they are not lost."""
    with open(path, "a", encoding="utf-8") as handle:
        for order, reason in skipped:
            record = {
                "order_id": order.order_id,
                "placed_at": order.placed_at.isoformat(),
                "sku": order.sku,
                "quantity": order.quantity,
                "channel": order.channel,
                "unit": order.unit,
                "reason": reason,
            }
            handle.write(json.dumps(record) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    parser.add_argument(
        "--rejected", default=DEFAULT_REJECTED, help="where skipped orders are saved"
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
        save_rejected(args.rejected, skipped)
        for order, reason in skipped:
            print(f"order {order.order_id} skipped: {reason}", file=sys.stderr)
        print(
            f"sync finished: {len(skipped)} of {len(orders)} orders skipped, "
            f"saved in {args.rejected}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
