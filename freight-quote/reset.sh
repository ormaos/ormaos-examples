#!/bin/sh
# Rebuild the input and the database from seed/, so every run starts the same.
# Uses "python3" unless PYTHON is set:  PYTHON=.venv/bin/python ./reset.sh
set -eu
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

mkdir -p data
cp seed/shipments.csv data/shipments.csv
cp seed/carrier.json data/carrier.json
"$PYTHON" quotes.py --db data/quotes.db --create
echo "reset: data/shipments.csv and data/carrier.json restored"
