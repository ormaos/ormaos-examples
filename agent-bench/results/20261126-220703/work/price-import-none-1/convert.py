"""Convert the supplier's price list to the import format.

    python convert.py <supplier list> <output>

The supplier's list is a CSV with semicolons and the columns ``article``,
``description``, ``price``, ``currency`` and ``pack``. A price is written
the continental way, ``1.234,50``, and is the price of one pack; ``pack`` is
the number of pieces in it. The output is a CSV with ``sku`` and
``price_cents``: the price of one piece.

Prints a line every ten rows, and ``done`` at the end.
"""

import csv
import sys
from decimal import ROUND_HALF_UP, Decimal


def to_cents(text):
    """``1.234,50`` -> 123450."""
    plain = text.strip().replace(".", "").replace(",", ".")
    return int((Decimal(plain) * 100).to_integral_value(ROUND_HALF_UP))


def piece_cents(pack_cents, pack):
    """The price of one piece, rounded half up to a cent."""
    pieces = Decimal(pack_cents) / Decimal(int(pack))
    return int(pieces.to_integral_value(ROUND_HALF_UP))


def convert(source, target):
    rows = 0
    with open(source, newline="", encoding="utf-8") as supplier, \
            open(target, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("sku", "price_cents"))
        for row in csv.DictReader(supplier, delimiter=";"):
            if row["currency"].strip() != "EUR":
                continue
            cents = piece_cents(to_cents(row["price"]), row["pack"] or 1)
            writer.writerow((row["article"].strip(), cents))
            rows += 1
            if rows % 10 == 0:
                print(f"{rows} rows")
    return rows


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    rows = convert(argv[1], argv[2])
    print(f"done, {rows} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
