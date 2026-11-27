"""Turn raw order rows into Order records."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime

# Hyphen-like characters that should be read as "-" in a SKU.
_DASHES = re.compile(r"[‐-―−﹘﹣－]")

FIELDS = ("order_id", "placed_at", "sku", "quantity", "channel")
# Optional column: "each" (single items, the default) or "pack".
DEFAULT_UNIT = "each"


class ParseError(ValueError):
    """A row that cannot be read as an order."""


@dataclass(frozen=True)
class Order:
    order_id: str
    placed_at: datetime
    sku: str
    quantity: int
    channel: str
    unit: str = DEFAULT_UNIT


def normalize_sku(raw):
    """Write a SKU the way the warehouse does: AAA-0000.

    The sales system does not always send SKUs that way (lower case, stray
    spaces, full-width characters, a typographic dash). Without this, those
    orders fail the SKU check and never reach the inventory.
    """
    sku = unicodedata.normalize("NFKC", raw).strip().upper()
    return _DASHES.sub("-", sku)


def parse_row(row):
    """Build one Order from a mapping with the columns in FIELDS."""
    missing = [name for name in FIELDS if row.get(name) in (None, "")]
    if missing:
        raise ParseError(f"missing fields: {', '.join(missing)}")
    try:
        placed_at = datetime.fromisoformat(row["placed_at"])
        quantity = int(row["quantity"])
    except ValueError as exc:
        raise ParseError(f"order {row['order_id']}: {exc}") from exc
    return Order(
        order_id=row["order_id"].strip(),
        placed_at=placed_at,
        sku=normalize_sku(row["sku"]),
        quantity=quantity,
        channel=row["channel"].strip(),
        unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
    )


def parse_rows(rows):
    """Parse all rows and return the orders, oldest first."""
    orders = [parse_row(row) for row in rows]
    orders.sort(key=lambda order: (order.placed_at, order.order_id))
    return orders
