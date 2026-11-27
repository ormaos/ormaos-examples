"""The rates table, in SQLite.

    python rates.py            # the rates
    python rates.py --create   # an empty table
"""

import argparse
import sqlite3
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "rates.db"
MICROS = 1_000_000
# A rate that moves more than this against the stored one is not taken over.
MAX_MOVE_PERCENT = 20

SCHEMA = """
CREATE TABLE IF NOT EXISTS rates (
    currency    TEXT PRIMARY KEY,
    rate_micros INTEGER NOT NULL,
    published   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS held (
    currency    TEXT NOT NULL,
    rate_micros INTEGER NOT NULL,
    published   TEXT NOT NULL,
    PRIMARY KEY (currency, published)
);
"""


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def to_micros(text):
    """``"1.0832"`` -> 1083200. Raises ValueError for anything not above zero."""
    value = int(Decimal(text) * MICROS)
    if value <= 0:
        raise ValueError(f"not a rate: {text!r}")
    return value


def store(conn, currency, rate_micros, published):
    """Take over one rate. Returns "stored", "held" or "older".

    A rate that is not newer than the stored one changes nothing. A rate
    that moved more than MAX_MOVE_PERCENT goes to ``held`` for a person to
    look at, and the stored one stays.
    """
    row = conn.execute(
        "SELECT rate_micros, published FROM rates WHERE currency = ?", (currency,)
    ).fetchone()
    with conn:
        if row is not None:
            stored, stored_published = row
            if published <= stored_published:
                return "older"
            if abs(rate_micros - stored) * 100 > stored * MAX_MOVE_PERCENT:
                conn.execute(
                    "INSERT OR REPLACE INTO held VALUES (?, ?, ?)",
                    (currency, rate_micros, published),
                )
                return "held"
        conn.execute(
            "INSERT OR REPLACE INTO rates VALUES (?, ?, ?)", (currency, rate_micros, published)
        )
    return "stored"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the rates.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make an empty table")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if not args.create:
        for currency, micros, published in conn.execute("SELECT * FROM rates ORDER BY currency"):
            print(f"{currency}  {micros / MICROS:12.6f}  {published}")
        for currency, micros, published in conn.execute("SELECT * FROM held ORDER BY currency"):
            print(f"{currency}  {micros / MICROS:12.6f}  {published}  held")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
