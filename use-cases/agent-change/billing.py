"""Prices of order lines, invoices and refunds. All amounts are in cents."""


def line_price(item):
    return item["unit_cents"] * item["quantity"]


def invoice_total(order):
    return sum(line_price(item) for item in order["items"])


def refund_amount(order, returned_skus):
    return sum(line_price(item) for item in order["items"] if item["sku"] in returned_skus)
