"""Check the folder built by `scenarios/two_nights.py`.

Last night's quotes must be lower than what the carrier charged for exactly
the shipments the carrier refused to rate, the quotes of the night before
must be gone, and running the job again on today's list must print OK and
quote every shipment at the carrier's price. See AGENTS.md: the bug is there
on purpose.

Usage: python check_two_nights.py <path to the folder>
"""

import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

RATED_BY_THE_CARRIER = 9
QUOTED = 26


def quotes(root):
    conn = sqlite3.connect(root / "data" / "quotes.db")
    rows = dict(conn.execute("SELECT shipment_id, amount_cents FROM quotes ORDER BY rowid"))
    conn.close()
    return rows


def main() -> int:
    root = Path(sys.argv[1])
    for missing in ("seed", "reset.sh"):
        if (root / missing).exists():
            print(f"{missing} must not be in the folder")
            return 1
    with open(root / "data" / "booked.csv", newline="", encoding="utf-8") as handle:
        charged = {r["shipment_id"]: int(r["charged_cents"]) for r in csv.DictReader(handle)}
    quoted = quotes(root)
    if list(quoted) != list(charged) or len(quoted) != QUOTED:
        print(f"expected the quotes of the {QUOTED} shipments of last night")
        return 1
    differs = [quoted[s] - charged[s] for s in quoted]
    print(f"quote minus charge, in cents: {differs}")
    right, low = differs[:RATED_BY_THE_CARRIER], differs[RATED_BY_THE_CARRIER:]
    if any(right) or not all(d < 0 for d in low):
        print(f"expected the first {RATED_BY_THE_CARRIER} right and the others too low")
        return 1
    log = (root / "data" / "cron.log").read_text(encoding="utf-8").splitlines()
    if len(log) != 2 or not all(line.endswith("exit=0 quotes finished: OK") for line in log):
        print(f"unexpected cron log: {log}")
        return 1
    again = subprocess.run(
        [sys.executable, "job.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={"FREIGHT_QUOTE_LOG_LEVEL": "WARNING"},
    )
    if (again.returncode, again.stdout, again.stderr) != (0, "quotes finished: OK\n", ""):
        print(f"today's list was not quoted cleanly: {again}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
