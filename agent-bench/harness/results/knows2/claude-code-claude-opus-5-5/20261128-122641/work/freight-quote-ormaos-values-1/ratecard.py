"""The contract rate card: the prices agreed with the carrier, per lane."""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CARD = HERE / "ratecard.csv"
MINIMUM_CENTS = 950
EXPRESS_FACTOR = 1.5


class UnknownLaneError(LookupError):
    """The rate card has no price for this pair of depots."""


def load(path=DEFAULT_CARD):
    """Read the card. Returns {lane: (base_cents, per_kg_cents)}."""
    with open(path, newline="", encoding="utf-8") as handle:
        return {
            row["lane"]: (int(row["base_cents"]), int(row["per_kg_cents"]))
            for row in csv.DictReader(handle)
        }


def rate(card, shipment):
    """The freight of one shipment by the card, in cents."""
    if shipment.lane not in card:
        raise UnknownLaneError(shipment.lane)
    base_cents, per_kg_cents = card[shipment.lane]
    cents = max(MINIMUM_CENTS, base_cents + per_kg_cents * shipment.chargeable_kg)
    if shipment.service == "express":
        cents *= EXPRESS_FACTOR
    return round(cents)
