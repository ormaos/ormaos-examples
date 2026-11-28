# data-pipeline: revenue by region

A monthly report made with pandas from two exports:

- `orders.csv`: one row per order (`order_id`, `customer_id`, `placed`, `amount`), 200 orders of October;
- `customers.csv`: one row per customer (`customer_id`, `name`, `region`).

The pipeline drops the orders that have no amount yet, drops repeated order numbers when there are any, joins each order to its customer, sums the amounts by region and writes `report.csv`.

## Run it

```bash
pip install -r requirements.txt
python pipeline.py
```

It prints one line and writes the report next to the script:

```
report.csv written: 4 regions
```
