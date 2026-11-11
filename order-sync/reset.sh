#!/bin/sh
# Rebuild the input and the database from seed/, so every run starts the same.
# Uses "python3" unless PYTHON is set:  PYTHON=.venv/bin/python ./reset.sh
set -eu
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

mkdir -p data
cp seed/orders.csv data/orders.csv
"$PYTHON" inventory.py --db data/inventory.db --create-from seed/stock.csv
echo "reset: data/orders.csv restored"
