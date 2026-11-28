"""Monthly revenue by region, from the orders and customers exports."""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent


def load_orders(path):
    return pd.read_csv(path, dtype={"customer_id": "string"})


def load_customers(path):
    return pd.read_csv(path, dtype={"customer_id": "string"})


def drop_unpriced(orders):
    """Orders exported before they were priced have no amount yet."""
    return orders.dropna(subset=["amount"])


def drop_repeats(orders):
    return orders.drop_duplicates(subset=["order_id"])


def join_customers(orders, customers):
    return orders.merge(customers, on="customer_id")


def revenue_by_region(joined):
    totals = joined.groupby("region", as_index=False)["amount"].sum()
    return totals.sort_values("region").round(2)


def write_report(report, path):
    report.to_csv(path, index=False)


def main():
    orders = load_orders(HERE / "orders.csv")
    customers = load_customers(HERE / "customers.csv")
    orders = drop_unpriced(orders)
    if orders["order_id"].duplicated().any():
        orders = drop_repeats(orders)
    joined = join_customers(orders, customers)
    report = revenue_by_region(joined)
    write_report(report, HERE / "report.csv")
    print(f"report.csv written: {len(report)} regions")


if __name__ == "__main__":
    main()
