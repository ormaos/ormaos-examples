"""late-fees: charge the late fee of the night on every overdue invoice.

Meant to run on a schedule (see README.md)::

    python job.py

Exit code 0 means the night was handled; anything else means the job could
not run.
"""

import argparse
import logging
import os
import sys
from datetime import date

import fees
import invoices
import settings

log = logging.getLogger("late_fees")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("LATE_FEES_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def charge_night(conn, config, day):
    """Charge tonight's fee on every invoice that is chargeable. Returns how many."""
    charged = 0
    for invoice in invoices.due_before(conn, day):
        if not fees.is_chargeable(invoice, day, config):
            continue
        cents = fees.fee_for(invoice, invoices.charged_so_far(conn, invoice.invoice_id), config)
        if cents == 0:
            log.info("%s is at its cap", invoice.invoice_id)
            continue
        if invoices.add_fee(conn, invoice.invoice_id, day, fees.days_late(invoice, day), cents):
            charged += 1
    return charged


def skip_night(conn, day):
    """A paused night: count what would have been looked at, charge nothing."""
    waiting = len(invoices.due_before(conn, day))
    log.info("paused: %d invoices left as they are", waiting)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Charge the late fees of one night.")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="the night to charge (default: today)")
    parser.add_argument("--db", default=invoices.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()
    day = args.date or date.today()

    try:
        config = settings.load()
        conn = invoices.connect(args.db)
    except (OSError, KeyError, ValueError) as exc:
        print(f"late fees failed: {exc}", file=sys.stderr)
        return 2

    if config.pause:
        charged = skip_night(conn, day)
        # Cron keeps only what is printed: a paused night must not look like a charged one.
        print(f"late fees paused: nothing charged for {day}")
    else:
        charged = charge_night(conn, config, day)
    conn.close()
    log.info("%s: %d fees charged", day, charged)
    print("late fees finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
