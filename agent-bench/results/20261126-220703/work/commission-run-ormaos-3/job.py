"""commission-run: work out the reps' commissions on the day's deals.

Meant to run on a schedule (see README.md)::

    python job.py

Every deals file in ``inbox/`` is worked out, written as the payouts of the
day, and then deleted. Exit code 0 means every file was handled; anything
else means the job could not run.
"""

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

import deals
import payouts
import rates

HERE = Path(__file__).resolve().parent
DEFAULT_INBOX = HERE / "inbox"

log = logging.getLogger("commission_run")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("COMMISSION_RUN_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def totals_of(conn, rows):
    """rep -> (deals, commission in cents) for the deals of one file."""
    reps = payouts.known_reps(conn)
    totals = {}
    for deal in rows:
        if deal.status != "won":
            continue
        for rep_id in deal.reps:
            if rep_id not in reps:
                log.warning("%s: %s is not a rep, nothing paid", deal.deal_id, rep_id)
                continue
            count, cents = totals.get(rep_id, (0, 0))
            totals[rep_id] = (count + 1, cents + rates.commission_cents(conn, deal, rep_id))
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(description="Work out the commissions of the deals.")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--db", default=payouts.DEFAULT_DB, help="the SQLite file")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="the day of the payouts (default: today)")
    args = parser.parse_args(argv)
    configure_logging()
    day = args.date or date.today()

    try:
        conn = payouts.connect(args.db)
        for path in sorted(args.inbox.glob("deals-*.csv")):
            totals = totals_of(conn, deals.read(path))
            payouts.write_day(conn, day, totals)
            log.info("%s: %d reps paid", path.name, len(totals))
            path.unlink()
    except (OSError, ValueError, KeyError) as exc:
        print(f"commissions failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    print("commissions finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
