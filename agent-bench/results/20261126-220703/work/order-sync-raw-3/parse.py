"""Turn raw order rows into Order records."""

from dataclasses import dataclass
from datetime import datetime

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
        # Normalise like the other text fields: the sales system may send
        # " KBD-0101" or "kbd-0101" for the warehouse SKU KBD-0101.
        sku=row["sku"].strip().upper(),
        quantity=quantity,
        channel=row["channel"].strip(),
        unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
    )


def parse_rows(rows):
    """Parse all rows and return the orders, oldest first."""
    orders = [parse_row(row) for row in rows]
    orders.sort(key=lambda order: (order.placed_at, order.order_id))
    return orders
