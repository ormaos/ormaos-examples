"""Check the folder built by `scenarios/morning_after.py`.

The stock must differ from the warehouse count for exactly the SKUs whose
orders arrived in a bad format last night, and running the job again on
today's orders must still print OK. See AGENTS.md: the bug is there on purpose.

Usage: python check_morning_after.py <path to the folder>
"""

import csv
import sqlite3
import subprocess
import sys
from pathlib import Path

EXPECTED_WRONG = {"HDS-0402": 4, "KBD-0101": 9, "MON-0201": 1}


def main() -> int:
    root = Path(sys.argv[1])
    for missing in ("seed", "reset.sh"):
        if (root / missing).exists():
            print(f"{missing} must not be in the folder")
            return 1
    with open(root / "data" / "count.csv", newline="", encoding="utf-8") as handle:
        counted = {row["sku"]: int(row["counted"]) for row in csv.DictReader(handle)}
    conn = sqlite3.connect(root / "data" / "inventory.db")
    on_hand = dict(conn.execute("SELECT sku, on_hand FROM stock"))
    applied = conn.execute("SELECT COUNT(*) FROM applied_orders").fetchone()[0]
    backorders = conn.execute("SELECT COUNT(*) FROM backorders").fetchone()[0]
    conn.close()

    wrong = {sku: on_hand[sku] - counted[sku] for sku in counted if on_hand[sku] != counted[sku]}
    print(f"differs from the count: {wrong}")
    print(f"orders applied: {applied}, back-orders: {backorders}")
    if wrong != EXPECTED_WRONG or backorders != 2 or applied != 33:
        print(f"expected {EXPECTED_WRONG}, 33 orders applied and 2 back-orders")
        return 1
    log = (root / "data" / "cron.log").read_text(encoding="utf-8").splitlines()
    if len(log) != 2 or not all(line.endswith("exit=0 sync finished: OK") for line in log):
        print(f"unexpected cron log: {log}")
        return 1
    again = subprocess.run(
        [sys.executable, "job.py", "--source", "api"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={"ORDER_SYNC_LOG_LEVEL": "WARNING"},
    )
    if (again.returncode, again.stdout, again.stderr) != (0, "sync finished: OK\n", ""):
        print(f"today's orders did not sync cleanly: {again}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
