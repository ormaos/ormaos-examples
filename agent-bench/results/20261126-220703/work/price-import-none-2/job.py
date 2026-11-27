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


def convert_list(supplier_list, staging):
    """Run the converter, a program of its own that purchasing also uses by hand."""
    staging = Path(staging)
    partial = staging.with_name(staging.name + ".partial")
    command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(partial)]
    log.info("running %s", " ".join(command))
    # The converter reports its progress line by line; keep that out of cron's
    # mail, but capture it so a failure can be reported.
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        detail = (result.stderr.strip() or result.stdout.strip()).splitlines()
        reason = detail[-1] if detail else "no output"
        log.error("converter output:\n%s%s", result.stdout, result.stderr)
        raise ValueError(f"converter exited with {result.returncode}: {reason}")
    # Only a completely converted list ever becomes the staging file.
    os.replace(partial, staging)


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
    finally:
        if "conn" in locals():
            conn.close()
    log.info("%d rows taken over", rows)
    print("price import finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
