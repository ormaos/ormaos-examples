# web-backend: an order service

A small FastAPI service over a SQLite database of customers, products and orders. It has one route:

```
GET /customers/{customer_id}/orders          the customer's orders, each with its total
GET /customers/{customer_id}/orders?names=1  the same, with the product names of each order
```

A gold customer gets 10% off, a silver one 5%.

## Run it

```bash
pip install -r requirements.txt
python main.py        # builds orders.db, asks for the orders of customer 3 through the test client
python main.py 1      # another customer
```

It prints one line:

```
GET /customers/3/orders -> 200, 12 orders
```

## Files

- `store.py`: the schema, the seed data, `connect()`.
- `app.py`: the FastAPI app and its route.
- `main.py`: one request through `fastapi.testclient`.
