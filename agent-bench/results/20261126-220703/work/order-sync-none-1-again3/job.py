"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit code 0 means every order was applied (or had been already); 1 means the
sync ran but some orders were skipped (they are logged and kept in
data/rejected.jsonl); 2 means it could not run.
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
# The sales API hands every order over only once, so whatever it returns is
# written here before anything else happens: a rejected order can be fixed and
# replayed instead of being lost.
FETCHED_DIR = HERE / "data" / "fetched"
REJECTED_FILE = HERE / "data" / "rejected.jsonl"

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_fetched(rows):
    """Keep a copy of what the API handed over. Returns the file path."""
    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = FETCHED_DIR / f"orders-{stamp}.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"fetched_at": _now(), "orders": rows}, handle, indent=1)
    return path


def load_rows(source, orders_csv):
    """Fetch the raw rows from the chosen source."""
    if source == "api":
        with fetch.local_api(orders_csv) as base_url:
            log.info("fetching orders from %s", base_url)
            rows = fetch.from_api(base_url)
        log.info("saved the fetched orders to %s", save_fetched(rows))
    else:
        log.info("reading orders from %s", orders_csv)
        rows = fetch.from_csv(orders_csv)
    return rows


def parse_all(rows):
    """Parse every row. Returns (orders oldest first, [(row, reason)])."""
    orders, bad = [], []
    for row in rows:
        try:
            orders.append(parse.parse_row(row))
        except parse.ParseError as exc:
            bad.append((row, f"parse error: {exc}"))
    orders.sort(key=lambda order: (order.placed_at, order.order_id))
    return orders, bad


def record_rejected(rejected):
    """Append rejected orders to REJECTED_FILE so they can be fixed and replayed."""
    if not rejected:
        return
    REJECTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REJECTED_FILE, "a", encoding="utf-8") as handle:
        for row, reason in rejected:
            entry = {"rejected_at": _now(), "reason": reason, "row": row}
            handle.write(json.dumps(entry) + "\n")


def sync_orders(conn, orders):
    """Apply every order. Returns (applied now, [(order, reason)] skipped)."""
    applied = 0
    skipped = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except Exception as exc:
            log.error("order %s skipped: %s", order.order_id, exc)
            skipped.append((order, str(exc)))
    return applied, skipped


def _raw_row(order, rows):
    for row in rows:
        if str(row.get("order_id", "")).strip() == order.order_id:
            return row
    return {"order_id": order.order_id}


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

    orders, rejected = parse_all(rows)
    for row, reason in rejected:
        log.error("order %s skipped: %s", row.get("order_id") or "?", reason)
    applied, skipped = sync_orders(conn, orders)
    conn.close()
    rejected += [(_raw_row(order, rows), reason) for order, reason in skipped]
    record_rejected(rejected)
    log.info("%d orders read, %d applied in this run", len(rows), applied)

    if rejected:
        ids = ", ".join(str(row.get("order_id") or "?") for row, _ in rejected)
        print(
            f"sync finished: {len(rejected)} of {len(rows)} orders SKIPPED ({ids}); "
            f"see {REJECTED_FILE}",
            file=sys.stderr,
        )
        return 1
    print("sync finished: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
