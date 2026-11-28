"""The quotes: one per shipment of the dispatch list, in a local SQLite database.

Run this file to see them::

    python quotes.py
    python quotes.py --booked data/booked.csv    # next to what the carrier charged
"""

import argparse
import csv
import sqlite3
import sys
from dataclasses import astuple, dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "quotes.db"

SCHEMA = """
CREATE TABLE quotes (
    shipment_id    TEXT PRIMARY KEY,
    lane           TEXT NOT NULL,
    service        TEXT NOT NULL,
    chargeable_kg  REAL NOT NULL,
    amount_cents   INTEGER NOT NULL,
    quoted_at      TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Quote:
    shipment_id: str
    lane: str
    service: str
    chargeable_kg: float
    amount_cents: int
    quoted_at: str

    @classmethod
    def of(cls, shipment, cents):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return cls(shipment.shipment_id, shipment.lane, shipment.service,
                   shipment.chargeable_kg, cents, now)


def connect(db_path=DEFAULT_DB, create=False):
    db_path = Path(db_path)
    if create:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.unlink(missing_ok=True)
    elif not db_path.exists():
        raise FileNotFoundError(f"{db_path} does not exist; run ./reset.sh first")
    conn = sqlite3.connect(db_path)
    if create:
        conn.executescript(SCHEMA)
    return conn


def replace_all(conn, rows):
    """The table holds the quotes of the current dispatch list and no other."""
    with conn:
        conn.execute("DELETE FROM quotes")
        conn.executemany(
            "INSERT INTO quotes VALUES (?, ?, ?, ?, ?, ?)", [astuple(r) for r in rows]
        )


def show(conn, booked_csv=None):
    booked = {}
    if booked_csv:
        with open(booked_csv, newline="", encoding="utf-8") as handle:
            booked = {r["shipment_id"]: int(r["charged_cents"]) for r in csv.DictReader(handle)}
    query = "SELECT * FROM quotes ORDER BY shipment_id"
    for shipment_id, lane, service, kg, cents, _ in conn.execute(query):
        line = f"{shipment_id}  {lane}  {service:<8}  {kg:>6.1f} kg  {cents / 100:>8.2f}"
        if shipment_id in booked:
            charged = booked[shipment_id]
            line += f"  charged {charged / 100:>8.2f}  {(cents - charged) / 100:>+8.2f}"
        print(line)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the quotes.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make a new, empty database")
    parser.add_argument("--booked", help="a CSV of what the carrier charged")
    args = parser.parse_args(argv)
    conn = connect(args.db, create=args.create)
    show(conn, args.booked)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
