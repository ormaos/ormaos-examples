"""Check that the order-sync demo still behaves as the demo needs.

After `./reset.sh` and one run of the job, the stock must be too high for
exactly the SKUs whose orders arrived in a bad format (lowercase or padded),
and right for every other SKU. See AGENTS.md: the bug is there on purpose.

Usage: python check_order_sync.py <path to order-sync>
"""

import csv
import sqlite3
import sys
from pathlib import Path

EXPECTED_WRONG = {"HDS-0402", "HUB-0301", "KBD-0101", "MON-0201"}


def main() -> int:
    root = Path(sys.argv[1])
    with open(root / "seed" / "stock.csv", newline="", encoding="utf-8") as handle:
        right = {row["sku"]: int(row["on_hand"]) for row in csv.DictReader(handle)}
    with open(root / "seed" / "orders.csv", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            right[row["sku"].strip().upper()] -= int(row["quantity"])

    conn = sqlite3.connect(root / "data" / "inventory.db")
    actual = dict(conn.execute("SELECT sku, on_hand FROM stock"))
    conn.close()

    wrong = {sku for sku in right if actual[sku] != right[sku]}
    for sku in sorted(right):
        mark = "wrong" if sku in wrong else "right"
        print(f"{sku}: in the database {actual[sku]}, should be {right[sku]} ({mark})")
    if wrong != EXPECTED_WRONG:
        print(f"expected wrong stock for {sorted(EXPECTED_WRONG)}, got {sorted(wrong)}")
        return 1
    if any(actual[sku] <= right[sku] for sku in wrong):
        print("expected the wrong stock levels to be too high")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
