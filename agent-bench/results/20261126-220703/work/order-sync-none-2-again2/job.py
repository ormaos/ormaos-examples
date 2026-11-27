"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes: 0 means every order was applied (or had been already); 1 means
the sync ran but some orders were rejected (they are listed on stderr and
saved under data/rejected/ so they can be fixed and replayed); 2 means it
could not run at all.
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
REJECTED_DIR = HERE / "data" / "rejected"

log = logging.getLogger("order_sync")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("ORDER_SYNC_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def load_orders(source, orders_csv):
    """Fetch the raw rows from the chosen source and parse them.

    Returns (orders, rejected): rejected is a list of (raw_row, reason) for the
    rows that could not be parsed. One bad row must not drop the whole batch:
    the sales API hands every order over only once.
    """
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
    (order, reason) for the orders that were not applied.
    """
    applied = 0
    rejected = []
    for order in orders:
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except Exception as exc:
            log.error("order %s rejected: %s", order.order_id, exc)
            rejected.append((order, str(exc)))
    return applied, rejected


def save_rejected(entries, directory=REJECTED_DIR):
    """Keep the raw data of rejected orders; the API will not send them again."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"rejected-{stamp}.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            [{"row": row, "reason": reason} for row, reason in entries],
            handle,
            indent=2,
            default=str,
        )
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync orders into the inventory.")
    parser.add_argument("--source", choices=("csv", "api"), default="csv")
    parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
    parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = inventory.connect(args.db)
        orders, bad_rows = load_orders(args.source, args.orders)
    except (OSError, ValueError, KeyError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    applied, bad_orders = sync_orders(conn, orders)
    conn.close()
    log.info("%d orders read, %d applied in this run", len(orders), applied)

    rejected = list(bad_rows) + [(order.raw, reason) for order, reason in bad_orders]
    if rejected:
        try:
            saved = f"saved to {save_rejected(rejected)}"
        except OSError as exc:
            saved = f"could NOT be saved ({exc}); raw rows follow"
            for row, _ in rejected:
                print(json.dumps(row, default=str), file=sys.stderr)
        print(
            f"sync finished with errors: {len(rejected)} order(s) rejected, "
            f"{applied} applied; {saved}",
            file=sys.stderr,
        )
        for row, reason in rejected:
            order_id = row.get("order_id", "?") if isinstance(row, dict) else "?"
            print(f"  rejected {order_id}: {reason}", file=sys.stderr)
        return 1

    print("sync finished: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
