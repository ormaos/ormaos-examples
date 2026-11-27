"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means the sync finished; anything else means it could not run.
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
# Orders that could not be applied. The sales API hands an order over only
# once, so a rejected order is kept here (in the export's format) to be fixed
# and replayed with: python3 job.py --orders data/rejected_orders.csv
DEFAULT_REJECTED = HERE / "data" / "rejected_orders.csv"
REJECTED_FIELDS = ("order_id", "placed_at", "sku", "quantity", "channel", "unit", "reason")

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

    Returns (applied, rejected): how many were applied now, and a list of
    (order, reason) for the orders that break a rule or name an unknown SKU.
    Any other error is not an order problem and stops the job.
    """
    applied = 0
    rejected = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            log.error("order %s rejected: %s", order.order_id, exc)
            rejected.append((order, str(exc)))
    return applied, rejected


def save_rejected(path, rejected):
    """Append the rejected orders to a CSV that job.py can read back."""
    path = Path(path)
    already = set()
    if path.exists():
        with open(path, newline="", encoding="utf-8") as handle:
            already = {row["order_id"] for row in csv.DictReader(handle)}
    new = [(o, reason) for o, reason in rejected if o.order_id not in already]
    if not new:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(REJECTED_FIELDS)
        for o, reason in new:
            writer.writerow(
                (o.order_id, o.placed_at.isoformat(timespec="minutes"), o.sku,
                 o.quantity, o.channel, o.unit, reason)
            )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    parser.add_argument(
        "--rejected", default=DEFAULT_REJECTED, help="where rejected orders are kept"
    )
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        orders = load_orders(args.source, args.orders)
    except (OSError, parse.ParseError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    applied, rejected = sync_orders(conn, orders)
    conn.close()
    log.info("%d orders read, %d applied in this run", len(orders), applied)
    if rejected:
        save_rejected(args.rejected, rejected)
        ids = ", ".join(order.order_id for order, _ in rejected)
        print(
            f"sync finished: {len(rejected)} orders REJECTED ({ids}); "
            f"kept in {args.rejected}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
