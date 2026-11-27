"""The purchases file of the tills.

A CSV with ``purchase_id``, ``member_id``, ``email``, ``amount_cents`` and
``store``. The tills of the older stores do not know member numbers: their
rows have an empty ``member_id`` and the e-mail address the customer gave.
A negative amount is a refund.
"""

import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Purchase:
    purchase_id: str
    member_id: str
    email: str
    amount_cents: int
    store: str


def read(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [
            Purchase(
                purchase_id=row["purchase_id"].strip(),
                member_id=row["member_id"].strip(),
                email=row["email"].strip().lower(),
                amount_cents=int(row["amount_cents"]),
                store=row["store"].strip(),
            )
            for row in csv.DictReader(handle)
        ]
