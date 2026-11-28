# agent-change: invoices and refunds

A small billing tool. Every day it reads the orders (`orders.json`) and the returned goods (`returns.json`) and writes two files:

- `invoices.csv`: one row per order, with its total;
- `refunds.csv`: one row per return, with the amount to give back for the returned lines.

`tiers.json` has the loyalty tier of each customer. All amounts are in cents.

## Run it

```bash
python run.py
```

It prints one line:

```
12 invoices, 3 refunds written
```

Standard library only. `billing.py` has the prices; `run.py` reads and writes the files.
