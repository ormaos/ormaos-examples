"""The catalog, in SQLite.

    python catalog.py                        # the catalog
    python catalog.py --compare LIST.csv     # next to a supplier list
    python catalog.py --create               # an empty catalog
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

import convert

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "catalog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1
);
"""


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def load(conn, staging):
    """Take over the prices of a converted list. Returns how many rows it had.

    A price of zero is how the supplier marks an article it no longer sells:
    the product becomes inactive and keeps its price. An article the catalog
    does not know is added inactive, for someone to give it a name.
    """
    rows = 0
    with open(staging, newline="", encoding="utf-8") as handle, conn:
        for row in csv.DictReader(handle):
            sku, cents = row["sku"], int(row["price_cents"])
            rows += 1
            if cents == 0:
                conn.execute("UPDATE products SET active = 0 WHERE sku = ?", (sku,))
                continue
            known = conn.execute("SELECT 1 FROM products WHERE sku = ?", (sku,)).fetchone()
            if known is None:
                conn.execute(
                    "INSERT INTO products (sku, name, price_cents, active) VALUES (?, '', ?, 0)",
                    (sku, cents),
                )
            else:
                conn.execute("UPDATE products SET price_cents = ? WHERE sku = ?", (cents, sku))
    return rows


def compare(conn, supplier_list):
    """Print every article whose catalog price is not the price of the list."""
    with open(supplier_list, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            listed = convert.piece_cents(convert.to_cents(row["price"]), row["pack"] or 1)
            found = conn.execute(
                "SELECT price_cents FROM products WHERE sku = ?", (row["article"].strip(),)
            ).fetchone()
            ours = found[0] if found else None
            if listed and ours != listed:
                print(f"{row['article']}  catalog {ours}  list {listed}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the catalog.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make an empty catalog")
    parser.add_argument("--compare", metavar="LIST", help="a supplier list")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if args.compare:
        compare(conn, args.compare)
    elif not args.create:
        for sku, name, cents, active in conn.execute("SELECT * FROM products ORDER BY sku"):
            print(f"{sku}  {cents / 100:9.2f}  {'' if active else 'inactive  '}{name}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
