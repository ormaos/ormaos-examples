"""order-sync: apply the orders from the sales system to the inventory.

Meant to run on a schedule (see README.md)::

    python job.py                 # read the CSV export
    python job.py --source api    # ask the sales API instead

Exit codes:

- 0: every order was applied (or had been applied before);
- 1: the sync ran, but some orders were rejected. They are written to
  data/rejected/ (same columns as the CSV export, plus ``error``) and listed on
  stderr. The sales API does not hand an order over twice, so that file is the
  only copy: fix the rows and replay it with ``python3 job.py --orders FILE``;
- 2: the sync could not run.
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import fetch
import inventory
import parse
import validate

HERE = Path(__file__).resolve().parent
DEFAULT_ORDERS = HERE / "data" / "orders.csv"
REJECTED_DIR = HERE / "data" / "rejected"
CSV_COLUMNS = parse.FIELDS + ("unit",)

# Errors that mean "this one order is wrong"; anything else stops the run.
ORDER_ERRORS = (validate.ValidationError, inventory.UnknownSkuError)

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


def sync_orders(conn, orders, raw_by_id):
    """Apply every order to the inventory.

    Returns (applied now, [(raw_row, error)] for the orders that were rejected).
    If something other than a bad order goes wrong, the orders not applied yet
    are returned as rejected too, so none of them is lost.
    """
    applied = 0
    rejected = []
    for index, order in enumerate(orders):
        try:
            validate.check_order(order)
            if inventory.apply_order(conn, order):
                applied += 1
        except ORDER_ERRORS as exc:
            log.error("order %s rejected: %s", order.order_id, exc)
            rejected.append((raw_by_id[order.order_id], exc))
        except Exception as exc:  # database or program error: stop, keep the rest
            log.error("sync stopped at order %s: %s", order.order_id, exc)
            for left in orders[index:]:
                rejected.append((raw_by_id[left.order_id], f"not applied: {exc}"))
            break
    return applied, rejected


def save_rejected(rejected, directory=REJECTED_DIR):
    """Write the rejected rows to a CSV that job.py can read again."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"rejected-{datetime.now():%Y%m%dT%H%M%S}.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=CSV_COLUMNS + ("error",), extrasaction="ignore"
        )
        writer.writeheader()
        for row, error in rejected:
            writer.writerow({**{k: row.get(k, "") for k in CSV_COLUMNS}, "error": str(error)})
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
        rows = load_rows(args.source, args.orders)
    except OSError as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 2

    # The API hands every order over only once: from here on, every row must
    # end up either applied or saved in data/rejected/.
    orders, rejected = parse.parse_rows_lenient(rows)
    for row, exc in rejected:
        log.error("row rejected: %s", exc)
    raw_by_id = {}
    for row in rows:
        raw_by_id.setdefault((row.get("order_id") or "").strip(), row)
    applied, not_applied = sync_orders(conn, orders, raw_by_id)
    rejected += not_applied
    conn.close()
    log.info("%d orders read, %d applied in this run", len(rows), applied)

    if rejected:
        path = save_rejected(rejected)
        print(
            f"sync finished with {len(rejected)} of {len(rows)} orders REJECTED "
            f"(saved to {path}):",
            file=sys.stderr,
        )
        for row, error in rejected:
            print(f"  {row.get('order_id', '?')}: {error}", file=sys.stderr)
        return 1
    print("sync finished: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
