"""Business rules an order must pass before it touches the inventory."""

import re

# Warehouse SKUs: three capital letters, a dash, four digits. Example: KBD-0101.
SKU_PATTERN = re.compile(r"[A-Z]{3}-[0-9]{4}")
MAX_QUANTITY = 500


class ValidationError(ValueError):
    """An order that breaks a business rule."""


class SkuFormatError(ValidationError):
    pass


class QuantityError(ValidationError):
    pass


def check_sku(sku):
    if not SKU_PATTERN.fullmatch(sku):
        raise SkuFormatError(f"SKU {sku!r} is not in the format AAA-0000")


def check_quantity(quantity):
    if quantity < 1:
        raise QuantityError(f"quantity must be at least 1, got {quantity}")
    if quantity > MAX_QUANTITY:
        raise QuantityError(f"quantity {quantity} is above the limit {MAX_QUANTITY}")


def check_order(order):
    """Raise ValidationError if the order must not be applied."""
    check_sku(order.sku)
    check_quantity(order.quantity)
