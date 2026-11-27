"""The commission database, in SQLite.

    python payouts.py                                 # the payouts, per day
    python payouts.py --compare data/finance_check.csv
    python payouts.py --create                        # an empty database
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "commissions.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reps (
    rep_id TEXT PRIMARY KEY,
    name   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_table (
    rep_id       TEXT NOT NULL,
    product_line TEXT NOT NULL,
    rate_bp      INTEGER NOT NULL,
    PRIMARY KEY (rep_id, product_line)
);
CREATE TABLE IF NOT EXISTS payouts (
    day              TEXT NOT NULL,
    rep_id           TEXT NOT NULL REFERENCES reps (rep_id),
    deals            INTEGER NOT NULL,
    commission_cents INTEGER NOT NULL,
    PRIMARY KEY (day, rep_id)
);
"""


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def known_reps(conn):
    return {rep_id for (rep_id,) in conn.execute("SELECT rep_id FROM reps")}


def write_day(conn, day, totals):
    """Replace the payouts of a day. ``totals`` is rep -> (deals, cents)."""
    with conn:
        conn.execute("DELETE FROM payouts WHERE day = ?", (day.isoformat(),))
        conn.executemany(
            "INSERT INTO payouts (day, rep_id, deals, commission_cents) VALUES (?, ?, ?, ?)",
            [(day.isoformat(), rep, deals, cents) for rep, (deals, cents) in sorted(totals.items())],
        )


def compare(conn, finance_csv):
    """Print the payouts next to finance's own numbers."""
    with open(finance_csv, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            found = conn.execute(
                "SELECT commission_cents FROM payouts WHERE day = ? AND rep_id = ?",
                (row["day"], row["rep_id"]),
            ).fetchone()
            ours, theirs = (found[0] if found else 0), int(row["commission_cents"])
            mark = "" if ours == theirs else f"   <-- differs by {ours - theirs}"
            print(f"{row['day']}  {row['rep_id']}  paid {ours:>8}  finance {theirs:>8}{mark}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the payouts.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make an empty database")
    parser.add_argument("--compare", metavar="CSV", help="finance's numbers")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if args.compare:
        compare(conn, args.compare)
    elif not args.create:
        rows = conn.execute("SELECT * FROM payouts ORDER BY day, rep_id")
        for day, rep_id, deals, cents in rows:
            print(f"{day}  {rep_id}  {deals:3d} deals  {cents / 100:10.2f}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
