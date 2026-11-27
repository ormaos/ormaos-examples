"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes:

- 0: the sync finished and every order was applied (or had been already);
- 1: the sync finished, but some orders were skipped (listed on stderr; the
  raw orders of the run are kept in data/received/ so they can be replayed);
- 2: the sync could not run.
"""

import argparse
import json
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
RECEIVED_DIR = HERE / "data" / "received"

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def keep_received(rows, source, received_dir=RECEIVED_DIR):
    """Write the raw rows to disk before anything else can fail.

    The sales API hands every order over only once, so if an order is
    rejected (or the parse fails) this file is the only copy left of it.
    """
    received_dir = Path(received_dir)
    received_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = received_dir / f"{stamp}-{source}.json"
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return path


def load_orders(source, orders_csv):
    """Fetch the raw rows from the chosen source, keep a copy, and parse them."""
    if source == "api":
        with fetch.local_api(orders_csv) as base_url:
            log.info("fetching orders from %s", base_url)
            rows = fetch.from_api(base_url)
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    kept = keep_received(rows, source)
    log.info("raw orders kept in %s", kept)
    return parse.parse_rows(rows)


def sync_orders(conn, orders):
    """Apply every order to the inventory.

    Returns (applied, skipped): how many were applied now, and a list of
    (order, reason) for the orders that were not applied because of an error.
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
        for order, exc in skipped:
            print(f"order {order.order_id} skipped: {exc}", file=sys.stderr)
        print(
            f"sync finished: {len(skipped)} of {len(orders)} orders SKIPPED "
            f"(raw orders kept in {RECEIVED_DIR})",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
