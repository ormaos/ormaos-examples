"""The ledger of the bank account, in SQLite.

    python ledger.py                                # the balance
    python ledger.py --compare data/bank_balance.csv
    python ledger.py --create 1250000               # a new ledger, opening balance in cents
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "ledger.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    bank_id      TEXT PRIMARY KEY,
    booked_on    TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    text         TEXT NOT NULL
);
"""


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def has(conn, bank_id):
    row = conn.execute("SELECT 1 FROM entries WHERE bank_id = ?", (bank_id,)).fetchone()
    return row is not None


def book(conn, record):
    """Put one record of a statement in the ledger. Returns whether it was new.

    The bank sends the last records of a statement again with the next one,
    and a pending transaction again when it is booked: an id is booked once,
    and a pending transaction not at all. A reversal takes back the amount of
    the transaction it names, if that one is in the ledger.
    """
    if record.status == "P" or has(conn, record.bank_id):
        return False
    amount, text = record.amount_cents, record.text
    if record.kind == "R":
        row = conn.execute(
            "SELECT amount_cents FROM entries WHERE bank_id = ?", (record.reverses,)
        ).fetchone()
        if row is None:
            return False
        amount, text = -row[0], f"reversal of {record.reverses}"
    conn.execute(
        "INSERT INTO entries (bank_id, booked_on, amount_cents, text) VALUES (?, ?, ?, ?)",
        (record.bank_id, record.booked_on.isoformat(), amount, text),
    )
    return True


def balance(conn, until=None):
    """The balance in cents, of all entries or of those up to a day."""
    if until is None:
        row = conn.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM entries").fetchone()
    else:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM entries WHERE booked_on <= ?", (until,)
        ).fetchone()
    return row[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the balance of the ledger.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", type=int, metavar="CENTS", help="a new ledger")
    parser.add_argument("--compare", metavar="CSV", help="the bank's closing balances")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if args.create is not None:
        with conn:
            conn.execute(
                "INSERT INTO entries VALUES ('OPENING', '2000-01-01', ?, 'opening balance')",
                (args.create,),
            )
    elif args.compare:
        with open(args.compare, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                ours, theirs = balance(conn, row["date"]), int(row["closing_cents"])
                mark = "" if ours == theirs else f"   <-- differs by {ours - theirs}"
                print(f"{row['date']}  ledger {ours:>10}  bank {theirs:>10}{mark}")
    else:
        count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        print(f"{count} entries, balance {balance(conn) / 100:.2f}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
