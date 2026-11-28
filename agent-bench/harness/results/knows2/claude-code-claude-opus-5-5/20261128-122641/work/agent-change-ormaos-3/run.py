"""Write the invoices and the refunds of the day."""

import csv
import json
from pathlib import Path

import billing

HERE = Path(__file__).parent


def load(name):
    with open(HERE / name) as source:
        return json.load(source)


def write_rows(name, header, rows):
    with open(HERE / name, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    orders = load("orders.json")
    returns = load("returns.json")
    by_id = {order["id"]: order for order in orders}
    invoices = [(order["id"], order["customer"], billing.invoice_total(order)) for order in orders]
    refunds = [
        (r["order_id"], billing.refund_amount(by_id[r["order_id"]], set(r["skus"]))) for r in returns
    ]
    write_rows("invoices.csv", ["order_id", "customer", "total_cents"], invoices)
    write_rows("refunds.csv", ["order_id", "refund_cents"], refunds)
    print(f"{len(invoices)} invoices, {len(refunds)} refunds written")


if __name__ == "__main__":
    main()
