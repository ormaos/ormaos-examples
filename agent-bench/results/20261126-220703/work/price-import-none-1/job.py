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
import subprocess
import sys
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


def snapshot_list(supplier_list, target):
    """Copy the supplier's list, making sure the sync did not change it meanwhile.

    The supplier's sync can replace the list at any time; reading it while it
    is being written gives a cut-off list.
    """
    supplier_list = Path(supplier_list)
    before = supplier_list.stat()
    data = supplier_list.read_bytes()
    after = supplier_list.stat()
    same = (before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_ino, after.st_size, after.st_mtime_ns)
    if not same or len(data) != after.st_size:
        raise ValueError(f"{supplier_list} changed while it was read; run again")
    if not data.endswith(b"\n"):
        raise ValueError(f"{supplier_list} does not end with a newline; it looks cut off")
    Path(target).write_bytes(data)


def convert_list(supplier_list, staging):
    """Run the converter, a program of its own that purchasing also uses by hand."""
    command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(staging)]
    log.info("running %s", " ".join(command))
    # The converter reports its progress line by line; keep that out of cron's mail,
    # but keep it to tell what went wrong if it fails.
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise ValueError(
            f"converter exited with {result.returncode}: "
            f"{detail[-1] if detail else 'no output'}"
        )


def convert_and_load(conn, supplier_list, staging):
    """Convert a snapshot of the list to a fresh file, load it, then keep it as staging."""
    staging = Path(staging)
    snapshot = staging.with_name(staging.name + ".list.tmp")
    fresh = staging.with_name(staging.name + ".tmp")
    try:
        snapshot_list(supplier_list, snapshot)
        fresh.unlink(missing_ok=True)
        convert_list(snapshot, fresh)
        rows = catalog.load(conn, fresh)
        os.replace(fresh, staging)
        return rows
    finally:
        snapshot.unlink(missing_ok=True)
        fresh.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Take over the supplier's prices.")
    parser.add_argument("--list", default=DEFAULT_LIST, help="the supplier's list")
    parser.add_argument("--staging", default=DEFAULT_STAGING, help="the converted list")
    parser.add_argument("--db", default=catalog.DEFAULT_DB, help="the SQLite file")
    args = parser.parse_args(argv)
    configure_logging()

    try:
        conn = catalog.connect(args.db)
        rows = convert_and_load(conn, args.list, args.staging)
    except (OSError, ValueError, KeyError) as exc:
        print(f"price import failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    log.info("%d rows taken over", rows)
    print("price import finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
