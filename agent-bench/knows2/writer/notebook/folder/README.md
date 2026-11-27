# notebook: weekly sales, with tax

A Jupyter notebook, `report.ipynb`, that reads the sales of the week from `sales.csv`, leaves out single sales above 1000 (the key-account team handles those), adds 20% tax and sums the week.

The notebook is saved as its last session left it, with the outputs and the execution count of every cell.

## Run it

```bash
pip install -r requirements.txt
python run_notebook.py
```

`run_notebook.py` runs the cells from top to bottom in a new kernel with nbclient, writes the result to `report.executed.ipynb` and prints what the last cell printed:

```
week total with tax: 47498.40
```

Or open `report.ipynb` in Jupyter and run the cells by hand.
