"""The inventory: stock levels in a local SQLite database.

Run this file to see the stock levels::

    python inventory.py
"""

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "inventory.db"

SCHEMA = """
CREATE TABLE stock (
    sku      TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    on_hand  INTEGER NOT NULL
);
CREATE TABLE applied_orders (
    order_id    TEXT PRIMARY KEY,
    sku         TEXT NOT NULL REFERENCES stock (sku),
    quantity    INTEGER NOT NULL,
    applied_at  TEXT NOT NULL
);
"""


class UnknownSkuError(LookupError):
    """The order names a SKU that the warehouse does not stock."""


def connect(db_path=DEFAULT_DB):
    if not Path(db_path).exists():
        raise FileNotFoundError(f"{db_path} does not exist; run ./reset.sh first")
    return sqlite3.connect(db_path)


def create(db_path, stock_csv):
    """Create a new database with the stock levels from a CSV file."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with open(stock_csv, newline="", encoding="utf-8") as handle:
        rows = [(r["sku"], r["name"], int(r["on_hand"])) for r in csv.DictReader(handle)]
    conn = sqlite3.connect(db_path)
    with conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO stock (sku, name, on_hand) VALUES (?, ?, ?)", rows)
    conn.close()
    return len(rows)


def apply_order(conn, order):
    """Take the order's quantity out of stock.

    Returns False if this order was already applied by an earlier run, so the
    job can run again over the same export without counting an order twice.
    """
    found = conn.execute(
        "SELECT on_hand FROM stock WHERE sku = ?", (order.sku,)
    ).fetchone()
    if found is None:
        raise UnknownSkuError(f"SKU {order.sku!r} is not in the inventory")
    seen = conn.execute(
        "SELECT 1 FROM applied_orders WHERE order_id = ?", (order.order_id,)
    ).fetchone()
    if seen is not None:
        return False
    with conn:
        conn.execute(
            "UPDATE stock SET on_hand = on_hand - ? WHERE sku = ?",
            (order.quantity, order.sku),
        )
        conn.execute(
            "INSERT INTO applied_orders (order_id, sku, quantity, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (
                order.order_id,
                order.sku,
                order.quantity,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
    return True


def stock_levels(conn):
    """Return (sku, name, on_hand) for every item, ordered by SKU."""
    return conn.execute("SELECT sku, name, on_hand FROM stock ORDER BY sku").fetchall()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show or rebuild the inventory.")
    parser.add_argument("--db", default=DEFAULT_DB, help="path of the SQLite file")
    parser.add_argument(
        "--create-from",
        metavar="STOCK_CSV",
        help="rebuild the database from a stock CSV (sku,name,on_hand)",
    )
    args = parser.parse_args(argv)
    if args.create_from:
        count = create(args.db, args.create_from)
        print(f"inventory: {count} items loaded into {args.db}")
        return 0
    try:
        conn = connect(args.db)
    except FileNotFoundError as exc:
        print(f"inventory: {exc}", file=sys.stderr)
        return 2
    print(f"{'SKU':<10} {'ITEM':<22} {'ON HAND':>7}")
    for sku, name, on_hand in stock_levels(conn):
        print(f"{sku:<10} {name:<22} {on_hand:>7}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
