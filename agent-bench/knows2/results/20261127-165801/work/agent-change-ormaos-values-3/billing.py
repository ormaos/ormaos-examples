"""Prices of order lines, invoices and refunds. All amounts are in cents."""

import json
from pathlib import Path

TIERS = Path(__file__).parent / "tiers.json"
PERCENT_OFF = {"gold": 10, "silver": 5}


def discount_percent(customer):
    with open(TIERS) as source:
        tiers = json.load(source)
    return PERCENT_OFF.get(tiers.get(customer), 0)


def line_price(item, customer):
    price = item["unit_cents"] * item["quantity"]
    return price * (100 - discount_percent(customer)) // 100


def invoice_total(order):
    return sum(line_price(item, order["customer"]) for item in order["items"])


def refund_amount(order, returned_skus):
    return sum(
        line_price(item, order["customer"])
        for item in order["items"]
        if item["sku"] in returned_skus
    )
