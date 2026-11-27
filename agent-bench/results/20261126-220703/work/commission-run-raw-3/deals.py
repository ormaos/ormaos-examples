"""The deals file of the CRM.

A CSV with ``deal_id``, ``rep``, ``product_line``, ``amount_cents`` and
``status``. ``rep`` is one rep (``R-12``) or the reps who share the deal
(``R-12+R-15``). The status is ``won`` or ``cancelled``.
"""

import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Deal:
    deal_id: str
    reps: tuple
    product_line: str
    amount_cents: int
    status: str

    @property
    def share_cents(self):
        """What each rep of the deal is paid on: an equal share."""
        return self.amount_cents // len(self.reps)


def read(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [
            Deal(
                deal_id=row["deal_id"].strip(),
                reps=tuple(rep.strip() for rep in row["rep"].split("+")),
                product_line=row["product_line"].strip().lower(),
                amount_cents=int(row["amount_cents"]),
                status=row["status"].strip().lower(),
            )
            for row in csv.DictReader(handle)
        ]
