"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes: 0 the sync finished and every order was applied; 1 the sync
finished but some orders were rejected (see data/rejected.jsonl); 2 it could
not run.
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
# The sales API hands each order over only once, so every batch it returns is
# kept on disk before anything else happens, and every order that could not be
# applied is written out with the reason, so it can be fixed and replayed.
DEFAULT_INBOX = HERE / "data" / "inbox"
DEFAULT_REJECTED = HERE / "data" / "rejected.jsonl"

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def fetch_rows(source, orders_csv, inbox):
    """Fetch the raw rows from the chosen source.

    Rows from the API are saved in ``inbox`` first: the API will not send them
    again, so this copy is the only one left if anything below goes wrong.
    """
    if source == "api":
        with fetch.local_api(orders_csv) as base_url:
            log.info("fetching orders from %s", base_url)
            rows = fetch.from_api(base_url)
        inbox = Path(inbox)
        inbox.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        saved = inbox / f"orders-{stamp}.json"
        saved.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        log.info("saved %d raw orders to %s", len(rows), saved)
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    return rows


def parse_orders(rows):
    """Parse each row on its own. Returns (orders oldest first, rejected)."""
    orders, rejected = [], []
    for row in rows:
        try:
            orders.append(parse.parse_row(row))
        except parse.ParseError as exc:
            rejected.append((row, exc))
    orders.sort(key=lambda order: (order.placed_at, order.order_id))
    return orders, rejected


def sync_orders(conn, orders):
    """Apply every order to the inventory.

    Returns (how many were applied now, [(order, error), ...] not applied).
    """
    applied = 0
    rejected = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
            rejected.append((order, exc))
    return applied, rejected


def record_rejected(path, rejected):
    """Append the rejected orders, with the reason, to a JSON-lines file."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(path, "a", encoding="utf-8") as handle:
        for item, exc in rejected:
            if isinstance(item, parse.Order):
                row = {**vars(item), "placed_at": item.placed_at.isoformat()}
            else:
                row = dict(item)
            entry = {"rejected_at": now, "reason": str(exc), "order": row}
            handle.write(json.dumps(entry) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    parser.add_argument("--inbox", default=DEFAULT_INBOX,
                        help="where raw API batches are saved")
    parser.add_argument("--rejected", default=DEFAULT_REJECTED,
                        help="where orders that could not be applied are written")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        rows = fetch_rows(args.source, args.orders, args.inbox)
    except OSError as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    orders, rejected = parse_orders(rows)
    applied, not_applied = sync_orders(conn, orders)
    conn.close()
    rejected += not_applied
    log.info("%d orders read, %d applied in this run", len(rows), applied)

    if rejected:
        record_rejected(args.rejected, rejected)
        for item, exc in rejected:
            order_id = getattr(item, "order_id", None) or dict(item).get("order_id")
            print(f"order {order_id} rejected: {exc}", file=sys.stderr)
        print(
            f"sync finished: {len(rejected)} of {len(rows)} orders REJECTED, "
            f"written to {args.rejected}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
