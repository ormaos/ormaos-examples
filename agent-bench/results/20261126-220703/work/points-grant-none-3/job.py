"""points-grant: grant loyalty points for the day's purchases.

Meant to run on a schedule (see README.md)::

    python job.py

Every purchases file in ``inbox/`` is granted and then deleted. Exit code 0
means every file was handled; anything else means the job could not run.
"""

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

import members
import purchases

HERE = Path(__file__).resolve().parent
DEFAULT_INBOX = HERE / "inbox"

log = logging.getLogger("points_grant")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("POINTS_GRANT_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def grant_file(conn, path, day):
    """Grant one purchases file. Returns (purchases, grants)."""
    rows = purchases.read(path)
    granted = 0
    for purchase in rows:
        points = members.grant(conn, purchase, day)
        if points is None:
            log.info("%s: nothing granted", purchase.purchase_id)
        else:
            granted += 1
    return len(rows), granted


def main(argv=None):
    parser = argparse.ArgumentParser(description="Grant the points of the purchases.")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--db", default=members.DEFAULT_DB, help="the SQLite file")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="the day of the grants (default: today)")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = members.connect(args.db)
        for path in sorted(args.inbox.glob("purchases-*.csv")):
            seen, granted = grant_file(conn, path, args.date or date.today())
            log.info("%s: %d purchases, %d grants", path.name, seen, granted)
            path.unlink()
    except (OSError, ValueError, KeyError) as exc:
        print(f"points failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    print("points finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
