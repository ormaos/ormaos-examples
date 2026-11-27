"""The dispatch list: the shipments that leave tomorrow."""

import csv
import math
from dataclasses import dataclass

FIELDS = ("shipment_id", "origin", "destination", "weight_kg",
          "length_cm", "width_cm", "height_cm", "service")
SERVICES = ("standard", "express")
# The carrier charges a bulky parcel by its volume: 1 kg per 5000 cm3.
VOLUME_DIVISOR = 5000


@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    origin: str
    destination: str
    weight_kg: float
    length_cm: int
    width_cm: int
    height_cm: int
    service: str

    @property
    def lane(self):
        """The two depots, in alphabetical order: a lane costs the same both ways."""
        return "-".join(sorted((self.origin, self.destination)))

    @property
    def chargeable_kg(self):
        """The larger of the real and the volume weight, rounded up to half a kilo."""
        volume_kg = self.length_cm * self.width_cm * self.height_cm / VOLUME_DIVISOR
        return math.ceil(max(self.weight_kg, volume_kg) * 2) / 2


def parse_row(row):
    missing = [name for name in FIELDS if row.get(name) in (None, "")]
    if missing:
        raise ValueError(f"shipment row without {', '.join(missing)}")
    service = row["service"].strip().lower()
    if service not in SERVICES:
        raise ValueError(f"{row['shipment_id']}: unknown service {service!r}")
    return Shipment(
        shipment_id=row["shipment_id"].strip(),
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        weight_kg=float(row["weight_kg"]),
        length_cm=int(row["length_cm"]),
        width_cm=int(row["width_cm"]),
        height_cm=int(row["height_cm"]),
        service=service,
    )


def read(path):
    """Read the dispatch list. Returns the shipments in the order of the file."""
    with open(path, newline="", encoding="utf-8") as handle:
        return [parse_row(row) for row in csv.DictReader(handle)]
