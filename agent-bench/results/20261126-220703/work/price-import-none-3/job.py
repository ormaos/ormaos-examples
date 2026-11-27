"""price-import: take over the supplier's price list.

Meant to run on a schedule (see README.md)::

    python job.py

The supplier's list is converted to the import format and its prices are
written to the catalog. Exit code 0 means the prices were taken over;
anything else means the job could not run.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import catalog

HERE = Path(__file__).resolve().parent
DEFAULT_LIST = HERE / "data" / "supplier" / "pricelist.csv"
DEFAULT_STAGING = HERE / "data" / "staging.csv"

log = logging.getLogger("price_import")


def configure_logging():
    # Quiet by default: cron mails every line a job prints.
    level = os.environ.get("PRICE_IMPORT_LOG_LEVEL", "ERROR").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.ERROR),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


# The supplier's sync can replace the list at any time, also while the job runs.
SETTLE_SECONDS = 2
SNAPSHOT_ATTEMPTS = 5


def snapshot_list(supplier_list, target):
    """Copy the supplier's list to ``target`` while nobody is writing to it.

    The list is copied only once it has not changed for SETTLE_SECONDS, and
    the copy counts only if the list did not change while it was copied.
    """
    supplier_list = Path(supplier_list)
    for _ in range(SNAPSHOT_ATTEMPTS):
        before = supplier_list.stat()
        age = time.time() - before.st_mtime
        if age < SETTLE_SECONDS:
            time.sleep(SETTLE_SECONDS - age)
            continue
        shutil.copyfile(supplier_list, target)
        after = supplier_list.stat()
        if (before.st_mtime_ns, before.st_size, before.st_ino) == (
                after.st_mtime_ns, after.st_size, after.st_ino):
            return
        log.warning("%s changed while it was copied, trying again", supplier_list)
    raise OSError(f"{supplier_list} keeps changing, it could not be read in one piece")


def convert_list(supplier_list, staging):
    """Run the converter, a program of its own that purchasing also uses by hand.

    The converter writes to a temporary file that replaces ``staging`` only
    when the converter succeeded, so a failed run never leaves a staging file
    that looks like a converted list.
    """
    staging = Path(staging)
    with tempfile.TemporaryDirectory(dir=staging.parent, prefix=".convert-") as work:
        snapshot = Path(work) / "pricelist.csv"
        converted = Path(work) / "staging.csv"
        snapshot_list(supplier_list, snapshot)
        command = [sys.executable, str(HERE / "convert.py"), str(snapshot), str(converted)]
        log.info("running %s", " ".join(command))
        # The converter reports its progress line by line on stdout; keep that out
        # of cron's mail, but keep its errors.
        result = subprocess.run(command, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            detail = result.stderr.strip().splitlines()
            reason = detail[-1] if detail else "no message"
            log.error("converter output:\n%s", result.stderr)
            raise ValueError(
                f"converting {supplier_list} failed (exit {result.returncode}): {reason}")
        converted.replace(staging)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Take over the supplier's prices.")
    parser.add_argument("--list", default=DEFAULT_LIST, help="the supplier's list")
    parser.add_argument("--staging", default=DEFAULT_STAGING, help="the converted list")
    parser.add_argument("--db", default=catalog.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = catalog.connect(args.db)
        convert_list(args.list, args.staging)
        rows = catalog.load(conn, args.staging)
    except (OSError, ValueError, KeyError) as exc:
        print(f"price import failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    log.info("%d rows taken over", rows)
    print("price import finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
