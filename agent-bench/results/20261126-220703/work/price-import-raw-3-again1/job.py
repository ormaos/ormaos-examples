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


class ConversionFailed(Exception):
    pass


def convert_list(supplier_list, staging):
    """Run the converter, a program of its own that purchasing also uses by hand.

    The converter writes to a temporary file next to the staging file, and only
    a complete conversion (exit code 0) replaces the staging file. A converter
    that stops half-way therefore never leaves a partial list to be loaded.
    """
    staging = Path(staging)
    partial = staging.with_name(staging.name + ".partial")
    command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(partial)]
    log.info("running %s", " ".join(command))
    # The converter reports its progress line by line on stdout; keep that out
    # of cron's mail, but keep its stderr: that is where it says why it failed.
    result = subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        details = result.stderr.strip().splitlines()
        reason = details[-1] if details else "no message"
        log.error("converter output:\n%s", result.stderr)
        raise ConversionFailed(
            f"converter exited with code {result.returncode} on {supplier_list}: {reason}"
        )
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
    except (OSError, ValueError, KeyError, ConversionFailed) as exc:
        print(f"price import failed: {exc}", file=sys.stderr)
        return 2
    conn.close()
    log.info("%d rows taken over", rows)
    print("price import finished: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
