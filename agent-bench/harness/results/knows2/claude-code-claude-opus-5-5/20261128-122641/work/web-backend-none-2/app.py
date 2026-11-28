"""The order service: one FastAPI app over the SQLite store."""

from fastapi import Depends, FastAPI, HTTPException

import store

app = FastAPI(title="orders")

DISCOUNT_PERCENT = {"gold": 10, "silver": 5}


def database():
    connection = store.connect()
    try:
        yield connection
    finally:
        connection.close()


def find_customer(db, customer_id):
    row = db.execute("SELECT id, name, tier FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="no such customer")
    return row


def discount_for(tier):
    try:
        return DISCOUNT_PERCENT[tier]
    except KeyError:
        return 0


def items_of(db, order_id):
    return db.execute(
        "SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()


def price_of(db, product_id):
    row = db.execute("SELECT cents FROM products WHERE id = ?", (product_id,)).fetchone()
    return row["cents"]


def product_names(db):
    return {row["id"]: row["name"] for row in db.execute("SELECT id, name FROM products")}


def order_total(db, order_id):
    return sum(price_of(db, item["product_id"]) * item["quantity"] for item in items_of(db, order_id))


@app.get("/customers/{customer_id}/orders")
def list_orders(customer_id: int, names: bool = False, db=Depends(database)):
    customer = find_customer(db, customer_id)
    percent = discount_for(customer["tier"])
    orders = db.execute(
        "SELECT id, placed FROM orders WHERE customer_id = ? ORDER BY placed", (customer_id,)
    ).fetchall()
    labels = product_names(db) if names else None
    result = []
    for order in orders:
        total = order_total(db, order["id"])
        entry = {
            "id": order["id"],
            "placed": order["placed"],
            "total_cents": total * (100 - percent) // 100,
        }
        if labels is not None:
            entry["products"] = [labels[i["product_id"]] for i in items_of(db, order["id"])]
        result.append(entry)
    return {"customer": customer["name"], "orders": result}
