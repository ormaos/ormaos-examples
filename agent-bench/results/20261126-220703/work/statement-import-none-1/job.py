"""statement-import: book the bank's statements into the ledger.

Meant to run on a schedule (see README.md)::

    python job.py

Every statement file in ``inbox/`` is booked and then deleted. Exit code 0
means every file was booked; anything else means the job could not run.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import ledger
import statement

HERE = Path(__file__).resolve().parent
DEFAULT_INBOX = HERE / "inbox"
ACCOUNT = os.environ.get("STATEMENT_IMPORT_ACCOUNT", "ACC-7701")

log = logging.getLogger("statement_import")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("STATEMENT_IMPORT_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def book_file(conn, path):
    """Book one statement file. Returns (records read, records booked)."""
    account, day, records = statement.read(path)
    if account != ACCOUNT:
        raise statement.StatementError(f"{path.name} is for account {account}")
    booked = 0
    with conn:
        for record in records:
            if ledger.book(conn, record):
                booked += 1
    log.info("%s of %s: %d records, %d booked", path.name, day, len(records), booked)
    return len(records), booked


def main(argv=None):
    parser = argparse.ArgumentParser(description="Book the statements in the inbox.")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--db", default=ledger.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = ledger.connect(args.db)
        files = sorted(args.inbox.glob("statement-*.txt"))
        for path in files:
            book_file(conn, path)
            path.unlink()
    except (OSError, ValueError) as exc:
        print(f"statement import failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    print("statement import finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
