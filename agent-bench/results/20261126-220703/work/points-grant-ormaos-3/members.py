"""The members and their points, in SQLite.

    python members.py            # the members
    python members.py --check    # members whose points are not the sum of their grants
    python members.py --create   # an empty database
"""

import argparse
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "members.db"
MULTIPLIER_PERCENT = {"silver": 100, "gold": 150, "platinum": 200}
MINIMUM_CENTS = 500

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    member_id TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    email     TEXT NOT NULL,
    tier      TEXT NOT NULL,
    points    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS grants (
    purchase_id TEXT PRIMARY KEY,
    member_id   TEXT NOT NULL REFERENCES members (member_id),
    points      INTEGER NOT NULL,
    granted_on  TEXT NOT NULL
);
"""


def connect(path=DEFAULT_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def find(conn, purchase):
    """The member of a purchase: (member_id, tier, points), or None.

    By member number when the till sent one, else by e-mail address.
    """
    if purchase.member_id:
        return conn.execute(
            "SELECT member_id, tier, points FROM members WHERE member_id = ?",
            (purchase.member_id,),
        ).fetchone()
    return conn.execute(
        "SELECT member_id, tier, points FROM members WHERE email = ? ORDER BY member_id",
        (purchase.email,),
    ).fetchone()


def points_for(amount_cents, tier):
    """One point per full euro, times the tier; a refund takes them back."""
    if abs(amount_cents) < MINIMUM_CENTS:
        return 0
    points = abs(amount_cents) // 100 * MULTIPLIER_PERCENT[tier] // 100
    return points if amount_cents > 0 else -points


def grant(conn, purchase, day):
    """Grant the points of one purchase. Returns the points, or None if not granted.

    A purchase is granted once. A refund never takes a member below zero:
    the grant is what was really taken.
    """
    if conn.execute(
        "SELECT 1 FROM grants WHERE purchase_id = ?", (purchase.purchase_id,)
    ).fetchone():
        return None
    member = find(conn, purchase)
    if member is None:
        return None
    member_id, tier, balance = member
    points = max(points_for(purchase.amount_cents, tier), -balance)
    if points == 0:
        return None
    with conn:
        conn.execute(
            "INSERT INTO grants (purchase_id, member_id, points, granted_on) VALUES (?, ?, ?, ?)",
            (purchase.purchase_id, member_id, points, day.isoformat()),
        )
        conn.execute(
            "UPDATE members SET points = points + ? WHERE member_id = ?",
            (points, member_id),
        )
    return points


def unbalanced(conn):
    """Members whose points are not the sum of their grants."""
    return conn.execute(
        "SELECT m.member_id, m.name, m.points, COALESCE(SUM(g.points), 0) "
        "FROM members m LEFT JOIN grants g ON g.member_id = m.member_id "
        "GROUP BY m.member_id HAVING m.points != COALESCE(SUM(g.points), 0) "
        "ORDER BY m.member_id"
    ).fetchall()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show the members and their points.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--create", action="store_true", help="make an empty database")
    parser.add_argument("--check", action="store_true", help="points against grants")
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if args.check:
        for member_id, name, points, granted in unbalanced(conn):
            print(f"{member_id}  {name}: {points} points, grants add up to {granted}")
    elif not args.create:
        rows = conn.execute("SELECT member_id, name, tier, points FROM members ORDER BY member_id")
        for member_id, name, tier, points in rows:
            print(f"{member_id}  {tier:8}  {points:6d}  {name}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
