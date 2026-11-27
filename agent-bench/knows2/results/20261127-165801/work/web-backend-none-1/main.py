"""Ask the order service for one customer's orders, through its test client."""

import sys

from fastapi.testclient import TestClient

import store
from app import app


def main(customer_id=3):
    store.create()
    client = TestClient(app)
    response = client.get(f"/customers/{customer_id}/orders")
    body = response.json()
    print(f"GET /customers/{customer_id}/orders -> {response.status_code}, {len(body['orders'])} orders")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
