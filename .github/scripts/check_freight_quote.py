"""Check that the freight-quote demo still behaves as the demo needs.

After `./reset.sh` and one run of the job, the quotes of the shipments the
carrier still rated must be the carrier's price, and the quotes of the others
must be lower. See AGENTS.md: the bug is there on purpose.

Usage: python check_freight_quote.py <path to freight-quote>
"""

import json
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1])
    sys.path.insert(0, str(root))
    import carrier
    import shipments

    seed = json.loads((root / "seed" / "carrier.json").read_text(encoding="utf-8"))
    rated = seed["calls_per_day"] - seed["calls_used_today"]
    conn = sqlite3.connect(root / "data" / "quotes.db")
    quoted = dict(conn.execute("SELECT shipment_id, amount_cents FROM quotes"))
    conn.close()

    todo = shipments.read(root / "seed" / "shipments.csv")
    wrong = []
    for number, shipment in enumerate(todo):
        price = carrier.tariff_price(
            seed["tariff"], shipment.lane, shipment.chargeable_kg, shipment.service
        )
        cents = quoted[shipment.shipment_id]
        expected_low = number >= rated
        mark = "low" if cents < price else "right" if cents == price else "high"
        print(f"{shipment.shipment_id}: quoted {cents}, the carrier's price {price} ({mark})")
        if mark != ("low" if expected_low else "right"):
            wrong.append(shipment.shipment_id)
    if wrong or not 0 < rated < len(todo):
        print(f"expected the first {rated} right and the others low; not so: {wrong}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
