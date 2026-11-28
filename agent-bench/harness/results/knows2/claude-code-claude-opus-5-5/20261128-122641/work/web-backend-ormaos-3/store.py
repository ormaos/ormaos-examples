"""The SQLite store of the order service: schema, seed data, one connection."""

import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "orders.db"

SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, tier TEXT);
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, cents INTEGER);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, placed TEXT);
CREATE TABLE order_items (order_id INTEGER, product_id INTEGER, quantity INTEGER);
"""

CUSTOMERS = [(1, "Ana", "gold"), (2, "Bruno", "silver"), (3, "Clara", "trial")]
PRODUCTS = [(1, "notebook", 450), (2, "pen", 120), (3, "stapler", 990), (4, "tape", 260)]


def connect():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def create():
    """Build the database again, with the same customers, products and orders."""
    DB.unlink(missing_ok=True)
    connection = connect()
    connection.executescript(SCHEMA)
    connection.executemany("INSERT INTO customers VALUES (?, ?, ?)", CUSTOMERS)
    connection.executemany("INSERT INTO products VALUES (?, ?, ?)", PRODUCTS)
    order_id = 0
    for customer_id, how_many in ((1, 4), (2, 3), (3, 12)):
        for n in range(how_many):
            order_id += 1
            connection.execute(
                "INSERT INTO orders VALUES (?, ?, ?)",
                (order_id, customer_id, f"2026-11-{n + 1:02d}"),
            )
            for k in range(1 + order_id % 3):
                connection.execute(
                    "INSERT INTO order_items VALUES (?, ?, ?)",
                    (order_id, 1 + (order_id + k) % 4, 1 + k),
                )
    connection.commit()
    connection.close()
