"""The billing database: invoices (written by the billing system) and fees.

    python invoices.py            # the fees charged, per night
    python invoices.py --create   # an empty database
"""

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "billing.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id   TEXT PRIMARY KEY,
    customer     TEXT NOT NULL,
    plan         TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    due_on       TEXT NOT NULL,
    paid_on      TEXT,
    disputed     INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS fees (
    invoice_id TEXT NOT NULL REFERENCES invoices (invoice_id),
    charged_on TEXT NOT NULL,
    days_late  INTEGER NOT NULL,
    fee_cents  INTEGER NOT NULL,
    PRIMARY KEY (invoice_id, charged_on)
);
"""


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    customer: str
    plan: str
    amount_cents: int
    due_on: date
    paid_on: date | None
    disputed: bool


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def due_before(conn, day):
    """Every invoice that was due before ``day``, oldest first."""
    rows = conn.execute(
        "SELECT invoice_id, customer, plan, amount_cents, due_on, paid_on, disputed "
        "FROM invoices WHERE due_on < ? ORDER BY due_on, invoice_id",
        (day.isoformat(),),
    )
    return [
        Invoice(
            invoice_id, customer, plan, amount_cents,
            date.fromisoformat(due_on),
            date.fromisoformat(paid_on) if paid_on else None,
            bool(disputed),
        )
        for invoice_id, customer, plan, amount_cents, due_on, paid_on, disputed in rows
    ]


def charged_so_far(conn, invoice_id):
    row = conn.execute(
        "SELECT COALESCE(SUM(fee_cents), 0) FROM fees WHERE invoice_id = ?", (invoice_id,)
    ).fetchone()
    return row[0]


def add_fee(conn, invoice_id, day, days_late, fee_cents):
    """One fee per invoice and night; a second run of a night adds nothing."""
    with conn:
        done = conn.execute(
            "INSERT OR IGNORE INTO fees (invoice_id, charged_on, days_late, fee_cents) "
            "VALUES (?, ?, ?, ?)",
            (invoice_id, day.isoformat(), days_late, fee_cents),
        )
    return done.rowcount == 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the fees charged, per night.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make an empty database")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if not args.create:
        rows = conn.execute(
            "SELECT charged_on, COUNT(*), SUM(fee_cents) FROM fees "
            "GROUP BY charged_on ORDER BY charged_on"
        )
        for charged_on, count, cents in rows:
            print(f"{charged_on}  {count:3d} fees  {cents / 100:9.2f}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
