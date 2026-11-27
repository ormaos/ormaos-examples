"""Turn raw order rows into Order records."""

from dataclasses import dataclass, field
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
    # The row as received, kept so a rejected order can be saved and replayed.
    raw: dict = field(default=None, compare=False, repr=False)


def parse_row(row):
    """Build one Order from a mapping with the columns in FIELDS."""
    if not isinstance(row, dict):
        raise ParseError(f"not an order record: {row!r}")
    missing = [name for name in FIELDS if row.get(name) in (None, "")]
    if missing:
        raise ParseError(f"missing fields: {', '.join(missing)}")
    try:
        placed_at = datetime.fromisoformat(row["placed_at"])
        quantity = int(row["quantity"])
    except ValueError as exc:
        raise ParseError(f"order {row['order_id']}: {exc}") from exc
    except TypeError as exc:
        raise ParseError(f"order {row['order_id']}: {exc}") from exc
    return Order(
        order_id=row["order_id"].strip(),
        placed_at=placed_at,
        sku=str(row["sku"]).strip(),
        quantity=quantity,
        channel=row["channel"].strip(),
        unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
        raw=dict(row),
    )


def parse_rows(rows):
    """Parse all rows. Returns (orders oldest first, [(raw_row, reason), ...]).

    A row that cannot be parsed is returned as rejected instead of aborting
    the whole batch.
    """
    orders, rejected = [], []
    for row in rows:
        try:
            orders.append(parse_row(row))
        except ParseError as exc:
            rejected.append((row, str(exc)))
    orders.sort(key=lambda order: (order.placed_at, order.order_id))
    return orders, rejected
